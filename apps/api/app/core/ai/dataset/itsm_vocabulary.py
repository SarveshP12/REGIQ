"""ITSM / ServiceNow vocabulary for NLP tokenization and NER."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

# Core ServiceNow platform vocabulary (modules, tables, technical terms)
SERVICENOW_MODULES = [
    "incident",
    "problem",
    "change_management",
    "service_catalog",
    "cmdb",
    "knowledge",
    "discovery",
    "service_mapping",
    "event_management",
    "asset_management",
    "hr_service_delivery",
    "customer_service_management",
    "security_operations",
    "virtual_agent",
    "predictive_intelligence",
    "performance_analytics",
    "agile_development",
    "devops",
    "governance_risk_compliance",
]

SERVICENOW_TABLES = [
    "incident",
    "problem",
    "change_request",
    "change_task",
    "task",
    "sc_req_item",
    "sc_task",
    "sc_cat_item",
    "cmdb_ci",
    "cmdb_ci_server",
    "cmdb_ci_appl",
    "cmdb_rel_ci",
    "sys_user",
    "sys_user_group",
    "sysapproval_approver",
    "kb_knowledge",
    "kb_category",
    "sla",
    "contract_sla",
    "ast_contract",
    "alm_asset",
    "sn_customerservice_case",
    "em_alert",
    "em_event",
    "wf_workflow",
    "sys_script",
    "sys_script_include",
    "sys_ui_action",
    "sys_ui_policy",
    "sys_client_script",
    "sys_rest_message",
    "sys_hub_flow",
    "sys_atf_test",
    "sys_atf_step",
]

SERVICENOW_TERMS = [
    "gliderecord",
    "glideajax",
    "glidesystem",
    "glideform",
    "glideaggregate",
    "business rule",
    "script include",
    "ui policy",
    "ui action",
    "client script",
    "data policy",
    "acl",
    "update set",
    "sys_id",
    "cmdb",
    "ci",
    "sla",
    "mttr",
    "mtbf",
    "priority",
    "urgency",
    "impact",
    "assignment group",
    "work notes",
    "close code",
    "resolution code",
    "major incident",
    "known error",
    "standard change",
    "normal change",
    "emergency change",
    "catalog item",
    "requested item",
    "fulfillment",
    "mid server",
    "integration hub",
    "flow designer",
    "service mapping",
    "discovery",
    "event management",
    "virtual agent",
    "predictive intelligence",
    "now assist",
    "atf",
    "automated test framework",
]

# ITSM abbreviations → expanded forms (used in NLP pipeline)
ITSM_ABBREVIATIONS = {
    "itsm": "IT service management",
    "cmdb": "configuration management database",
    "ci": "configuration item",
    "sla": "service level agreement",
    "slo": "service level objective",
    "kpi": "key performance indicator",
    "rfc": "request for change",
    "cab": "change advisory board",
    "p1": "priority 1 critical",
    "p2": "priority 2 high",
    "p3": "priority 3 moderate",
    "uat": "user acceptance testing",
    "e2e": "end to end",
    "api": "application programming interface",
    "rest": "representational state transfer",
    "soap": "simple object access protocol",
    "sso": "single sign on",
    "ldap": "lightweight directory access protocol",
    "grc": "governance risk compliance",
    "csm": "customer service management",
    "hrsd": "hr service delivery",
    "itom": "it operations management",
    "secops": "security operations",
}


def extract_corpus_terms(texts: Iterable[str], min_freq: int = 2) -> list[str]:
    """Extract frequent domain terms (bigrams/trigrams) from training corpus."""
    counter: Counter[str] = Counter()
    token_re = re.compile(r"[a-z][a-z0-9_]{2,}")
    for text in texts:
        lower = text.lower()
        tokens = token_re.findall(lower)
        for t in tokens:
            if t not in ("the", "and", "for", "with", "should", "successfully"):
                counter[t] += 1
        for i in range(len(tokens) - 1):
            bg = f"{tokens[i]} {tokens[i+1]}"
            counter[bg] += 1
    return [term for term, count in counter.most_common(500) if count >= min_freq]


def build_vocabulary(corpus_texts: Iterable[str] | None = None) -> dict:
    """Build full ITSM vocabulary document."""
    corpus_terms: list[str] = []
    if corpus_texts:
        corpus_terms = extract_corpus_terms(corpus_texts)

    return {
        "version": "1.0",
        "servicenow_modules": SERVICENOW_MODULES,
        "servicenow_tables": SERVICENOW_TABLES,
        "servicenow_terms": sorted(set(SERVICENOW_TERMS)),
        "abbreviations": ITSM_ABBREVIATIONS,
        "corpus_terms": corpus_terms,
        "spacy_entity_patterns": _entity_patterns(),
    }


def _entity_patterns() -> list[dict]:
    """SpaCy ruler-style patterns for ServiceNow entities."""
    patterns = []
    for table in SERVICENOW_TABLES:
        patterns.append({"label": "SN_TABLE", "pattern": table})
    for term in SERVICENOW_TERMS[:40]:
        patterns.append({"label": "SN_TERM", "pattern": term})
    return patterns


def save_vocabulary(vocab: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(vocab, indent=2), encoding="utf-8")
