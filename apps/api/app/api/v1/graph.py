"""
Graph API Routes
Neo4j graph operations for asset topology
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.graph_db import neo4j_service

router = APIRouter()


# --- Request/Response Models ---

class NodeCreate(BaseModel):
    id: str
    label: str
    node_type: str  # Domain, IP, Port, Service, Vulnerability
    properties: Optional[Dict[str, Any]] = None
    parent_id: Optional[str] = None


class EdgeCreate(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str  # RESOLVES_TO, LISTENS_ON, RUNS, HAS_VULN
    properties: Optional[Dict[str, Any]] = None


class GraphData(BaseModel):
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]


class GraphStats(BaseModel):
    total: int
    Domain: Optional[int] = 0
    IP: Optional[int] = 0
    Port: Optional[int] = 0
    Service: Optional[int] = 0
    Vulnerability: Optional[int] = 0


# --- Routes ---

@router.get("/projects/{project_id}/graph", response_model=GraphData)
async def get_project_graph(project_id: str):
    """
    Get complete graph topology for a project.
    Returns nodes and links in react-force-graph format.
    """
    try:
        data = await neo4j_service.get_project_graph(project_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph: {str(e)}")


@router.get("/projects/{project_id}/graph/stats", response_model=GraphStats)
async def get_graph_stats(project_id: str):
    """Get statistics about the project's graph"""
    try:
        stats = await neo4j_service.get_stats(project_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@router.post("/projects/{project_id}/graph/nodes")
async def add_node(project_id: str, node: NodeCreate):
    """Add a new node to the graph"""
    try:
        result = await neo4j_service.add_node(
            project_id=project_id,
            node_id=node.id,
            label=node.label,
            node_type=node.node_type,
            properties=node.properties
        )
        
        # If parent_id is provided, create the edge
        if node.parent_id:
            # Determine relationship type based on node type
            rel_type = {
                "IP": "RESOLVES_TO",
                "Port": "LISTENS_ON",
                "Service": "RUNS",
                "Vulnerability": "HAS_VULN"
            }.get(node.node_type, "CONNECTS_TO")
            
            await neo4j_service.add_edge(
                project_id=project_id,
                source_id=node.parent_id,
                target_id=node.id,
                relationship_type=rel_type
            )
        
        return {"status": "created", "node": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add node: {str(e)}")


@router.post("/projects/{project_id}/graph/edges")
async def add_edge(project_id: str, edge: EdgeCreate):
    """Add a new edge between nodes"""
    try:
        result = await neo4j_service.add_edge(
            project_id=project_id,
            source_id=edge.source_id,
            target_id=edge.target_id,
            relationship_type=edge.relationship_type,
            properties=edge.properties
        )
        
        if result:
            return {"status": "created", "edge": edge.dict()}
        else:
            raise HTTPException(status_code=404, detail="One or both nodes not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add edge: {str(e)}")


@router.delete("/projects/{project_id}/graph/nodes/{node_id}")
async def remove_node(project_id: str, node_id: str):
    """Remove a node and all its relationships"""
    try:
        await neo4j_service.remove_node(project_id, node_id)
        return {"status": "deleted", "node_id": node_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove node: {str(e)}")


@router.patch("/projects/{project_id}/graph/nodes/{node_id}")
async def update_node(project_id: str, node_id: str, properties: Dict[str, Any]):
    """Update node properties"""
    try:
        result = await neo4j_service.update_node(project_id, node_id, properties)
        if result:
            return {"status": "updated", "node_id": node_id}
        else:
            raise HTTPException(status_code=404, detail="Node not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update node: {str(e)}")


@router.get("/projects/{project_id}/graph/nodes/{node_id}/neighbors")
async def get_node_neighbors(project_id: str, node_id: str):
    """Get all nodes connected to a specific node"""
    try:
        neighbors = await neo4j_service.get_node_neighbors(project_id, node_id)
        return {"node_id": node_id, "neighbors": neighbors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch neighbors: {str(e)}")


@router.get("/projects/{project_id}/graph/search")
async def search_nodes(
    project_id: str,
    q: str = Query(..., min_length=1, description="Search query"),
    node_type: Optional[str] = Query(None, description="Filter by node type")
):
    """Search for nodes by label/value"""
    try:
        results = await neo4j_service.search_nodes(project_id, q, node_type)
        return {"query": q, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# --- Domain-Specific Convenience Endpoints ---

@router.post("/projects/{project_id}/graph/domains")
async def add_domain(project_id: str, domain: str):
    """Add a domain node"""
    try:
        result = await neo4j_service.add_domain(project_id, domain)
        return {"status": "created", "node": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add domain: {str(e)}")


@router.post("/projects/{project_id}/graph/ips")
async def add_ip(
    project_id: str,
    ip: str,
    parent_domain: Optional[str] = None
):
    """Add an IP node, optionally linking to a domain"""
    try:
        result = await neo4j_service.add_ip(project_id, ip, parent_domain)
        return {"status": "created", "node": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add IP: {str(e)}")


@router.post("/projects/{project_id}/graph/ports")
async def add_port(
    project_id: str,
    ip: str,
    port: int,
    service: Optional[str] = None,
    version: Optional[str] = None
):
    """Add a port node linked to an IP"""
    try:
        result = await neo4j_service.add_port(project_id, ip, port, service, version)
        return {"status": "created", "node": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add port: {str(e)}")


@router.post("/projects/{project_id}/graph/vulnerabilities")
async def mark_vulnerable(
    project_id: str,
    node_id: str,
    vulnerability_id: str,
    severity: str
):
    """Mark a node as vulnerable"""
    try:
        await neo4j_service.mark_vulnerable(project_id, node_id, vulnerability_id, severity)
        return {"status": "marked", "node_id": node_id, "vulnerability_id": vulnerability_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark vulnerable: {str(e)}")

