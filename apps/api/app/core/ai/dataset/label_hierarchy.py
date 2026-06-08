"""Label hierarchy and CSV → TCC classifier dimension mappings."""

from __future__ import annotations

from typing import Any

# Canonical labels (must align with app.core.ai.classifier)
BUSINESS_PROCESS_LABELS = [
    "Incident Management",
    "Problem Management",
    "Change Management",
    "Service Catalog",
    "Knowledge Management",
    "Asset Management",
    "CMDB",
    "HR Service Delivery",
    "Customer Service Management",
    "Security Operations",
    "IT Operations Management",
    "Other",
]

CRITICALITY_LABELS = ["Critical", "High", "Medium", "Low"]
TEST_TYPE_LABELS = [
    "Functional",
    "Regression",
    "Integration",
    "Performance",
    "Security",
    "UAT",
    "Smoke",
    "Exploratory",
]
DEPENDENCY_CLASS_LABELS = ["Standalone", "Component", "Integration", "End-to-End"]
AUTOMATION_FEASIBILITY_LABELS = ["High", "Medium", "Low", "Not Feasible"]
EXECUTION_FREQUENCY_LABELS = [
    "Every Release",
    "Weekly",
    "Sprint",
    "Quarterly",
    "Annually",
]

DIMENSIONS = {
    "business_process": BUSINESS_PROCESS_LABELS,
    "criticality_level": CRITICALITY_LABELS,
    "test_case_type": TEST_TYPE_LABELS,
    "dependency_class": DEPENDENCY_CLASS_LABELS,
    "automation_feasibility": AUTOMATION_FEASIBILITY_LABELS,
    "execution_frequency": EXECUTION_FREQUENCY_LABELS,
}

# Map CSV "Business Process of Section" → canonical business_process
BUSINESS_PROCESS_SOURCE_MAP: dict[str, str] = {
    "Incident Logging": "Incident Management",
    "Incident Resolution": "Incident Management",
    "Incident Hold Process": "Incident Management",
    "Major Incident Process": "Incident Management",
    "Incident Workflow": "Incident Management",
    "Priority Calculation": "Incident Management",
    "SLA Management": "Incident Management",
    "Change Enablement": "Change Management",
    "Problem Investigation": "Problem Management",
    "Configuration Management": "CMDB",
    "Knowledge Integration": "Knowledge Management",
    "Customer Support": "Customer Service Management",
    "Relationship Management": "Customer Service Management",
    "Application Management": "Asset Management",
    "Automation": "IT Operations Management",
    "Intelligent Automation": "IT Operations Management",
    "Agent Intelligence": "IT Operations Management",
    "Platform Administration": "IT Operations Management",
    "Process Governance": "IT Operations Management",
    "ITSM Maturity": "Other",
    "ITSM Roadmap": "Other",
}

# Map CSV "Reference Section from Document" → module (hierarchy level 1)
MODULE_SOURCE_MAP: dict[str, str] = {
    "Change Management": "change_management",
    "Service Desk": "service_desk",
    "Governance": "governance",
    "CMDB": "cmdb",
    "Platform Architecture": "platform",
    "Automation": "automation",
    "State: New": "incident",
    "Problem Management": "problem",
    "Parent and Child Incidents": "incident",
    "State: Resolved": "incident",
    "State: On Hold": "incident",
    "Major Incident Management": "incident",
    "Priority Management": "incident",
    "State: In Progress": "incident",
    "Roadmap Planning": "governance",
    "Knowledge Management": "knowledge",
    "Service Level Management": "itsm_core",
}

# Hierarchy: canonical business process → source labels + ServiceNow module id
LABEL_HIERARCHY: dict[str, Any] = {
    "version": "1.0",
    "dimensions": DIMENSIONS,
    "business_process_tree": {
        "Incident Management": {
            "module": "incident",
            "servicenow_tables": ["incident", "task", "sysapproval_approver"],
            "source_business_processes": [
                k for k, v in BUSINESS_PROCESS_SOURCE_MAP.items() if v == "Incident Management"
            ],
            "source_sections": [
                "State: New",
                "State: Resolved",
                "State: On Hold",
                "State: In Progress",
                "Parent and Child Incidents",
                "Major Incident Management",
                "Priority Management",
                "Service Level Management",
            ],
        },
        "Change Management": {
            "module": "change_management",
            "servicenow_tables": ["change_request", "change_task"],
            "source_business_processes": ["Change Enablement"],
            "source_sections": ["Change Management"],
        },
        "Problem Management": {
            "module": "problem",
            "servicenow_tables": ["problem", "known_error"],
            "source_business_processes": ["Problem Investigation"],
            "source_sections": ["Problem Management"],
        },
        "CMDB": {
            "module": "cmdb",
            "servicenow_tables": ["cmdb_ci", "cmdb_rel_ci", "discovery_schedule"],
            "source_business_processes": ["Configuration Management"],
            "source_sections": ["CMDB"],
        },
        "Knowledge Management": {
            "module": "knowledge",
            "servicenow_tables": ["kb_knowledge", "kb_category"],
            "source_business_processes": ["Knowledge Integration"],
            "source_sections": ["Knowledge Management"],
        },
        "Customer Service Management": {
            "module": "csm",
            "servicenow_tables": ["sn_customerservice_case", "customer_contact"],
            "source_business_processes": ["Customer Support", "Relationship Management"],
            "source_sections": ["Service Desk"],
        },
        "IT Operations Management": {
            "module": "itom",
            "servicenow_tables": ["em_alert", "em_event", "sa_metric_map"],
            "source_business_processes": [
                "Automation",
                "Intelligent Automation",
                "Agent Intelligence",
                "Platform Administration",
            ],
            "source_sections": ["Automation", "Platform Architecture"],
        },
        "Other": {
            "module": "itsm_core",
            "servicenow_tables": ["sys_metadata", "sys_scope"],
            "source_business_processes": ["ITSM Maturity", "ITSM Roadmap", "Process Governance"],
            "source_sections": ["Governance", "Roadmap Planning"],
        },
    },
    "mappings": {
        "business_process_from_csv_section": BUSINESS_PROCESS_SOURCE_MAP,
        "module_from_reference_section": MODULE_SOURCE_MAP,
    },
}

