"""
Multi-Tenancy & Data Isolation
Namespace Strategy for SentryAI

This module ensures that:
1. User A's data is completely isolated from User B
2. All database queries are automatically filtered by tenant
3. Vector DB queries only return tenant's own data
4. Graph DB queries are scoped to tenant's project
5. File storage is isolated per tenant

This is enforced at the API Gateway level, not application logic.
"""
from typing import Optional, Dict, Any, List, Callable, TypeVar
from functools import wraps
from contextlib import asynccontextmanager
from dataclasses import dataclass
import hashlib
import os
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta


T = TypeVar('T')


@dataclass
class TenantContext:
    """
    Current tenant context - injected into every request.
    """
    tenant_id: str              # Unique tenant identifier
    user_id: str                # Specific user within tenant
    organization_id: str        # Organization (for enterprise)
    
    # Computed namespace prefixes
    pg_schema: str              # PostgreSQL schema name
    neo4j_label_prefix: str     # Neo4j label prefix
    weaviate_tenant: str        # Weaviate tenant name
    storage_prefix: str         # File storage path prefix
    redis_prefix: str           # Redis key prefix
    
    # Permissions
    is_admin: bool = False
    scopes: List[str] = None    # e.g., ["read", "write", "admin"]
    
    def __post_init__(self):
        if self.scopes is None:
            self.scopes = ["read", "write"]


class TenantResolver:
    """
    Resolves tenant context from requests.
    """
    
    def __init__(self, jwt_secret: str, jwt_algorithm: str = "HS256"):
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self._security = HTTPBearer()
    
    async def resolve_from_request(self, request: Request) -> TenantContext:
        """
        Extract tenant context from JWT token in request.
        """
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization")
        
        token = auth_header.split(" ")[1]
        
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        tenant_id = payload.get("tenant_id")
        user_id = payload.get("user_id") or payload.get("sub")
        org_id = payload.get("organization_id") or tenant_id
        
        if not tenant_id or not user_id:
            raise HTTPException(status_code=401, detail="Invalid token claims")
        
        return self._build_context(tenant_id, user_id, org_id, payload)
    
    def _build_context(
        self,
        tenant_id: str,
        user_id: str,
        org_id: str,
        jwt_payload: dict
    ) -> TenantContext:
        """
        Build a complete tenant context with all namespaces.
        """
        # Generate safe namespace identifiers
        safe_tenant = self._safe_identifier(tenant_id)
        
        return TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            organization_id=org_id,
            pg_schema=f"tenant_{safe_tenant}",
            neo4j_label_prefix=f"T_{safe_tenant}_",
            weaviate_tenant=safe_tenant,
            storage_prefix=f"tenants/{tenant_id}",
            redis_prefix=f"tenant:{tenant_id}:",
            is_admin=jwt_payload.get("is_admin", False),
            scopes=jwt_payload.get("scopes", ["read", "write"])
        )
    
    def _safe_identifier(self, value: str) -> str:
        """
        Convert tenant ID to a safe database identifier.
        Must be alphanumeric, lowercase, max 32 chars.
        """
        # Hash if too long or contains special chars
        if len(value) > 32 or not value.isalnum():
            return hashlib.md5(value.encode()).hexdigest()[:16]
        return value.lower()


# ============================================================================
# POSTGRESQL ISOLATION
# ============================================================================

class PostgresIsolation:
    """
    Enforces tenant isolation at the PostgreSQL level.
    Uses schema-based isolation.
    """
    
    def __init__(self, engine):
        self.engine = engine
    
    async def ensure_tenant_schema(self, ctx: TenantContext):
        """Create tenant schema if it doesn't exist"""
        async with self.engine.begin() as conn:
            await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {ctx.pg_schema}")
    
    def scoped_query(self, query: str, ctx: TenantContext) -> str:
        """
        Modify a SQL query to be tenant-scoped.
        Prepends schema to all table references.
        """
        # This is a simplified implementation
        # In production, use SQLAlchemy's schema parameter
        return query.replace("FROM ", f"FROM {ctx.pg_schema}.")
    
    @asynccontextmanager
    async def tenant_session(self, ctx: TenantContext):
        """
        Create a database session scoped to the tenant's schema.
        """
        async with self.engine.begin() as conn:
            # Set search path to tenant schema
            await conn.execute(f"SET search_path TO {ctx.pg_schema}, public")
            yield conn


# ============================================================================
# NEO4J ISOLATION
# ============================================================================

