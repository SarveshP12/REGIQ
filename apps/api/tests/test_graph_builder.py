"""Unit tests for Neo4j graph builder (mocked driver)."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.graph_builder import GraphBuilderService, MODULE_DEFINITIONS


@pytest.fixture
def builder() -> GraphBuilderService:
    with patch.object(GraphBuilderService, "__init__", lambda self: None):
        svc = GraphBuilderService()
        svc.neo4j = MagicMock()
        return svc


def test_process_metadata_change_business_rule(builder: GraphBuilderService):
    builder.process_metadata_change(
        {
            "sys_id": "br_001",
            "name": "Validate Priority",
            "sys_class_name": "sys_script",
            "collection": "incident",
            "script": "var gr = new GlideRecord('incident');",
        }
    )
    builder.neo4j.upsert_component.assert_called_once()
    builder.neo4j.create_relationship.assert_any_call(
        "Component", "br_001", "Table", "incident", "DEPENDS_ON", 1.0
    )
    builder.neo4j.upsert_table.assert_called_with(name="incident")


def test_process_metadata_change_table(builder: GraphBuilderService):
    builder.process_metadata_change(
        {
            "sys_id": "tbl_x",
            "name": "incident",
            "sys_class_name": "sys_db_object",
        }
    )
    builder.neo4j.upsert_table.assert_any_call(name="incident", parent_table="", scope="global")
    builder.neo4j.upsert_component.assert_not_called()


def test_ensure_module_scaffold_incident(builder: GraphBuilderService):
    builder.ensure_module_scaffold("incident")
    defn = MODULE_DEFINITIONS["incident"]
    builder.neo4j.upsert_business_process.assert_called_once()
    assert builder.neo4j.upsert_business_process.call_args.kwargs["bp_id"] == defn["bp_id"]


def test_link_test_case_covers_and_validates(builder: GraphBuilderService):
    builder.link_test_case(
        tc_id="tc-1",
        title="Incident SLA validation",
        description="Create incident and verify SLA",
        steps_text="Open incident form",
        tags=["incident", "regression"],
    )
    builder.neo4j.upsert_test_case.assert_called_once()
    builder.neo4j.create_relationship.assert_any_call(
        "TestCase", "tc-1", "Table", "incident", "COVERS", 0.7
    )
    builder.neo4j.create_relationship.assert_any_call(
        "TestCase", "tc-1", "BusinessProcess", "bp_incident_mgmt", "VALIDATES", 1.0
    )
    builder.neo4j.link_test_case_to_table_components.assert_called_with("tc-1", "incident")


def test_rebuild_default_graph_clears_and_builds(builder: GraphBuilderService):
    builder.rebuild_default_graph()
    builder.neo4j.clear_all.assert_called_once()
    assert builder.neo4j.create_relationship.call_count > 10
