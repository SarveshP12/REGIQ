"""Pytest configuration — mock Neo4j driver when the package is not installed locally."""

import sys
from unittest.mock import MagicMock

if "neo4j" not in sys.modules:
    _mock = MagicMock()
    _mock.GraphDatabase = MagicMock()
    _mock.Driver = MagicMock()
    sys.modules["neo4j"] = _mock