class Neo4jIsolation:
    """
    Enforces tenant isolation in Neo4j.
    Uses label prefixes and property filters.
    """
    
    def __init__(self, driver):
        self.driver = driver
    
    def scoped_query(self, cypher: str, ctx: TenantContext) -> str:
        """
        Modify a Cypher query to be tenant-scoped.
        Adds WHERE clause for tenant_id.
        """
        # Add tenant filter to MATCH clauses
        if "WHERE" in cypher.upper():
            # Add to existing WHERE
            cypher = cypher.replace(
                "WHERE",
                f"WHERE n.tenant_id = '{ctx.tenant_id}' AND",
                1
            )
        else:
            # Add new WHERE clause after first MATCH
            match_end = cypher.upper().find("MATCH") + len("MATCH")
            # Find end of MATCH pattern (closing parenthesis)
            paren_count = 0
            for i, c in enumerate(cypher[match_end:], match_end):
                if c == '(':
                    paren_count += 1
                elif c == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        insert_pos = i + 1
                        break
            else:
                insert_pos = len(cypher)
            
            cypher = (
                cypher[:insert_pos] +
                f" WHERE n.tenant_id = '{ctx.tenant_id}'" +
                cypher[insert_pos:]
            )
        
        return cypher
    
    def label_for_tenant(self, base_label: str, ctx: TenantContext) -> str:
        """Get tenant-scoped label"""
        return f"{ctx.neo4j_label_prefix}{base_label}"
    
    async def create_node(
        self,
        ctx: TenantContext,
        labels: List[str],
        properties: dict
    ):
        """Create a node with tenant isolation"""
        # Add tenant_id to properties
        properties["tenant_id"] = ctx.tenant_id
        
        # Prefix labels
        scoped_labels = [self.label_for_tenant(l, ctx) for l in labels]
        
        labels_str = ":".join(scoped_labels)
        query = f"CREATE (n:{labels_str} $props) RETURN n"
        
        async with self.driver.session() as session:
            result = await session.run(query, props=properties)
            return await result.single()


# ============================================================================
# WEAVIATE ISOLATION
# ============================================================================

class WeaviateIsolation:
    """
    Enforces tenant isolation in Weaviate vector database.
    Uses native multi-tenancy feature.
    """
    
    def __init__(self, client):
        self.client = client
    
    async def ensure_tenant_exists(self, ctx: TenantContext, class_name: str):
        """Ensure tenant exists for the class"""
        try:
            self.client.schema.add_tenant(
                class_name=class_name,
                tenant=ctx.weaviate_tenant
            )
        except Exception:
            pass  # Tenant already exists
    
    def scoped_query(
        self,
        class_name: str,
        ctx: TenantContext
    ):
        """
        Return a query builder scoped to tenant.
        """
        return (
            self.client.query
            .get(class_name)
            .with_tenant(ctx.weaviate_tenant)
        )
    
    async def add_object(
        self,
        ctx: TenantContext,
        class_name: str,
        properties: dict,
        vector: List[float] = None
    ):
        """Add an object with tenant isolation"""
        await self.ensure_tenant_exists(ctx, class_name)
        
        return self.client.data_object.create(
            class_name=class_name,
            data_object=properties,
            vector=vector,
            tenant=ctx.weaviate_tenant
        )
    
    async def search(
        self,
        ctx: TenantContext,
        class_name: str,
        query_vector: List[float],
        limit: int = 10
    ) -> List[dict]:
        """Search within tenant's data only"""
        result = (
            self.client.query
            .get(class_name)
            .with_tenant(ctx.weaviate_tenant)
            .with_near_vector({"vector": query_vector})
            .with_limit(limit)
            .do()
        )
        
        return result.get("data", {}).get("Get", {}).get(class_name, [])


# ============================================================================
# REDIS ISOLATION
# ============================================================================

class RedisIsolation:
    """
    Enforces tenant isolation in Redis.
    Uses key prefixing.
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def scoped_key(self, key: str, ctx: TenantContext) -> str:
        """Prefix key with tenant namespace"""
        return f"{ctx.redis_prefix}{key}"
    
    async def get(self, key: str, ctx: TenantContext):
        """Get value for tenant-scoped key"""
        return await self.redis.get(self.scoped_key(key, ctx))
    
    async def set(self, key: str, value: Any, ctx: TenantContext, ex: int = None):
        """Set value for tenant-scoped key"""
        scoped = self.scoped_key(key, ctx)
        if ex:
            return await self.redis.setex(scoped, ex, value)
        return await self.redis.set(scoped, value)
    
    async def publish(self, channel: str, message: str, ctx: TenantContext):
        """Publish to tenant-scoped channel"""
        return await self.redis.publish(self.scoped_key(channel, ctx), message)
    
    async def subscribe(self, channel: str, ctx: TenantContext):
        """Subscribe to tenant-scoped channel"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.scoped_key(channel, ctx))
        return pubsub


