"""Jira REST API client — fetches bug issues for defect ingestion.

Supports:
  - JQL-based search with pagination
  - Field normalization to REGIQ defect schema
  - Fallback sample data for offline development
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class JiraClient:
    """Client for Jira Cloud / Server REST API."""

    def __init__(self, base_url: str, email: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (email, token)

    async def fetch_defects(
        self,
        jql: str = "type = Bug ORDER BY created DESC",
        max_results: int = 200,
    ) -> List[Dict[str, Any]]:
        """Fetch bugs from Jira using JQL search with automatic pagination.

        Returns normalized defect records matching the REGIQ defect schema.
        """
        all_defects: List[Dict[str, Any]] = []
        start_at = 0
        page_size = min(max_results, 100)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                while start_at < max_results:
                    url = f"{self.base_url}/rest/api/3/search"
                    payload = {
                        "jql": jql,
                        "fields": [
                            "summary",
                            "priority",
                            "status",
                            "components",
                            "fixVersions",
                            "labels",
                            "created",
                            "updated",
                            "resolution",
                        ],
                        "startAt": start_at,
                        "maxResults": page_size,
                    }
                    response = await client.post(url, json=payload, auth=self.auth)

                    if response.status_code != 200:
                        logger.warning(
                            "Jira search failed (%s). Using fallback data.",
                            response.status_code,
                        )
                        return self._fallback_defects()

                    data = response.json()
                    issues = data.get("issues", [])
                    if not issues:
                        break

                    for issue in issues:
                        all_defects.append(self._normalize_issue(issue))

                    total = data.get("total", 0)
                    start_at += page_size
                    if start_at >= total:
                        break

                return all_defects

        except Exception as e:
            logger.warning("Jira fetch failed: %s. Returning fallback data.", e)
            return self._fallback_defects()

    def _normalize_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a Jira issue to the REGIQ defect schema."""
        fields = issue.get("fields", {})
        priority = fields.get("priority", {})
        status = fields.get("status", {})
        components = fields.get("components", [])

        # Map Jira priority to REGIQ severity
        priority_map = {
            "Highest": "Critical",
            "Blocker": "Critical",
            "High": "High",
            "Medium": "Medium",
            "Low": "Low",
            "Lowest": "Low",
        }
        raw_priority = priority.get("name", "Medium") if priority else "Medium"

        # Extract module from components
        module = components[0].get("name") if components else None

        return {
            "external_id": issue.get("key", "UNKNOWN-0"),
            "title": fields.get("summary", "Untitled Bug"),
            "severity": priority_map.get(raw_priority, "Medium"),
            "status": status.get("name", "Open") if status else "Open",
            "module": module,
            "source_system": "jira",
        }

    @staticmethod
    def _fallback_defects() -> List[Dict[str, Any]]:
        """Return sample defect data for offline development."""
        return [
            {
                "external_id": "BUG-101",
                "title": "Login page crash on mobile Safari when SSO redirect fails",
                "severity": "High",
                "status": "Open",
                "module": "Auth",
                "source_system": "jira",
            },
            {
                "external_id": "BUG-102",
                "title": "Incorrect CMDB CI relationship mapping on bulk import",
                "severity": "Medium",
                "status": "In Progress",
                "module": "CMDB",
                "source_system": "jira",
            },
            {
                "external_id": "BUG-103",
                "title": "Change request approval chain breaks with parallel approvers",
                "severity": "Critical",
                "status": "Open",
                "module": "Change Management",
                "source_system": "jira",
            },
            {
                "external_id": "BUG-104",
                "title": "Incident auto-assignment rule ignoring shift schedule timezone",
                "severity": "High",
                "status": "In Progress",
                "module": "Incident Management",
                "source_system": "jira",
            },
            {
                "external_id": "BUG-105",
                "title": "Knowledge article search returning archived drafts in results",
                "severity": "Low",
                "status": "Open",
                "module": "Knowledge Management",
                "source_system": "jira",
            },
        ]


# Default singleton — uses mock credentials for development
jira_client = JiraClient(
    base_url="https://regiq.atlassian.net",
    email="user@regiq.com",
    token="token_mock",
)
