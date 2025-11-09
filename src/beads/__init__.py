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

from beads.models import Issue, IssueStatus, IssueType, DependencyType, Dependency, DependencyTree
from beads.client import BeadsClient, create_beads_client

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