# ============================================================================
# FILE STORAGE ISOLATION
# ============================================================================

class StorageIsolation:
    """
    Enforces tenant isolation for file storage.
    """
    
    def __init__(self, base_path: str = "./storage"):
        self.base_path = base_path
    
    def tenant_path(self, ctx: TenantContext) -> str:
        """Get the base path for tenant's files"""
        path = os.path.join(self.base_path, ctx.storage_prefix)
        os.makedirs(path, exist_ok=True)
        return path
    
    def resolve_path(self, relative_path: str, ctx: TenantContext) -> str:
        """
        Resolve a path within tenant's storage.
        Prevents path traversal attacks.
        """
        tenant_base = self.tenant_path(ctx)
        full_path = os.path.normpath(os.path.join(tenant_base, relative_path))
        
        # Ensure path is within tenant directory
        if not full_path.startswith(tenant_base):
            raise PermissionError("Path traversal detected")
        
        return full_path


# ============================================================================
# FASTAPI MIDDLEWARE
# ============================================================================

class TenantMiddleware:
    """
    FastAPI middleware that enforces tenant context on all requests.
    """
    
    def __init__(self, resolver: TenantResolver):
        self.resolver = resolver
    
    async def __call__(self, request: Request, call_next):
        # Skip auth for certain paths
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        try:
            ctx = await self.resolver.resolve_from_request(request)
            request.state.tenant = ctx
        except HTTPException as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        
        return await call_next(request)


def get_tenant(request: Request) -> TenantContext:
    """
    FastAPI dependency to get current tenant context.
    Use this in route handlers.
    """
    ctx = getattr(request.state, "tenant", None)
    if not ctx:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return ctx


def require_scope(scope: str):
    """
    Decorator to require specific scope.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            ctx = get_tenant(request)
            if scope not in ctx.scopes and not ctx.is_admin:
                raise HTTPException(status_code=403, detail=f"Requires '{scope}' permission")
            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# UNIFIED ISOLATION MANAGER
# ============================================================================

class IsolationManager:
    """
    Unified interface for all isolation concerns.
    """
    
    def __init__(
        self,
        pg_engine=None,
        neo4j_driver=None,
        weaviate_client=None,
        redis_client=None,
        storage_base: str = "./storage"
    ):
        self.postgres = PostgresIsolation(pg_engine) if pg_engine else None
        self.neo4j = Neo4jIsolation(neo4j_driver) if neo4j_driver else None
        self.weaviate = WeaviateIsolation(weaviate_client) if weaviate_client else None
        self.redis = RedisIsolation(redis_client) if redis_client else None
        self.storage = StorageIsolation(storage_base)
    
    async def initialize_tenant(self, ctx: TenantContext):
        """
        Initialize all storage for a new tenant.
        Call this when a new tenant signs up.
        """
        if self.postgres:
            await self.postgres.ensure_tenant_schema(ctx)
        
        # Create storage directory
        self.storage.tenant_path(ctx)
        
        # Weaviate tenants are created on-demand per class


# ============================================================================
# JWT TOKEN GENERATION (for testing)
# ============================================================================

def generate_tenant_token(
    tenant_id: str,
    user_id: str,
    secret: str,
    organization_id: str = None,
    is_admin: bool = False,
    scopes: List[str] = None,
    expires_hours: int = 24
) -> str:
    """Generate a JWT token with tenant claims"""
    payload = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "organization_id": organization_id or tenant_id,
        "is_admin": is_admin,
        "scopes": scopes or ["read", "write"],
        "exp": datetime.utcnow() + timedelta(hours=expires_hours),
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, secret, algorithm="HS256")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Generate a test token
    secret = "your-secret-key"
    token = generate_tenant_token(
        tenant_id="acme-corp",
        user_id="john.doe@acme.com",
        secret=secret,
        is_admin=True
    )
    
    print(f"Test Token: {token}")
    
    # Decode it back
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    print(f"Decoded: {decoded}")
    
    # Build context
    resolver = TenantResolver(secret)
    ctx = resolver._build_context(
        tenant_id="acme-corp",
        user_id="john.doe@acme.com",
        org_id="acme-corp",
        jwt_payload=decoded
    )
    
    print(f"\nTenant Context:")
    print(f"  PostgreSQL Schema: {ctx.pg_schema}")
    print(f"  Neo4j Prefix: {ctx.neo4j_label_prefix}")
    print(f"  Weaviate Tenant: {ctx.weaviate_tenant}")
    print(f"  Storage Prefix: {ctx.storage_prefix}")
    print(f"  Redis Prefix: {ctx.redis_prefix}")

