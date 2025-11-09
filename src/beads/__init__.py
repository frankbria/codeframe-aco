"""
Beads Integration Layer

Python interface for the Beads issue tracker CLI, enabling programmatic
DAG management for autonomous orchestration.

This package provides:
- Issue CRUD operations
- Dependency graph queries
- Status synchronization
- JSON parsing of bd command outputs
"""

from beads.client import BeadsClient, create_beads_client
from beads.models import Dependency, DependencyTree, DependencyType, Issue, IssueStatus, IssueType

__version__ = "0.1.0"

__all__ = [
    "Issue",
    "IssueStatus",
    "IssueType",
    "DependencyType",
    "Dependency",
    "DependencyTree",
    "BeadsClient",
    "create_beads_client",
]
