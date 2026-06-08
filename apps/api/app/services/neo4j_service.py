"""Neo4j Graph Database Service — handles dependency mapping and impact analysis."""

import logging
from typing import Any, Optional
from uuid import UUID

from neo4j import GraphDatabase, Driver

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Neo4jService:
    """Service to connect and interact with Neo4j database."""

    _driver: Optional[Driver] = None

    @classmethod
    def get_driver(cls) -> Driver:
        """Get or initialize the Neo4j driver (singleton)."""
        if cls._driver is None:
            try:
                cls._driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password)
                )
                # Verify connectivity
                cls._driver.verify_connectivity()
                logger.info("Successfully connected to Neo4j database")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j database: {e}")
                raise
        return cls._driver

    @classmethod
    def close(cls):
        """Close the Neo4j driver connection."""
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None
            logger.info("Closed Neo4j driver connection")

    def __init__(self):
        self.driver = self.get_driver()

    def initialize_schema(self):
        """Create constraints and indexes to enforce uniqueness and speed up queries."""
        constraints = [
            "CREATE CONSTRAINT component_id_unique IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT bp_id_unique IF NOT EXISTS FOR (b:BusinessProcess) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT table_name_unique IF NOT EXISTS FOR (t:Table) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT workflow_id_unique IF NOT EXISTS FOR (w:Workflow) REQUIRE w.id IS UNIQUE",
            "CREATE CONSTRAINT integration_id_unique IF NOT EXISTS FOR (i:Integration) REQUIRE i.id IS UNIQUE",
            "CREATE CONSTRAINT testcase_id_unique IF NOT EXISTS FOR (t:TestCase) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT defect_id_unique IF NOT EXISTS FOR (d:Defect) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT release_id_unique IF NOT EXISTS FOR (r:Release) REQUIRE r.id IS UNIQUE",
        ]
        with self.driver.session() as session:
            for c in constraints:
                try:
                    session.run(c)
                except Exception as e:
                    logger.warning(f"Error creating Neo4j constraint: {e}")

    # ── Node operations ──────────────────────────────────────

    def upsert_component(self, comp_id: str, name: str, comp_type: str, scope: str = "global", table: str = "", script_hash: str = ""):
        """Upsert a Component node."""
        query = """
        MERGE (c:Component {id: $comp_id})
        SET c.name = $name,
            c.type = $comp_type,
            c.scope = $scope,
            c.table = $table,
            c.script_hash = $script_hash,
            c.last_modified = timestamp(),
            c.active = true
        RETURN c
        """
        with self.driver.session() as session:
            session.run(query, comp_id=comp_id, name=name, comp_type=comp_type, scope=scope, table=table, script_hash=script_hash)

    def upsert_business_process(self, bp_id: str, name: str, module: str, criticality: str = "Medium", owner: str = "", sla_impact: float = 0.0):
        """Upsert a BusinessProcess node."""
        query = """
        MERGE (b:BusinessProcess {id: $bp_id})
        SET b.name = $name,
            b.module = $module,
            b.criticality = $criticality,
            b.owner = $owner,
            b.sla_impact = $sla_impact
        RETURN b
        """
        with self.driver.session() as session:
            session.run(query, bp_id=bp_id, name=name, module=module, criticality=criticality, owner=owner, sla_impact=sla_impact)

    def upsert_table(self, name: str, scope: str = "global", parent_table: str = "", field_count: int = 0, is_audited: bool = True):
        """Upsert a Table node."""
        query = """
        MERGE (t:Table {name: $name})
        SET t.scope = $scope,
            t.parent_table = $parent_table,
            t.field_count = $field_count,
            t.is_audited = $is_audited
        RETURN t
        """
        with self.driver.session() as session:
            session.run(query, name=name, scope=scope, parent_table=parent_table, field_count=field_count, is_audited=is_audited)

    def upsert_test_case(self, tc_id: str, title: str, criticality: str = "medium", tc_type: str = "Functional", automation_flag: str = "manual"):
        """Upsert a TestCase node."""
        query = """
        MERGE (t:TestCase {id: $tc_id})
        SET t.title = $title,
            t.criticality = $criticality,
            t.type = $tc_type,
            t.automation_flag = $automation_flag
        RETURN t
        """
        with self.driver.session() as session:
            session.run(query, tc_id=tc_id, title=title, criticality=criticality, tc_type=tc_type, automation_flag=automation_flag)

    def upsert_workflow(self, wf_id: str, name: str, table: str, version: str = "1.0", active: bool = True, stage_count: int = 1):
        """Upsert a Workflow node."""
        query = """
        MERGE (w:Workflow {id: $wf_id})
        SET w.name = $name,
            w.table = $table,
            w.version = $version,
            w.active = $active,
            w.stage_count = $stage_count
        RETURN w
        """
        with self.driver.session() as session:
            session.run(query, wf_id=wf_id, name=name, table=table, version=version, active=active, stage_count=stage_count)

    def upsert_integration(self, int_id: str, name: str, int_type: str, direction: str = "both", protocol: str = "REST", target_system: str = ""):
        """Upsert an Integration node."""
        query = """
        MERGE (i:Integration {id: $int_id})
        SET i.name = $name,
            i.type = $int_type,
            i.direction = $direction,
            i.protocol = $protocol,
            i.target_system = $target_system
        RETURN i
        """
        with self.driver.session() as session:
            session.run(query, int_id=int_id, name=name, int_type=int_type, direction=direction, protocol=protocol, target_system=target_system)

    def upsert_defect(self, defect_id: str, title: str, severity: str = "Medium", status: str = "Open", recurrence_count: int = 1):
        """Upsert a Defect node."""
        query = """
        MERGE (d:Defect {id: $defect_id})
        SET d.title = $title,
            d.severity = $severity,
            d.status = $status,
            d.recurrence_count = $recurrence_count
        RETURN d
        """
        with self.driver.session() as session:
            session.run(query, defect_id=defect_id, title=title, severity=severity, status=status, recurrence_count=recurrence_count)

    def upsert_release(self, rel_id: str, name: str, date_str: str = "", rel_type: str = "minor", risk_score: float = 0.0):
        """Upsert a Release node."""
        query = """
        MERGE (r:Release {id: $rel_id})
        SET r.name = $name,
            r.date = $date_str,
            r.type = $rel_type,
            r.risk_score = $risk_score
        RETURN r
        """
        with self.driver.session() as session:
            session.run(query, rel_id=rel_id, name=name, date_str=date_str, rel_type=rel_type, risk_score=risk_score)

    # ── Relationship Operations ────────────────────────────────

    def create_relationship(self, from_label: str, from_id: str, to_label: str, to_id: str, rel_type: str, weight: float = 1.0):
        """Create a relationship from one node to another."""
        # Clean label/rel strings to prevent Injection (parameterization is not supported for labels/rels in Cypher)
        # Note: Cypher parameters can't specify labels or relationship types, so we interpolate them safely.
        safe_from_lbl = "".join(c for c in from_label if c.isalnum())
        safe_to_lbl = "".join(c for c in to_label if c.isalnum())
        safe_rel_type = "".join(c for c in rel_type if c.isalnum() or c == '_')

        # Custom ID key depending on node type (Table uses 'name', others use 'id')
        from_key = "name" if safe_from_lbl == "Table" else "id"
        to_key = "name" if safe_to_lbl == "Table" else "id"

        query = f"""
        MATCH (a:{safe_from_lbl} {{{from_key}: $from_id}})
        MATCH (b:{safe_to_lbl} {{{to_key}: $to_id}})
        MERGE (a)-[r:{safe_rel_type}]->(b)
        SET r.weight = $weight
        RETURN r
        """
        with self.driver.session() as session:
            session.run(query, from_id=from_id, to_id=to_id, weight=weight)

    # ── Dependency Querying ───────────────────────────────────

    def get_full_graph(self, limit: int = 150) -> dict[str, list[dict]]:
        """Retrieve all nodes and edges for visualization up to a limit."""
        nodes: dict[str, dict] = {}
        edges: list[dict] = []

        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            for record in result:
                n = record["n"]
                r = record["r"]
                m = record["m"]

                # Process node n
                if n:
                    n_id = n.get("id") or n.get("name")
                    if n_id and n_id not in nodes:
                        labels = list(n.labels)
                        nodes[n_id] = {
                            "id": n_id,
                            "label": n.get("name") or n.get("title") or n_id,
                            "type": labels[0] if labels else "Unknown",
                            "properties": dict(n),
                        }

                # Process node m
                if m:
                    m_id = m.get("id") or m.get("name")
                    if m_id and m_id not in nodes:
                        labels = list(m.labels)
                        nodes[m_id] = {
                            "id": m_id,
                            "label": m.get("name") or m.get("title") or m_id,
                            "type": labels[0] if labels else "Unknown",
                            "properties": dict(m),
                        }

                # Process edge r
                if r and n and m:
                    from_id = n.get("id") or n.get("name")
                    to_id = m.get("id") or m.get("name")
                    edge_id = f"{from_id}-{r.type}-{to_id}"
                    edges.append({
                        "id": edge_id,
                        "source": from_id,
                        "target": to_id,
                        "type": r.type,
                        "weight": r.get("weight", 1.0),
                    })

        return {"nodes": list(nodes.values()), "edges": edges}

    def get_component_dependencies(self, comp_id: str, max_depth: int = 3) -> dict[str, list[dict]]:
        """Find upstream and downstream dependencies for a component up to max_depth."""
        nodes: dict[str, dict] = {}
        edges: list[dict] = []

        # Find dependency tree using variable length path
        query = """
        MATCH (c:Component {id: $comp_id})
        MATCH path = (c)-[*1..3]-(n)
        RETURN path LIMIT 100
        """
        with self.driver.session() as session:
            result = session.run(query, comp_id=comp_id)
            for record in result:
                path = record["path"]
                # Traverse path segments to collect nodes and relationships
                for relationship in path.relationships:
                    start_node = relationship.start_node
                    end_node = relationship.end_node

                    for node in (start_node, end_node):
                        nid = node.get("id") or node.get("name")
                        if nid not in nodes:
                            labels = list(node.labels)
                            nodes[nid] = {
                                "id": nid,
                                "label": node.get("name") or node.get("title") or nid,
                                "type": labels[0] if labels else "Unknown",
                                "properties": dict(node),
                            }

                    sid = start_node.get("id") or start_node.get("name")
                    tid = end_node.get("id") or end_node.get("name")
                    edge_id = f"{sid}-{relationship.type}-{tid}"
                    if not any(e["id"] == edge_id for e in edges):
                        edges.append({
                            "id": edge_id,
                            "source": sid,
                            "target": tid,
                            "type": relationship.type,
                            "weight": relationship.get("weight", 1.0),
                        })

        return {"nodes": list(nodes.values()), "edges": edges}

    def get_test_dependency_chain(self, test_case_id: str) -> dict[str, list[dict]]:
        """Get the dependency chain for a test case (what components/processes it validates)."""
        nodes: dict[str, dict] = {}
        edges: list[dict] = []

        query = """
        MATCH (t:TestCase {id: $test_case_id})
        MATCH path = (t)-[:TESTS|COVERS|VALIDATES*1..3]-(n)
        RETURN path LIMIT 50
        """
        with self.driver.session() as session:
            result = session.run(query, test_case_id=test_case_id)
            for record in result:
                path = record["path"]
                for relationship in path.relationships:
                    start_node = relationship.start_node
                    end_node = relationship.end_node

                    for node in (start_node, end_node):
                        nid = node.get("id") or node.get("name")
                        if nid not in nodes:
                            labels = list(node.labels)
                            nodes[nid] = {
                                "id": nid,
                                "label": node.get("name") or node.get("title") or nid,
                                "type": labels[0] if labels else "Unknown",
                                "properties": dict(node),
                            }

                    sid = start_node.get("id") or start_node.get("name")
                    tid = end_node.get("id") or end_node.get("name")
                    edge_id = f"{sid}-{relationship.type}-{tid}"
                    if not any(e["id"] == edge_id for e in edges):
                        edges.append({
                            "id": edge_id,
                            "source": sid,
                            "target": tid,
                            "type": relationship.type,
                            "weight": relationship.get("weight", 1.0),
                        })

        return {"nodes": list(nodes.values()), "edges": edges}

    def check_health(self) -> bool:
        """Return True when the driver can reach the Neo4j instance."""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            logger.warning("Neo4j health check failed: %s", e)
            return False

    def get_graph_stats(self) -> dict[str, int]:
        """Return node and relationship counts for operational verification."""
        query = """
        MATCH (n)
        WITH count(n) AS node_count
        MATCH ()-[r]->()
        RETURN node_count, count(r) AS rel_count
        """
        with self.driver.session() as session:
            record = session.run(query).single()
            if not record:
                return {"nodes": 0, "relationships": 0}
            return {
                "nodes": record["node_count"],
                "relationships": record["rel_count"],
            }

    def link_test_case_to_table_components(
        self, tc_id: str, table_name: str, rel_type: str = "TESTS", weight: float = 0.85
    ) -> int:
        """Link a test case to every component that depends on the given table."""
        query = """
        MATCH (t:TestCase {id: $tc_id})
        MATCH (c:Component)-[:DEPENDS_ON]->(tbl:Table {name: $table_name})
        MERGE (t)-[r:TESTS]->(c)
        SET r.weight = $weight
        RETURN count(r) AS linked
        """
        with self.driver.session() as session:
            record = session.run(
                query, tc_id=tc_id, table_name=table_name, weight=weight
            ).single()
            return int(record["linked"]) if record else 0

    def clear_all(self):
        """Wipe the graph clean. Primarily for testing and clean rebuilds."""
        query = "MATCH (n) DETACH DELETE n"
        with self.driver.session() as session:
            session.run(query)
