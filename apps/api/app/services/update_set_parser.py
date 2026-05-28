"""ServiceNow update-set XML parser — extracts all 10 component types."""

from typing import Any
from xml.etree import ElementTree as ET


# Mapping of ServiceNow sys_class_name values to our component types
_CLASS_MAP: dict[str, str] = {
    "sys_script": "business_rule",
    "wf_activity": "workflow_activity",
    "sys_ui_policy": "ui_policy",
    "sys_ui_action": "ui_action",
    "sys_security_acl": "acl",
    "sys_script_include": "script_include",
    "sys_rest_message": "rest_api",
    "sys_rest_message_fn": "rest_api",
    "sc_cat_item": "catalog_item",
    "item_option_new": "catalog_variable",
    "sysauto_script": "scheduled_job",
    "sysevent_email_action": "email_notification",
    "sys_db_object": "table_definition",
    "sys_dictionary": "field_definition",
}

_COMPONENT_ATTRIBUTES: dict[str, list[str]] = {
    "business_rule": ["name", "collection", "when", "order", "script", "active", "filter_condition"],
    "workflow_activity": ["name", "workflow_version", "stage", "activity_type", "condition"],
    "ui_policy": ["table", "short_description", "condition", "active", "global"],
    "ui_action": ["table", "action_name", "condition", "script", "active"],
    "acl": ["name", "operation", "condition", "script", "type"],
    "script_include": ["name", "script", "client_callable", "active", "api_name"],
    "rest_api": ["name", "rest_endpoint", "http_method"],
    "catalog_item": ["name", "category", "short_description", "workflow"],
    "catalog_variable": ["name", "question_text", "type", "cat_item"],
    "scheduled_job": ["name", "run_type", "run_time", "script", "active"],
    "email_notification": ["name", "event_name", "condition", "template", "recipients"],
    "table_definition": ["name", "label", "super_class"],
    "field_definition": ["name", "element", "internal_type", "column_label", "max_length"],
}


def parse_update_set_xml(xml_content: str) -> list[dict[str, Any]]:
    """Parse a ServiceNow update-set XML and return a list of component dicts.

    Each component dict contains:
        - component_type: one of the 10 recognised types
        - component_name: human-readable name
        - scope: application scope if present
        - table_name: target table if applicable
        - change_type: created | modified | deleted
        - attributes: dict of extracted attributes for this component type
    """
    components: list[dict[str, Any]] = []

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return components

    # Walk every element looking for update-set entries
    # ServiceNow update set XML typically has <unload> or <record_update> structure
    for record in _find_records(root):
        sys_class = _get_text(record, "sys_class_name", "")
        component_type = _CLASS_MAP.get(sys_class)

        if not component_type:
            # Try to detect from the tag name or type attribute
            component_type = _infer_type(record)
            if not component_type:
                continue

        name = _get_text(record, "name") or _get_text(record, "sys_name") or _get_text(record, "short_description") or "Unknown"
        scope = _get_text(record, "sys_scope") or _get_text(record, "scope") or None
        table_name = _get_text(record, "collection") or _get_text(record, "name") or None
        action = _get_text(record, "action") or _get_text(record, "sys_mod_count", "0")

        # Determine change type
        change_type = "modified"
        if action in ("INSERT", "insert", "INSERT_OR_UPDATE"):
            change_type = "created"
        elif action in ("DELETE", "delete"):
            change_type = "deleted"

        # Extract type-specific attributes
        attrs: dict[str, Any] = {}
        for attr_name in _COMPONENT_ATTRIBUTES.get(component_type, []):
            val = _get_text(record, attr_name)
            if val is not None:
                attrs[attr_name] = val

        components.append({
            "component_type": component_type,
            "component_name": name,
            "scope": scope,
            "table_name": table_name if component_type in ("business_rule", "acl", "ui_policy", "ui_action", "table_definition", "field_definition") else None,
            "change_type": change_type,
            "attributes": attrs,
        })

    return components


def _find_records(root: ET.Element) -> list[ET.Element]:
    """Recursively find record-like elements in the XML tree."""
    records: list[ET.Element] = []

    # <sys_remote_update_set> wrapper or direct children
    for tag in ("sys_update_xml", "record_update", "sys_metadata"):
        records.extend(root.iter(tag))

    # If none found, treat all immediate children as records
    if not records:
        for child in root:
            # Look for any child that has a sys_class_name sub-element
            if child.find("sys_class_name") is not None:
                records.append(child)
            else:
                # Some exports wrap each record in a payload element
                for grandchild in child:
                    if grandchild.find("sys_class_name") is not None:
                        records.append(grandchild)

    return records


def _get_text(elem: ET.Element, tag: str, default: str | None = None) -> str | None:
    """Get text content of a child element."""
    child = elem.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    # Also try as attribute
    return elem.get(tag, default)


def _infer_type(elem: ET.Element) -> str | None:
    """Try to infer component type from element tag or attributes."""
    tag = elem.tag.lower()
    for class_name, comp_type in _CLASS_MAP.items():
        if class_name in tag:
            return comp_type
    return None
