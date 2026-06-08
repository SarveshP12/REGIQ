"""AI Classification Engine — Multi-label BERT-based test case classifier.

Classifies test cases across 6 dimensions:
  1. Business Process   (e.g., Incident Management, Change Management)
  2. Criticality Level  (Critical, High, Medium, Low)
  3. Test Case Type     (Functional, Regression, Integration, Performance, Security, UAT)
  4. Dependency Class   (Standalone, Component, Integration, End-to-End)
  5. Automation Feasibility (High, Medium, Low, Not Feasible)
  6. Execution Frequency (Every Release, Weekly, Sprint, Quarterly, Annually)

Uses a fine-tuned BERT model when available, falls back to a rule-based
heuristic classifier for bootstrapping before training data is collected.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

try:
    import torch
except ImportError:  # pragma: no cover - optional in slim Docker images
    torch = None  # type: ignore[assignment]

TORCH_AVAILABLE = torch is not None

from app.core.ai.nlp_pipeline import NLPResult, process_text
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# ── Classification Dimensions ────────────────────────────

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

ALL_DIMENSIONS = {
    "business_process": BUSINESS_PROCESS_LABELS,
    "criticality_level": CRITICALITY_LABELS,
    "test_case_type": TEST_TYPE_LABELS,
    "dependency_class": DEPENDENCY_CLASS_LABELS,
    "automation_feasibility": AUTOMATION_FEASIBILITY_LABELS,
    "execution_frequency": EXECUTION_FREQUENCY_LABELS,
}


@dataclass
class ClassificationResult:
    """Result of classifying a single test case."""

    business_process: str
    criticality_level: str
    test_case_type: str
    dependency_class: str
    automation_feasibility: str
    execution_frequency: str
    confidence_scores: dict[str, float] = field(default_factory=dict)
    needs_review: bool = False
    model_version: str = "rule-based-v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "business_process": self.business_process,
            "criticality_level": self.criticality_level,
            "test_case_type": self.test_case_type,
            "dependency_class": self.dependency_class,
            "automation_feasibility": self.automation_feasibility,
            "execution_frequency": self.execution_frequency,
            "confidence_scores": self.confidence_scores,
            "needs_review": self.needs_review,
            "model_version": self.model_version,
        }


# ── BERT Model Wrapper ───────────────────────────────────

_model = None
_tokenizer = None


def _load_bert_model() -> bool:
    """Attempt to load a fine-tuned BERT model from disk.

    Returns True if successful, False otherwise (fall back to rules).
    """
    global _model, _tokenizer
    if not TORCH_AVAILABLE:
        logger.warning("PyTorch not installed; using rule-based classifier")
        return False
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        model_path = settings.classifier_model_path
        _tokenizer = AutoTokenizer.from_pretrained(model_path)
        _model = AutoModelForSequenceClassification.from_pretrained(model_path)
        _model.eval()
        logger.info("Loaded fine-tuned BERT classifier from %s", model_path)
        return True
    except Exception as e:
        logger.warning("BERT model not available (%s), using rule-based fallback", e)
        return False


def _bert_classify(text: str) -> dict[str, tuple[str, float]]:
    """Classify text using the fine-tuned BERT model.

    Returns dict mapping dimension name to (predicted_label, confidence).
    """
    if not TORCH_AVAILABLE or _model is None or _tokenizer is None:
        return {}

    inputs = _tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True,
    )

    with torch.no_grad():
        outputs = _model(**inputs)
        logits = outputs.logits

    # The model outputs logits for all dimensions concatenated
    # Split by dimension sizes
    results: dict[str, tuple[str, float]] = {}
    offset = 0
    for dim_name, labels in ALL_DIMENSIONS.items():
        dim_logits = logits[0, offset : offset + len(labels)]
        probs = torch.softmax(dim_logits, dim=0)
        best_idx = int(torch.argmax(probs))
        confidence = float(probs[best_idx])
        results[dim_name] = (labels[best_idx], confidence)
        offset += len(labels)

    return results


# ── Rule-Based Fallback Classifier ───────────────────────

# Keyword → Business Process mapping
_BP_KEYWORDS: dict[str, list[str]] = {
    "Incident Management": [
        "incident", "p1", "p2", "major incident", "outage",
        "restore", "workaround", "escalation", "triage",
    ],
    "Problem Management": [
        "problem", "root cause", "known error", "rca",
        "problem task", "kedb",
    ],
    "Change Management": [
        "change request", "change_request", "cab", "change advisory",
        "standard change", "emergency change", "normal change", "rfc",
    ],
    "Service Catalog": [
        "catalog", "sc_req", "sc_task", "request item",
        "service request", "order guide", "catalog item",
    ],
    "Knowledge Management": [
        "knowledge", "kb_knowledge", "article", "knowledge base",
    ],
    "Asset Management": [
        "asset", "alm_asset", "hardware asset", "software license",
    ],
    "CMDB": [
        "cmdb", "configuration item", "ci", "cmdb_ci", "discovery",
        "service mapping", "relationship",
    ],
    "HR Service Delivery": [
        "hr case", "onboarding", "offboarding", "hr service",
    ],
    "Customer Service Management": [
        "csm", "customer", "case", "sn_customerservice",
    ],
    "Security Operations": [
        "security", "vulnerability", "threat", "siem", "secops",
    ],
    "IT Operations Management": [
        "itom", "event management", "alert", "monitoring", "health log",
    ],
}

_TYPE_KEYWORDS: dict[str, list[str]] = {
    "Functional": ["verify", "validate", "check", "ensure", "confirm", "functional"],
    "Regression": ["regression", "retest", "re-test", "existing functionality"],
    "Integration": ["integration", "api", "rest", "soap", "interface", "mid server"],
    "Performance": ["performance", "load", "stress", "response time", "throughput"],
    "Security": ["security", "authentication", "authorization", "xss", "injection", "acl"],
    "UAT": ["uat", "user acceptance", "business validation", "stakeholder"],
    "Smoke": ["smoke", "sanity", "basic check", "health check"],
    "Exploratory": ["exploratory", "ad-hoc", "investigate"],
}


def _rule_based_classify(nlp_result: NLPResult) -> ClassificationResult:
    """Rule-based heuristic classifier for bootstrapping.

    Analyses cleaned text, ServiceNow entities, and key phrases
    to make classification decisions.
    """
    text_lower = nlp_result.cleaned_text.lower()
    scores: dict[str, float] = {}

    # ── Business Process ─────────────────────────────────
    bp_scores: dict[str, float] = {bp: 0.0 for bp in BUSINESS_PROCESS_LABELS}
    for bp, keywords in _BP_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                bp_scores[bp] += 1.0
    # Boost from ServiceNow table detection
    table_bp_map = {
        "incident": "Incident Management",
        "problem": "Problem Management",
        "change_request": "Change Management",
        "sc_req_item": "Service Catalog",
        "sc_task": "Service Catalog",
        "kb_knowledge": "Knowledge Management",
        "cmdb_ci": "CMDB",
        "cmdb_ci_server": "CMDB",
        "cmdb_ci_appl": "CMDB",
    }
    for table in nlp_result.servicenow_tables:
        mapped_bp = table_bp_map.get(table)
        if mapped_bp:
            bp_scores[mapped_bp] += 2.0

    best_bp = max(bp_scores, key=lambda k: bp_scores[k])
    bp_confidence = min(bp_scores[best_bp] / 5.0, 1.0) if bp_scores[best_bp] > 0 else 0.3
    if bp_scores[best_bp] == 0:
        best_bp = "Other"
        bp_confidence = 0.3
    scores["business_process"] = bp_confidence

    # ── Test Case Type ───────────────────────────────────
    type_scores: dict[str, float] = {t: 0.0 for t in TEST_TYPE_LABELS}
    for test_type, keywords in _TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                type_scores[test_type] += 1.0
    best_type = max(type_scores, key=lambda k: type_scores[k])
    type_confidence = min(type_scores[best_type] / 3.0, 1.0) if type_scores[best_type] > 0 else 0.4
    if type_scores[best_type] == 0:
        best_type = "Functional"
        type_confidence = 0.4
    scores["test_case_type"] = type_confidence

    # ── Criticality Level ────────────────────────────────
    crit_indicators = {
        "Critical": ["p1", "critical", "production down", "outage", "sev1", "revenue", "data loss"],
        "High": ["p2", "high", "major", "significant", "business impact"],
        "Medium": ["p3", "medium", "moderate", "normal"],
        "Low": ["p4", "low", "minor", "cosmetic", "informational"],
    }
    crit_scores = {c: 0.0 for c in CRITICALITY_LABELS}
    for level, indicators in crit_indicators.items():
        for indicator in indicators:
            if indicator in text_lower:
                crit_scores[level] += 1.0
    best_crit = max(crit_scores, key=lambda k: crit_scores[k])
    crit_confidence = min(crit_scores[best_crit] / 2.0, 1.0) if crit_scores[best_crit] > 0 else 0.4
    if crit_scores[best_crit] == 0:
        best_crit = "Medium"
        crit_confidence = 0.4
    scores["criticality_level"] = crit_confidence

    # ── Dependency Class ─────────────────────────────────
    integration_count = len(nlp_result.servicenow_apis) + len(nlp_result.servicenow_tables)
    if integration_count >= 4 or "end-to-end" in text_lower or "e2e" in text_lower:
        dep_class = "End-to-End"
        dep_confidence = 0.7
    elif integration_count >= 2 or "integration" in text_lower:
        dep_class = "Integration"
        dep_confidence = 0.65
    elif integration_count == 1 or "component" in text_lower:
        dep_class = "Component"
        dep_confidence = 0.6
    else:
        dep_class = "Standalone"
        dep_confidence = 0.5
    scores["dependency_class"] = dep_confidence

    # ── Automation Feasibility ───────────────────────────
    auto_positive = ["automated", "script", "selenium", "atf", "api test", "unit test"]
    auto_negative = ["manual", "visual", "exploratory", "usability", "ad-hoc"]
    auto_score = 0.0
    for kw in auto_positive:
        if kw in text_lower:
            auto_score += 1.0
    for kw in auto_negative:
        if kw in text_lower:
            auto_score -= 1.0

    if auto_score >= 2:
        auto_feas = "High"
        auto_conf = 0.75
    elif auto_score >= 1:
        auto_feas = "Medium"
        auto_conf = 0.6
    elif auto_score <= -1:
        auto_feas = "Not Feasible"
        auto_conf = 0.6
    else:
        auto_feas = "Medium"
        auto_conf = 0.45
    scores["automation_feasibility"] = auto_conf

    # ── Execution Frequency ──────────────────────────────
    freq_map = {
        "Every Release": ["every release", "release gate", "smoke", "sanity", "critical path"],
        "Weekly": ["weekly", "scheduled", "recurring"],
        "Sprint": ["sprint", "iteration", "biweekly"],
        "Quarterly": ["quarterly", "periodic", "audit"],
        "Annually": ["annually", "annual", "yearly", "compliance"],
    }
    freq_scores = {f: 0.0 for f in EXECUTION_FREQUENCY_LABELS}
    for freq, keywords in freq_map.items():
        for kw in keywords:
            if kw in text_lower:
                freq_scores[freq] += 1.0
    best_freq = max(freq_scores, key=lambda k: freq_scores[k])
    freq_confidence = min(freq_scores[best_freq] / 2.0, 1.0) if freq_scores[best_freq] > 0 else 0.35
    if freq_scores[best_freq] == 0:
        best_freq = "Sprint"
        freq_confidence = 0.35
    scores["execution_frequency"] = freq_confidence

    # ── Determine if review is needed ────────────────────
    avg_confidence = sum(scores.values()) / len(scores)
    needs_review = avg_confidence < settings.classification_confidence_threshold

    return ClassificationResult(
        business_process=best_bp,
        criticality_level=best_crit,
        test_case_type=best_type,
        dependency_class=dep_class,
        automation_feasibility=auto_feas,
        execution_frequency=best_freq,
        confidence_scores=scores,
        needs_review=needs_review,
        model_version="rule-based-v1",
    )


# ── Public API ───────────────────────────────────────────


def classify_test_case(
    title: str,
    description: Optional[str] = None,
    steps: Optional[str] = None,
) -> ClassificationResult:
    """Classify a single test case across all 6 dimensions.

    Tries the BERT model first, falls back to rule-based if unavailable.
    """
    # Combine all text fields
    combined = title
    if description:
        combined += f" {description}"
    if steps:
        combined += f" {steps}"

    # NLP preprocessing
    nlp_result = process_text(combined, include_ner=True)

    # Try BERT model first
    bert_results = _bert_classify(nlp_result.cleaned_text)
    if bert_results:
        scores = {dim: conf for dim, (_, conf) in bert_results.items()}
        avg_conf = sum(scores.values()) / len(scores)

        return ClassificationResult(
            business_process=bert_results["business_process"][0],
            criticality_level=bert_results["criticality_level"][0],
            test_case_type=bert_results["test_case_type"][0],
            dependency_class=bert_results["dependency_class"][0],
            automation_feasibility=bert_results["automation_feasibility"][0],
            execution_frequency=bert_results["execution_frequency"][0],
            confidence_scores=scores,
            needs_review=avg_conf < settings.classification_confidence_threshold,
            model_version="bert-tcc-v1",
        )

    # Fall back to rule-based
    return _rule_based_classify(nlp_result)


def classify_batch(
    test_cases: list[dict[str, Optional[str]]],
) -> list[ClassificationResult]:
    """Classify a batch of test cases.

    Each dict in the list should have keys: title, description, steps.
    """
    results = []
    for tc in test_cases:
        result = classify_test_case(
            title=tc.get("title", ""),
            description=tc.get("description"),
            steps=tc.get("steps"),
        )
        results.append(result)
    return results


# Attempt to load model at module import time (non-blocking)
try:
    _load_bert_model()
except Exception:
    pass