# Keyword rules for dimensions not present as CSV columns
CRITICALITY_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("p1", "critical", "major incident", "outage", "production down", "sev-1"), "Critical"),
    (("p2", "high priority", "sla breach", "urgent", "sev-2"), "High"),
    (("p3", "medium", "moderate"), "Medium"),
]

TEST_TYPE_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("regression", "retest", "re-run"), "Regression"),
    (("integration", "api", "rest", "soap", "webhook", "mid server"), "Integration"),
    (("performance", "load test", "stress"), "Performance"),
    (("security", "acl", "encryption", "vulnerability"), "Security"),
    (("uat", "user acceptance"), "UAT"),
    (("smoke", "sanity"), "Smoke"),
    (("exploratory", "ad hoc"), "Exploratory"),
]

DEPENDENCY_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("end-to-end", "e2e", "full workflow", "catalog to fulfillment"), "End-to-End"),
    (("integration", "api", "connector", "webhook", "ldap", "sso"), "Integration"),
    (("business rule", "script include", "workflow", "ui policy", "client script"), "Component"),
]

AUTOMATION_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("atf", "automated test", "ui runner", "headless"), "High"),
    (("verify field", "assert", "validate record", "check state"), "Medium"),
    (("manual", "exploratory", "ad hoc review"), "Low"),
]

FREQUENCY_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("every release", "each deployment", "regression suite"), "Every Release"),
    (("weekly", "sprint"), "Sprint"),
    (("quarterly", "qbr"), "Quarterly"),
    (("annual", "yearly"), "Annually"),
]


def _match_keywords(text: str, rules: list[tuple[tuple[str, ...], str]], default: str) -> str:
    lower = text.lower()
    for keywords, label in rules:
        if any(kw in lower for kw in keywords):
            return label
    return default


def map_business_process(
    csv_business_process: str,
    reference_section: str = "",
) -> str:
    """Map raw CSV business process or section to canonical label."""
    if csv_business_process in BUSINESS_PROCESS_SOURCE_MAP:
        return BUSINESS_PROCESS_SOURCE_MAP[csv_business_process]
    section = reference_section.strip()
    if section in ("Change Management",):
        return "Change Management"
    if section in ("Problem Management",):
        return "Problem Management"
    if section in ("CMDB",):
        return "CMDB"
    if section.startswith("State:") or section in (
        "Parent and Child Incidents",
        "Major Incident Management",
        "Priority Management",
        "Service Level Management",
    ):
        return "Incident Management"
    if section in ("Knowledge Management",):
        return "Knowledge Management"
    if section in ("Service Desk",):
        return "Customer Service Management"
    if section in ("Automation", "Platform Architecture"):
        return "IT Operations Management"
    return "Other"


def infer_secondary_labels(text: str) -> dict[str, str]:
    """Infer non-CSV classification dimensions from combined test text."""
    return {
        "criticality_level": _match_keywords(text, CRITICALITY_KEYWORDS, "Medium"),
        "test_case_type": _match_keywords(text, TEST_TYPE_KEYWORDS, "Functional"),
        "dependency_class": _match_keywords(text, DEPENDENCY_KEYWORDS, "Standalone"),
        "automation_feasibility": _match_keywords(text, AUTOMATION_KEYWORDS, "Medium"),
        "execution_frequency": _match_keywords(text, FREQUENCY_KEYWORDS, "Every Release"),
    }


def build_labels_for_row(row: dict[str, str]) -> dict[str, str]:
    """Produce all six TCC dimension labels for a CSV row."""
    combined = " ".join(
        filter(
            None,
            [
                row.get("Test Scenario Detail", ""),
                row.get("Test Case Description", ""),
                row.get("Step Description", ""),
                row.get("Expected Result", ""),
                row.get("Reference Subsection from Document", ""),
            ],
        )
    )
    bp = map_business_process(
        row.get("Business Process of Section", ""),
        row.get("Reference Section from Document", ""),
    )
    labels = {
        "business_process": bp,
        **infer_secondary_labels(combined),
    }
    return labels
