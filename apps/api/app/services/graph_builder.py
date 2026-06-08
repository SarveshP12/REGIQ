"""Graph Builder Service — parses ServiceNow updates and structures the Neo4j dependency model."""

import logging
import re
from typing import Any

from app.services.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)

# ServiceNow module → business process scaffold (used on sync and demo rebuild)
MODULE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "incident": {
        "bp_id": "bp_incident_mgmt",
        "name": "Incident Management",
        "module": "ITSM",
        "criticality": "Critical",
        "tables": ["incident", "task"],
    },
    "change_request": {
        "bp_id": "bp_change_mgmt",
        "name": "Change Management",
        "module": "ITSM",
        "criticality": "High",
        "tables": ["change_request", "task"],
    },
}

TABLE_CLASS_NAMES = frozenset({"sys_db_object", "sys_dictionary"})
WORKFLOW_CLASS_NAMES = frozenset(
    {"wf_workflow", "sys_hub_flow", "flow_designer_flow", "sys_workflow"}
)
INTEGRATION_CLASS_NAMES = frozenset(
    {"sys_rest_message", "sys_soap_message", "sys_transform_map", "sys_data_source"}
)
COMPONENT_CLASS_TYPES = {
    "sys_script": "Business Rule",
    "sys_script_include": "Script Include",
    "sys_ui_action": "UI Action",
    "sys_ui_policy": "UI Policy",
    "sys_client_script": "Client Script",
    "sys_variable_value": "Workflow Variable",
}


