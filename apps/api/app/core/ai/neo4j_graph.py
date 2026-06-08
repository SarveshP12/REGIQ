"""Legacy async Neo4j helper — delegates to the canonical Neo4jService."""

from typing import Any

from app.services.neo4j_service import Neo4jService


class Neo4jGraphBuilder:
    """Thin wrapper kept for backward compatibility with AI module imports."""

    def __init__(self) -> None:
        self._service = Neo4jService()

    async def close(self) -> None:
        Neo4jService.close()

    async def rebuild_graph(
        self, components: list[dict[str, Any]], test_cases: list[dict[str, Any]]
    ) -> None:
        from app.services.graph_builder import GraphBuilderService

        builder = GraphBuilderService()
        builder.neo4j.clear_all()
        for comp in components:
            builder.process_metadata_change(
                {
                    "sys_id": str(comp["id"]),
                    "name": comp.get("name", "Unknown"),
                    "sys_class_name": comp.get("type", "sys_script"),
                    "collection": comp.get("table", ""),
                }
            )
        for tc in test_cases:
            builder.link_test_case(
                tc_id=str(tc["id"]),
                title=tc.get("title", "Unknown"),
                description=tc.get("description", ""),
                steps_text="",
                tags=tc.get("tags", []),
            )

    async def get_graph(self) -> dict[str, Any]:
        return self._service.get_full_graph()

    async def get_component_graph(self, component_id: str) -> dict[str, Any]:
        return self._service.get_component_dependencies(component_id)


neo4j_builder = Neo4jGraphBuilder()
