"""NLP Pipeline — HTML stripping, ServiceNow markup cleaning, SpaCy NER.

Strips ServiceNow-specific HTML/XML markup from test case text, then
applies SpaCy NLP for tokenization and named entity recognition focused
on ServiceNow domain entities (table names, roles, API endpoints).
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup

# SpaCy is loaded lazily to avoid import-time overhead in workers that
# don't need NLP.  The model download is handled at container build time.
_nlp = None


def _get_spacy_nlp():
    """Lazy-load the SpaCy English model."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            import spacy
            # Fallback: download inline if model isn't installed
            from spacy.cli import download  # type: ignore[attr-defined]
            download("en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")
    return _nlp


# ── ServiceNow Entity Patterns ───────────────────────────

# Common ServiceNow table names
SN_TABLE_PATTERN = re.compile(
    r"\b(incident|problem|change_request|sc_req_item|sc_task|"
    r"cmdb_ci|cmdb_ci_server|cmdb_ci_appl|sys_user|sys_user_group|"
    r"kb_knowledge|sla|task|wf_workflow|sys_script|sys_ui_action|"
    r"sys_properties|sys_dictionary|sc_cat_item|sys_attachment)\b",
    re.IGNORECASE,
)

# ServiceNow API endpoint patterns
SN_API_PATTERN = re.compile(
    r"/api/now/(?:table|import|attachment|aggregate)/[\w.]+",
    re.IGNORECASE,
)

# ServiceNow role patterns
SN_ROLE_PATTERN = re.compile(
    r"\b(itil|admin|snc_internal|catalog_admin|"
    r"knowledge_admin|asset|change_manager|problem_manager|"
    r"incident_manager|sn_customerservice_agent)\b",
    re.IGNORECASE,
)


@dataclass
class NLPResult:
    """Result of the NLP processing pipeline."""

    cleaned_text: str
    tokens: list[str] = field(default_factory=list)
    entities: list[dict[str, str]] = field(default_factory=list)
    servicenow_tables: list[str] = field(default_factory=list)
    servicenow_apis: list[str] = field(default_factory=list)
    servicenow_roles: list[str] = field(default_factory=list)
    key_phrases: list[str] = field(default_factory=list)


def strip_html_markup(raw_text: str) -> str:
    """Remove HTML/XML tags and ServiceNow-specific markup from text.

    Handles:
    - Standard HTML tags (from rich-text fields)
    - ServiceNow Journal entries markup
    - XML from Update Sets
    - CDATA sections
    """
    if not raw_text:
        return ""

    # Remove CDATA sections
    text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", raw_text, flags=re.DOTALL)

    # Remove XML processing instructions
    text = re.sub(r"<\?xml.*?\?>", "", text, flags=re.DOTALL)

    # Use BeautifulSoup for robust HTML stripping
    soup = BeautifulSoup(text, "html.parser")

    # Extract text, preserving line breaks from block elements
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.insert_after("\n")

    cleaned = soup.get_text(separator=" ")

    # Normalise whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Remove ServiceNow-specific escape sequences
    cleaned = re.sub(r"\\n|\\r|\\t", " ", cleaned)

    return cleaned


def extract_servicenow_entities(text: str) -> dict[str, list[str]]:
    """Extract ServiceNow-specific entities using regex patterns.

    Returns dict with keys: tables, apis, roles
    """
    tables = list({m.lower() for m in SN_TABLE_PATTERN.findall(text)})
    apis = list(set(SN_API_PATTERN.findall(text)))
    roles = list({m.lower() for m in SN_ROLE_PATTERN.findall(text)})

    return {"tables": sorted(tables), "apis": sorted(apis), "roles": sorted(roles)}


def process_text(
    raw_text: str,
    include_ner: bool = True,
    description: Optional[str] = None,
) -> NLPResult:
    """Full NLP processing pipeline for a test case text field.

    1. Strip HTML/markup
    2. Extract ServiceNow entities via regex
    3. Run SpaCy tokenization and NER
    4. Extract key noun phrases

    Args:
        raw_text: The raw test case title/description/steps text.
        include_ner: Whether to run SpaCy NER (can be disabled for speed).
        description: Optional additional description text to include.

    Returns:
        NLPResult with all extracted information.
    """
    # Step 1: Clean text
    combined = raw_text
    if description:
        combined = f"{raw_text} {description}"

    cleaned = strip_html_markup(combined)

    if not cleaned:
        return NLPResult(cleaned_text="")

    # Step 2: ServiceNow entity extraction (fast, regex-based)
    sn_entities = extract_servicenow_entities(cleaned)

    # Step 3: SpaCy NLP processing
    tokens: list[str] = []
    entities: list[dict[str, str]] = []
    key_phrases: list[str] = []

    if include_ner:
        nlp = _get_spacy_nlp()
        doc = nlp(cleaned[:10000])  # Limit to prevent OOM on very long texts

        # Tokenisation (filter stopwords and punctuation)
        tokens = [
            token.lemma_.lower()
            for token in doc
            if not token.is_stop and not token.is_punct and len(token.text) > 1
        ]

        # Named entities
        entities = [
            {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
            for ent in doc.ents
        ]

        # Key noun phrases (chunks)
        key_phrases = [
            chunk.text.lower()
            for chunk in doc.noun_chunks
            if len(chunk.text) > 3
        ]

    return NLPResult(
        cleaned_text=cleaned,
        tokens=tokens,
        entities=entities,
        servicenow_tables=sn_entities["tables"],
        servicenow_apis=sn_entities["apis"],
        servicenow_roles=sn_entities["roles"],
        key_phrases=key_phrases[:50],  # Cap key phrases
    )