class GraphBuilderService:
    """Service responsible for translating metadata and test suites into Neo4j nodes and edges."""

    def __init__(self):
        self.neo4j = Neo4jService()
        self.neo4j.initialize_schema()

    def rebuild_default_graph(self):
        """Wipes and populates the graph with a complete ServiceNow module (Incident Management) for dev/testing."""
        self.neo4j.clear_all()
        logger.info("Cleared existing Neo4j graph for rebuild")

        # ── 1. Business processes ─────────────────────────────
        self.neo4j.upsert_business_process(
            bp_id="bp_incident_mgmt",
            name="Incident Management",
            module="ITSM",
            criticality="Critical",
            owner="Aileen Mottern",
            sla_impact=9.5,
        )
        self.neo4j.upsert_business_process(
            bp_id="bp_change_mgmt",
            name="Change Management",
            module="ITSM",
            criticality="High",
            owner="John Smith",
            sla_impact=8.0,
        )

        # ── 2. Tables ───────────────────────────────────────
        self.neo4j.upsert_table(
            name="incident", scope="global", parent_table="task", field_count=98, is_audited=True
        )
        self.neo4j.upsert_table(name="task", scope="global", field_count=52, is_audited=True)
        self.neo4j.upsert_table(
            name="change_request", scope="global", parent_table="task", field_count=84, is_audited=True
        )
        self.neo4j.upsert_table(name="sys_user", scope="global", field_count=35, is_audited=False)

        self.neo4j.create_relationship("Table", "incident", "Table", "task", "EXTENDED_BY", 1.0)
        self.neo4j.create_relationship("Table", "change_request", "Table", "task", "EXTENDED_BY", 1.0)
        self.neo4j.create_relationship("Table", "incident", "Table", "sys_user", "REFERENCES", 0.65)

        self.neo4j.create_relationship("Table", "incident", "BusinessProcess", "bp_incident_mgmt", "FULFILLS", 0.75)
        self.neo4j.create_relationship(
            "Table", "change_request", "BusinessProcess", "bp_change_mgmt", "FULFILLS", 0.75
        )
        self.neo4j.create_relationship("BusinessProcess", "bp_incident_mgmt", "Table", "incident", "COVERS_TABLE", 1.0)
        self.neo4j.create_relationship(
            "BusinessProcess", "bp_change_mgmt", "Table", "change_request", "COVERS_TABLE", 1.0
        )

        # ── 3. Components ───────────────────────────────────
        self.neo4j.upsert_component(
            comp_id="comp_br_validate_fields",
            name="Validate Critical Fields",
            comp_type="Business Rule",
            scope="global",
            table="incident",
        )
        self.neo4j.upsert_component(
            comp_id="comp_si_incident_utils",
            name="IncidentUtils",
            comp_type="Script Include",
            scope="global",
        )
        self.neo4j.upsert_component(
            comp_id="comp_br_sla_triggers",
            name="Trigger SLA Countdown",
            comp_type="Business Rule",
            scope="global",
            table="incident",
        )
        self.neo4j.upsert_component(
            comp_id="comp_si_change_risk",
            name="ChangeRiskEvaluator",
            comp_type="Script Include",
            scope="global",
            table="change_request",
        )

        # ── 4. Workflows ──────────────────────────────────────
        self.neo4j.upsert_workflow(
            wf_id="wf_incident_routing",
            name="Incident Routing Workflow",
            table="incident",
            version="1.2",
            active=True,
            stage_count=4,
        )
        self.neo4j.upsert_workflow(
            wf_id="wf_change_approval",
            name="Change Request Approval Engine",
            table="change_request",
            version="2.0",
            active=True,
            stage_count=5,
        )

        # ── 5. Integrations ───────────────────────────────────
        self.neo4j.upsert_integration(
            int_id="int_ms_teams",
            name="MS Teams Notification Webhook",
            int_type="Outbound Webhook",
            direction="outbound",
            protocol="REST",
            target_system="Microsoft Teams",
        )

        # ── 6. Defects & releases ─────────────────────────────
        self.neo4j.upsert_defect(
            defect_id="def_1001",
            title="SLA timers fail to load on mobile browsers",
            severity="High",
            status="Open",
            recurrence_count=3,
        )
        self.neo4j.upsert_release(
            rel_id="rel_q2_2026",
            name="Q2 2026 ITSM Patch",
            date_str="2026-06-01",
            rel_type="minor",
            risk_score=6.5,
        )

        # ── 7. Test cases ─────────────────────────────────────
        self.neo4j.upsert_test_case(
            tc_id="tc_verify_incident_sla",
            title="Verify Incident Creation with SLA triggers",
            criticality="high",
            tc_type="Regression",
            automation_flag="automated",
        )
        self.neo4j.upsert_test_case(
            tc_id="tc_change_risk_assessment",
            title="Given assessment questions, verify Change Risk calculations",
            criticality="medium",
            tc_type="Functional",
            automation_flag="manual",
        )

        # ── 8. Relationships (PRD-aligned edge types) ─────────
        for comp_id in (
            "comp_br_validate_fields",
            "comp_br_sla_triggers",
            "comp_si_incident_utils",
        ):
            self.neo4j.create_relationship(
                "BusinessProcess", "bp_incident_mgmt", "Component", comp_id, "HAS_COMPONENT", 1.0
            )

        self.neo4j.create_relationship(
            "BusinessProcess", "bp_change_mgmt", "Component", "comp_si_change_risk", "HAS_COMPONENT", 1.0
        )

        self.neo4j.create_relationship(
            "Component", "comp_br_validate_fields", "Table", "incident", "DEPENDS_ON", 1.0
        )
        self.neo4j.create_relationship(
            "Component", "comp_br_sla_triggers", "Table", "incident", "DEPENDS_ON", 1.0
        )
        self.neo4j.create_relationship(
            "Component", "comp_br_sla_triggers", "Component", "comp_si_incident_utils", "DEPENDS_ON", 0.9
        )
        self.neo4j.create_relationship(
            "Component", "comp_si_change_risk", "Table", "change_request", "DEPENDS_ON", 1.0
        )

        self.neo4j.create_relationship("Workflow", "wf_incident_routing", "Table", "incident", "EXECUTES_ON", 1.0)
        self.neo4j.create_relationship(
            "Workflow", "wf_change_approval", "Table", "change_request", "EXECUTES_ON", 1.0
        )
        self.neo4j.create_relationship(
            "Component", "comp_br_validate_fields", "Workflow", "wf_incident_routing", "TRIGGERS", 0.8
        )
        self.neo4j.create_relationship(
            "Integration", "int_ms_teams", "Workflow", "wf_incident_routing", "CALLS_WORKFLOW", 0.85
        )
        self.neo4j.create_relationship(
            "Component", "comp_br_sla_triggers", "Integration", "int_ms_teams", "INTEGRATES_WITH", 0.85
        )

        self.neo4j.create_relationship(
            "Defect", "def_1001", "Component", "comp_br_sla_triggers", "LINKED_TO_COMPONENT", 1.0
        )
        self.neo4j.create_relationship(
            "Release", "rel_q2_2026", "Component", "comp_br_sla_triggers", "INCLUDES_CHANGE", 1.0
        )

        self.neo4j.create_relationship(
            "TestCase", "tc_verify_incident_sla", "Component", "comp_br_sla_triggers", "TESTS", 1.0
        )
        self.neo4j.create_relationship(
            "TestCase", "tc_verify_incident_sla", "Table", "incident", "COVERS", 0.8
        )
        self.neo4j.create_relationship(
            "TestCase", "tc_verify_incident_sla", "BusinessProcess", "bp_incident_mgmt", "VALIDATES", 1.0
        )
        self.neo4j.create_relationship(
            "TestCase", "tc_verify_incident_sla", "Defect", "def_1001", "LINKED_TO_DEFECT", 0.9
        )

        self.neo4j.create_relationship(
            "TestCase", "tc_change_risk_assessment", "Component", "comp_si_change_risk", "TESTS", 1.0
        )
        self.neo4j.create_relationship(
            "TestCase", "tc_change_risk_assessment", "Table", "change_request", "COVERS", 0.8
        )
        self.neo4j.create_relationship(
            "TestCase", "tc_change_risk_assessment", "BusinessProcess", "bp_change_mgmt", "VALIDATES", 1.0
        )

        logger.info("Successfully completed graph rebuild for Incident Management module")

    def ensure_module_scaffold(self, table_name: str) -> None:
        """Ensure business process and table nodes exist for a ServiceNow module table."""
        module_key = table_name if table_name in MODULE_DEFINITIONS else None
        if not module_key:
            for key, defn in MODULE_DEFINITIONS.items():
                if table_name in defn.get("tables", []):
                    module_key = key
                    break
        if not module_key:
            return

        defn = MODULE_DEFINITIONS[module_key]
        self.neo4j.upsert_business_process(
            bp_id=defn["bp_id"],
            name=defn["name"],
            module=defn["module"],
            criticality=defn["criticality"],
        )
        for tbl in defn["tables"]:
            self.neo4j.upsert_table(name=tbl)
            self.neo4j.create_relationship("Table", tbl, "BusinessProcess", defn["bp_id"], "FULFILLS", 0.75)
            self.neo4j.create_relationship("BusinessProcess", defn["bp_id"], "Table", tbl, "COVERS_TABLE", 1.0)

    def process_metadata_change(self, change: dict[str, Any]) -> None:
        """Parse a ServiceNow update set/sync record and map it to graph nodes and edges."""
        sys_id = change.get("sys_id")
        if not sys_id:
            return

        name = change.get("name", "Unknown ServiceNow Component")
        class_name = (change.get("sys_class_name") or change.get("type") or "").lower()
        table = change.get("collection") or change.get("table") or ""
        script_body = change.get("script") or change.get("script_plain") or ""

        if class_name in TABLE_CLASS_NAMES or change.get("element_type") == "table":
            table_name = change.get("name") or table
            if table_name:
                self.neo4j.upsert_table(
                    name=table_name,
                    parent_table=change.get("super_class", ""),
                    scope=change.get("scope", "global"),
                )
                self.ensure_module_scaffold(table_name)
            return

        if class_name in WORKFLOW_CLASS_NAMES:
            self.neo4j.upsert_workflow(
                wf_id=sys_id,
                name=name,
                table=table,
                version=change.get("version", "1.0"),
                active=change.get("active", "true") != "false",
            )
            if table:
                self.neo4j.upsert_table(name=table)
                self.neo4j.create_relationship("Workflow", sys_id, "Table", table, "EXECUTES_ON", 1.0)
                self.ensure_module_scaffold(table)
            return

        if class_name in INTEGRATION_CLASS_NAMES:
            self.neo4j.upsert_integration(
                int_id=sys_id,
                name=name,
                int_type=class_name,
                protocol=change.get("protocol", "REST"),
                target_system=change.get("target_system", ""),
            )
            return

        comp_type = COMPONENT_CLASS_TYPES.get(class_name, "Metadata Resource")
        self.neo4j.upsert_component(
            comp_id=sys_id,
            name=name,
            comp_type=comp_type,
            scope=change.get("scope", "global"),
            table=table,
            script_hash=change.get("sys_hash", ""),
        )

        if table:
            self.neo4j.upsert_table(name=table)
            self.neo4j.create_relationship("Component", sys_id, "Table", table, "DEPENDS_ON", 1.0)
            self.ensure_module_scaffold(table)
            module_def = MODULE_DEFINITIONS.get(table) or next(
                (d for d in MODULE_DEFINITIONS.values() if table in d.get("tables", [])), None
            )
            if module_def:
                self.neo4j.create_relationship(
                    "BusinessProcess", module_def["bp_id"], "Component", sys_id, "HAS_COMPONENT", 1.0
                )

        self._extract_script_dependencies(sys_id, script_body)
        logger.info("Processed ServiceNow update for %s (%s)", name, comp_type)

    def _extract_script_dependencies(self, comp_id: str, script_body: str) -> None:
        """Infer DEPENDS_ON edges from GlideRecord / Script Include references in script text."""
        if not script_body:
            return

        for match in re.finditer(r"GlideRecord\(['\"]([a-z0-9_]+)['\"]\)", script_body, re.I):
            ref_table = match.group(1).lower()
            self.neo4j.upsert_table(name=ref_table)
            self.neo4j.create_relationship("Component", comp_id, "Table", ref_table, "DEPENDS_ON", 0.7)

        for match in re.finditer(r"new\s+([A-Za-z0-9_]+)\s*\(", script_body):
            include_name = match.group(1)
            if include_name.startswith(("Glide", "gs", "JSON")):
                continue
            # Heuristic: match demo script includes by normalized name
            known = {
                "IncidentUtils": "comp_si_incident_utils",
                "ChangeRiskEvaluator": "comp_si_change_risk",
            }
            target_id = known.get(include_name)
            if target_id:
                self.neo4j.create_relationship(
                    "Component", comp_id, "Component", target_id, "DEPENDS_ON", 0.85
                )

    def process_metadata_batch(self, changes: list[dict[str, Any]]) -> int:
        """Process a list of ServiceNow metadata records; returns count processed."""
        for change in changes:
            self.process_metadata_change(change)
        return len(changes)

    def link_test_case(
        self, tc_id: str, title: str, description: str, steps_text: str, tags: list[str]
    ) -> None:
        """Link a test case to components, tables, and business processes in Neo4j."""
        self.neo4j.upsert_test_case(
            tc_id=tc_id,
            title=title,
            tc_type="Regression" if "regression" in [t.lower() for t in tags] else "Functional",
        )

        known_tables = ["incident", "change_request", "problem", "task", "sys_user", "cmdb_ci"]
        combined_text = f"{title} {description} {steps_text}".lower()
        tag_lower = [t.lower() for t in tags]

        covered_tables: list[str] = []
        for t in known_tables:
            if t in combined_text or t in tag_lower:
                self.neo4j.upsert_table(name=t)
                self.neo4j.create_relationship("TestCase", tc_id, "Table", t, "COVERS", 0.7)
                covered_tables.append(t)
                self.neo4j.link_test_case_to_table_components(tc_id, t)

        module_keywords = {
            "incident": "bp_incident_mgmt",
            "change": "bp_change_mgmt",
            "change_request": "bp_change_mgmt",
        }
        for keyword, bp_id in module_keywords.items():
            if keyword in combined_text or keyword in tag_lower:
                self.neo4j.create_relationship("TestCase", tc_id, "BusinessProcess", bp_id, "VALIDATES", 1.0)

        if "sla" in combined_text:
            self.neo4j.create_relationship(
                "TestCase", tc_id, "Component", "comp_br_sla_triggers", "TESTS", 1.0
            )
        if "risk" in combined_text:
            self.neo4j.create_relationship(
                "TestCase", tc_id, "Component", "comp_si_change_risk", "TESTS", 1.0
            )
        if "validate" in combined_text:
            self.neo4j.create_relationship(
                "TestCase", tc_id, "Component", "comp_br_validate_fields", "TESTS", 1.0
            )
        if "routing" in combined_text:
            self.neo4j.create_relationship(
                "TestCase", tc_id, "Workflow", "wf_incident_routing", "TESTS", 1.0
            )
