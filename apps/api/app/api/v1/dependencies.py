"""Dependencies API Router — exposes graph queries and rebuild tasks."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_permissions
from app.services.graph_builder import GraphBuilderService
from app.services.neo4j_service import Neo4jService

router = APIRouter()


def _neo4j_or_503() -> Neo4jService:
    """Return a connected Neo4j service or raise 503."""
    try:
        service = Neo4jService()
        if not service.check_health():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j is unreachable. Start the neo4j service (docker compose up neo4j).",
            )
        return service
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Neo4j connection failed: {e}",
        ) from e


@router.get("/health")
async def graph_health() -> dict[str, Any]:
    """Check Neo4j connectivity and return graph statistics."""
    try:
        service = Neo4jService()
        healthy = service.check_health()
        stats = service.get_graph_stats() if healthy else {"nodes": 0, "relationships": 0}
        return {
            "status": "ok" if healthy else "unavailable",
            "neo4j": healthy,
            **stats,
        }
    except Exception as e:
        return {
            "status": "unavailable",
            "neo4j": False,
            "nodes": 0,
            "relationships": 0,
            "error": str(e),
        }


@router.get("/graph", dependencies=[Depends(require_permissions("tests:read"))])
async def get_full_graph() -> dict[str, Any]:
    """Retrieve full dependency graph nodes/edges for visualization."""
    service = _neo4j_or_503()
    data = service.get_full_graph()
    if not data["nodes"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Graph is empty. POST /api/v1/dependencies/rebuild to seed the Incident Management module.",
        )
    return data


@router.get("/component/{id}", dependencies=[Depends(require_permissions("tests:read"))])
async def get_component_deps(id: str) -> dict[str, Any]:
    """Get all dependencies for a component."""
    service = _neo4j_or_503()
    return service.get_component_dependencies(id)


@router.get("/test/{id}", dependencies=[Depends(require_permissions("tests:read"))])
async def get_test_deps(id: str) -> dict[str, Any]:
    """Get dependency chain for a test case."""
    service = _neo4j_or_503()
    return service.get_test_dependency_chain(id)


@router.post("/rebuild", dependencies=[Depends(require_permissions("tests:write"))])
async def rebuild_graph() -> dict[str, str]:
    """Trigger full graph rebuild (clears and populates Incident Management demo graph)."""
    try:
        builder = GraphBuilderService()
        builder.rebuild_default_graph()
        stats = builder.neo4j.get_graph_stats()
        return {
            "status": "success",
            "message": "Graph successfully rebuilt.",
            "nodes": str(stats["nodes"]),
            "relationships": str(stats["relationships"]),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rebuild graph: {e}",
        ) from e
