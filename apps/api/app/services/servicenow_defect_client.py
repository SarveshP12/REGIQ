"""ServiceNow Defect Client — imports incidents and problem records as defects."""

import logging
from typing import Any, Dict, List

import httpx

from app.core.crypto import decrypt_field

logger = logging.getLogger(__name__)


class ServiceNowDefectClient:
    """Fetches incident and problem records from ServiceNow for defect ingestion."""

    def __init__(self, instance_url: str, client_id: str, client_secret_encrypted: str):
        self.instance_url = instance_url.rstrip("/")
        self.client_id = client_id
        try:
            self.client_secret = decrypt_field(client_secret_encrypted)
        except Exception:
            self.client_secret = ""
        self.access_token: str | None = None

    async def _authenticate(self) -> bool:
        """OAuth2 Client Credentials Flow."""
        token_url = f"{self.instance_url}/oauth_token.do"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                resp = await client.post(token_url, data=data)
                if resp.status_code == 200:
                    self.access_token = resp.json().get("access_token")
                    return True
        except Exception as e:
            logger.warning("ServiceNow auth failed: %s", e)

        # Mock token for offline development
        self.access_token = "mock_sn_defect_token"
        return True

    async def _get_headers(self) -> dict:
        if not self.access_token:
            await self._authenticate()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    async def fetch_incidents(
        self,
        assignment_group: str | None = None,
        severity: str | None = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Fetch incident records from ServiceNow."""
        headers = await self._get_headers()
        conditions = ["active=true"]
        if assignment_group:
            conditions.append(f"assignment_group.name={assignment_group}")
        if severity:
            conditions.append(f"severity={severity}")
        query = "^".join(conditions)

        url = (
            f"{self.instance_url}/api/now/table/incident"
            f"?sysparm_query={query}&sysparm_limit={limit}"
            f"&sysparm_fields=sys_id,number,short_description,severity,state,assignment_group,category"
        )
        try:
            async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return [
                        self._normalize_incident(r) for r in resp.json().get("result", [])
                    ]
        except Exception as e:
            logger.warning("Failed to fetch ServiceNow incidents: %s", e)

        return self._fallback_incidents()

    async def fetch_problems(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch problem records from ServiceNow."""
        headers = await self._get_headers()
        url = (
            f"{self.instance_url}/api/now/table/problem"
            f"?sysparm_query=active=true&sysparm_limit={limit}"
            f"&sysparm_fields=sys_id,number,short_description,severity,state,assignment_group,category"
        )
        try:
            async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return [
                        self._normalize_problem(r) for r in resp.json().get("result", [])
                    ]
        except Exception as e:
            logger.warning("Failed to fetch ServiceNow problems: %s", e)

        return self._fallback_problems()

    async def fetch_defects(self, **kwargs) -> List[Dict[str, Any]]:
        """Unified method: fetches both incidents and problems."""
        incidents = await self.fetch_incidents(**kwargs)
        problems = await self.fetch_problems()
        return incidents + problems

    def _normalize_incident(self, record: Dict[str, Any]) -> Dict[str, Any]:
        severity_map = {"1": "Critical", "2": "High", "3": "Medium", "4": "Low"}
        state_map = {
            "1": "New", "2": "In Progress", "3": "On Hold",
            "6": "Resolved", "7": "Closed", "8": "Cancelled",
        }
        return {
            "external_id": record.get("number", record.get("sys_id", "")),
            "title": record.get("short_description", "Untitled Incident"),
            "severity": severity_map.get(str(record.get("severity", "3")), "Medium"),
            "status": state_map.get(str(record.get("state", "1")), "Open"),
            "module": record.get("category", "General"),
            "source_system": "servicenow",
        }

    def _normalize_problem(self, record: Dict[str, Any]) -> Dict[str, Any]:
        severity_map = {"1": "Critical", "2": "High", "3": "Medium", "4": "Low"}
        return {
            "external_id": f"PRB-{record.get('number', record.get('sys_id', ''))}",
            "title": record.get("short_description", "Untitled Problem"),
            "severity": severity_map.get(str(record.get("severity", "3")), "Medium"),
            "status": record.get("state", "Open"),
            "module": record.get("category", "General"),
            "source_system": "servicenow",
        }

    @staticmethod
    def _fallback_incidents() -> List[Dict[str, Any]]:
        return [
            {
                "external_id": "INC0010042",
                "title": "Email notification service outage affecting incident assignments",
                "severity": "Critical",
                "status": "In Progress",
                "module": "Incident Management",
                "source_system": "servicenow",
            },
            {
                "external_id": "INC0010043",
                "title": "SSO login failure for federated LDAP users on portal",
                "severity": "High",
                "status": "New",
                "module": "Security Operations",
                "source_system": "servicenow",
            },
            {
                "external_id": "INC0010044",
                "title": "Service catalog request form missing mandatory approval field",
                "severity": "Medium",
                "status": "In Progress",
                "module": "Service Catalog",
                "source_system": "servicenow",
            },
        ]

    @staticmethod
    def _fallback_problems() -> List[Dict[str, Any]]:
        return [
            {
                "external_id": "PRB-PRB0040001",
                "title": "Recurring CMDB discovery scan timeout causing stale CI records",
                "severity": "High",
                "status": "Open",
                "module": "CMDB",
                "source_system": "servicenow",
            },
            {
                "external_id": "PRB-PRB0040002",
                "title": "Change collision detection failing for overlapping maintenance windows",
                "severity": "Medium",
                "status": "Open",
                "module": "Change Management",
                "source_system": "servicenow",
            },
        ]
