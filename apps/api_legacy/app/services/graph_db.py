"""
Neo4j Graph Database Service
Handles asset topology storage and queries
"""
import os
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from neo4j import AsyncGraphDatabase, AsyncDriver
import json


class Neo4jService:
    """Wrapper for Neo4j graph database operations"""
    
    def __init__(self):
        self._driver: Optional[AsyncDriver] = None
        self._uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        self._user = os.getenv("NEO4J_USER", "neo4j")
        self._password = os.getenv("NEO4J_PASSWORD", "sentry_password")
    
    async def connect(self) -> AsyncDriver:
        """Get or create Neo4j driver"""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password)
            )
        return self._driver
    
    async def disconnect(self):
        """Close driver connection"""
        if self._driver:
            await self._driver.close()
            self._driver = None
    
    @asynccontextmanager
    async def session(self):
        """Context manager for Neo4j sessions"""
        driver = await self.connect()
        session = driver.session()
        try:
            yield session
        finally:
            await session.close()

    # --- Graph CRUD Operations ---
    
    async def get_project_graph(self, project_id: str) -> Dict[str, Any]:
        """
        Fetch complete graph topology for a project.
        Returns format compatible with react-force-graph.
        """
        query = """
        MATCH (n {project_id: $project_id})
        OPTIONAL MATCH (n)-[r]->(m {project_id: $project_id})
        RETURN n, r, m
        """
        
        nodes = {}
        links = []
        
        async with self.session() as session:
            result = await session.run(query, project_id=project_id)
            
            async for record in result:
                n = record.get("n")
                r = record.get("r")
                m = record.get("m")
                
                # Process source node
                if n:
                    node_id = n.get("id") or str(n.id)
                    if node_id not in nodes:
                        nodes[node_id] = {
                            "id": node_id,
                            "group": list(n.labels)[0] if n.labels else "Unknown",
                            "label": n.get("label") or n.get("value") or node_id,
                            **dict(n)
                        }
                
                # Process target node
                if m:
                    node_id = m.get("id") or str(m.id)
                    if node_id not in nodes:
                        nodes[node_id] = {
                            "id": node_id,
                            "group": list(m.labels)[0] if m.labels else "Unknown",
                            "label": m.get("label") or m.get("value") or node_id,
                            **dict(m)
                        }
                
                # Process relationship
                if r and n and m:
                    links.append({
                        "source": n.get("id") or str(n.id),
                        "target": m.get("id") or str(m.id),
                        "type": r.type,
                        "label": r.type.replace("_", " ").title()
                    })
        
        return {
            "nodes": list(nodes.values()),
            "links": links
        }
    
    async def add_node(
        self,
        project_id: str,
        node_id: str,
        label: str,
        node_type: str,
        properties: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Add a new node to the graph"""
        props = properties or {}
        props.update({
            "id": node_id,
            "label": label,
            "project_id": project_id
        })
        
        # Build property string for Cypher
        prop_str = ", ".join([f"{k}: ${k}" for k in props.keys()])
        
        query = f"""
        MERGE (n:{node_type} {{id: $id, project_id: $project_id}})
        SET n += {{{prop_str}}}
        RETURN n
        """
        
        async with self.session() as session:
            result = await session.run(query, **props)
            record = await result.single()
            if record:
                return {"id": node_id, "group": node_type, "label": label, **props}
        
        return None
    
    async def add_edge(
        self,
        project_id: str,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """Add a relationship between two nodes"""
        props = properties or {}
        
        query = f"""
        MATCH (a {{id: $source_id, project_id: $project_id}})
        MATCH (b {{id: $target_id, project_id: $project_id}})
        MERGE (a)-[r:{relationship_type}]->(b)
        SET r += $props
        RETURN r
        """
        
        async with self.session() as session:
            result = await session.run(
                query,
                source_id=source_id,
                target_id=target_id,
                project_id=project_id,
                props=props
            )
            record = await result.single()
            return record is not None
    
    async def remove_node(self, project_id: str, node_id: str) -> bool:
        """Remove a node and all its relationships"""
        query = """
        MATCH (n {id: $node_id, project_id: $project_id})
        DETACH DELETE n
        """
        
        async with self.session() as session:
            await session.run(query, node_id=node_id, project_id=project_id)
            return True
    
    async def update_node(
        self,
        project_id: str,
        node_id: str,
        properties: Dict[str, Any]
    ) -> bool:
        """Update node properties"""
        query = """
        MATCH (n {id: $node_id, project_id: $project_id})
        SET n += $props
        RETURN n
        """
        
        async with self.session() as session:
            result = await session.run(
                query,
                node_id=node_id,
                project_id=project_id,
                props=properties
            )
            record = await result.single()
            return record is not None

    # --- Domain-Specific Operations ---
    
    async def add_domain(self, project_id: str, domain: str) -> Dict[str, Any]:
        """Add a domain node"""
        return await self.add_node(
            project_id=project_id,
            node_id=domain,
            label=domain,
            node_type="Domain",
            properties={"value": domain}
        )
    
    async def add_ip(
        self,
        project_id: str,
        ip: str,
        parent_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add an IP node, optionally linking to a domain"""
        node = await self.add_node(
            project_id=project_id,
            node_id=ip,
            label=ip,
            node_type="IP",
            properties={"value": ip}
        )
        
        if parent_domain:
            await self.add_edge(
                project_id=project_id,
                source_id=parent_domain,
                target_id=ip,
                relationship_type="RESOLVES_TO"
            )
        
        return node
    
    async def add_port(
        self,
        project_id: str,
        ip: str,
        port: int,
        service: str = None,
        version: str = None
    ) -> Dict[str, Any]:
        """Add a port/service node linked to an IP"""
        node_id = f"{ip}:{port}"
        
        node = await self.add_node(
            project_id=project_id,
            node_id=node_id,
            label=f"{port}/tcp",
            node_type="Port",
            properties={
                "port": port,
                "service": service,
                "version": version
            }
        )
        
        await self.add_edge(
            project_id=project_id,
            source_id=ip,
            target_id=node_id,
            relationship_type="LISTENS_ON"
        )
        
        return node
    
    async def mark_vulnerable(
        self,
        project_id: str,
        node_id: str,
        vulnerability_id: str,
        severity: str
    ) -> bool:
        """Mark a node as vulnerable and create vulnerability node"""
        # Create vulnerability node
        await self.add_node(
            project_id=project_id,
            node_id=vulnerability_id,
            label=vulnerability_id,
            node_type="Vulnerability",
            properties={"severity": severity}
        )
        
        # Link to affected asset
        await self.add_edge(
            project_id=project_id,
            source_id=node_id,
            target_id=vulnerability_id,
            relationship_type="HAS_VULN"
        )
        
        # Update original node
        await self.update_node(
            project_id=project_id,
            node_id=node_id,
            properties={"vulnerable": True}
        )
        
        return True

    # --- Query Operations ---
    
    async def get_node_neighbors(self, project_id: str, node_id: str) -> List[Dict]:
        """Get all nodes connected to a specific node"""
        query = """
        MATCH (n {id: $node_id, project_id: $project_id})-[r]-(m)
        RETURN m, type(r) as relationship
        """
        
        neighbors = []
        async with self.session() as session:
            result = await session.run(query, node_id=node_id, project_id=project_id)
            async for record in result:
                m = record["m"]
                neighbors.append({
                    "id": m.get("id"),
                    "label": m.get("label"),
                    "group": list(m.labels)[0] if m.labels else "Unknown",
                    "relationship": record["relationship"]
                })
        
        return neighbors
    
    async def search_nodes(
        self,
        project_id: str,
        query: str,
        node_type: str = None
    ) -> List[Dict]:
        """Search for nodes by label/value"""
        cypher = """
        MATCH (n {project_id: $project_id})
        WHERE n.label CONTAINS $query OR n.value CONTAINS $query
        """
        
        if node_type:
            cypher = f"MATCH (n:{node_type} {{project_id: $project_id}}) WHERE n.label CONTAINS $query OR n.value CONTAINS $query"
        
        cypher += " RETURN n LIMIT 50"
        
        results = []
        async with self.session() as session:
            result = await session.run(cypher, project_id=project_id, query=query)
            async for record in result:
                n = record["n"]
                results.append({
                    "id": n.get("id"),
                    "label": n.get("label"),
                    "group": list(n.labels)[0] if n.labels else "Unknown",
                    **dict(n)
                })
        
        return results
    
    async def get_stats(self, project_id: str) -> Dict[str, int]:
        """Get graph statistics for a project"""
        query = """
        MATCH (n {project_id: $project_id})
        WITH labels(n)[0] AS label, count(*) AS count
        RETURN label, count
        """
        
        stats = {"total": 0}
        async with self.session() as session:
            result = await session.run(query, project_id=project_id)
            async for record in result:
                stats[record["label"]] = record["count"]
                stats["total"] += record["count"]
        
        return stats


# Singleton instance
neo4j_service = Neo4jService()

