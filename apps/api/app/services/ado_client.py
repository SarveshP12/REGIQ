"""Azure DevOps REST API client — fetches work items (bugs) for defect ingestion."""

import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


class AzureDevOpsClient:
    """Client for Azure DevOps REST API to fetch bug work items."""

    def __init__(self, organization: str, project: str, pat: str):
        self.organization = organization
        self.project = project
        self.base_url = f"https://dev.azure.com/{organization}/{project}"
        self.auth = ("", pat)  # PAT uses empty username

    async def fetch_defects(
        self,
        area_path: str | None = None,
        iteration_path: str | None = None,
        max_results: int = 200,
    ) -> List[Dict[str, Any]]:
        """Fetch bug work items from Azure DevOps using WIQL query.

        Returns normalized defect records matching the REGIQ defect schema.
        """
        # Build WIQL query
        conditions = ["[System.WorkItemType] = 'Bug'"]
        if area_path:
            conditions.append(f"[System.AreaPath] UNDER '{area_path}'")
        if iteration_path:
            conditions.append(f"[System.IterationPath] UNDER '{iteration_path}'")

        wiql = f"SELECT [System.Id] FROM WorkItems WHERE {' AND '.join(conditions)} ORDER BY [System.CreatedDate] DESC"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Step 1: Run WIQL query to get IDs
                wiql_url = f"{self.base_url}/_apis/wit/wiql?api-version=7.1"
                wiql_resp = await client.post(
                    wiql_url,
                    json={"query": wiql},
                    auth=self.auth,
                )
                if wiql_resp.status_code != 200:
                    logger.warning(
                        "ADO WIQL query failed (%s). Using fallback data.",
                        wiql_resp.status_code,
                    )
                    return self._fallback_defects()

                work_item_refs = wiql_resp.json().get("workItems", [])[:max_results]
                if not work_item_refs:
                    return []

                # Step 2: Batch fetch work item details
                ids = [str(ref["id"]) for ref in work_item_refs]
                ids_param = ",".join(ids[:200])
                fields = "System.Id,System.Title,Microsoft.VSTS.Common.Severity,System.State,System.AreaPath,System.IterationPath"
                detail_url = (
                    f"{self.base_url}/_apis/wit/workitems"
                    f"?ids={ids_param}&fields={fields}&api-version=7.1"
                )
                detail_resp = await client.get(detail_url, auth=self.auth)
                if detail_resp.status_code != 200:
                    logger.warning(
                        "ADO work item fetch failed (%s). Using fallback data.",
                        detail_resp.status_code,
                    )
                    return self._fallback_defects()

                items = detail_resp.json().get("value", [])
                return [self._normalize_work_item(item) for item in items]

        except Exception as e:
            logger.warning("Azure DevOps fetch failed: %s. Returning fallback data.", e)
            return self._fallback_defects()

    def _normalize_work_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize an ADO work item to the REGIQ defect schema."""
        fields = item.get("fields", {})
        severity_map = {
            "1 - Critical": "Critical",
            "2 - High": "High",
            "3 - Medium": "Medium",
            "4 - Low": "Low",
        }
        raw_severity = fields.get("Microsoft.VSTS.Common.Severity", "3 - Medium")
        area_path = fields.get("System.AreaPath", "")
        # Extract module from area path (last segment)
        module = area_path.split("\\")[-1] if area_path else None

        return {
            "external_id": f"ADO-{item.get('id', '0')}",
            "title": fields.get("System.Title", "Untitled Bug"),
            "severity": severity_map.get(raw_severity, "Medium"),
            "status": fields.get("System.State", "New"),
            "module": module,
            "source_system": "ado",
        }

    @staticmethod
    def _fallback_defects() -> List[Dict[str, Any]]:
        """Return sample ADO defect data for offline development."""
        return [
            {
                "external_id": "ADO-5001",
                "title": "Workflow approval stage skipped under concurrent load",
                "severity": "High",
                "status": "Active",
                "module": "Change Management",
                "source_system": "ado",
            },
            {
                "external_id": "ADO-5002",
                "title": "CMDB CI relationship import missing parent links",
                "severity": "Medium",
                "status": "New",
                "module": "CMDB",
                "source_system": "ado",
            },
            {
                "external_id": "ADO-5003",
                "title": "SLA timer not pausing on incident hold state",
                "severity": "Critical",
                "status": "Active",
                "module": "Incident Management",
                "source_system": "ado",
            },
            {
                "external_id": "ADO-5004",
                "title": "Knowledge article version diff shows incorrect delta",
                "severity": "Low",
                "status": "Resolved",
                "module": "Knowledge Management",
                "source_system": "ado",
            },
        ]
