"""Data models for Beads Integration Layer.

This module contains all data entities, enums, and dataclasses for
representing Beads issues, dependencies, and related structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


# T012: IssueStatus enum
class IssueStatus(str, Enum):
    """Valid states for an issue in the development workflow.

    Transitions:
        open → in_progress → closed
        open → blocked → in_progress → closed
        blocked → closed
    """

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    CLOSED = "closed"


# T013: IssueType enum
class IssueType(str, Enum):
    """Categories of work tracked in Beads.

    Priority Guidance:
        - bug: Usually P0-P2 (high priority)
        - feature: Usually P1-P3 (medium priority)
        - task: Usually P2-P3 (medium priority)
        - epic: Usually P1-P2 (large multi-issue effort)
        - chore: Usually P3-P4 (maintenance work)
    """

    BUG = "bug"
    FEATURE = "feature"
    TASK = "task"
    EPIC = "epic"
    CHORE = "chore"


# T014: DependencyType enum
class DependencyType(str, Enum):
    """Types of relationships between issues.

    Semantics:
        - blocks: Hard dependency (blocker MUST complete before blocked can close)
        - related: Soft association (informational link, no blocking)
        - parent-child: Hierarchical relationship (epic/subtask)
        - discovered-from: Provenance (blocked was discovered while working on blocker)
    """

    BLOCKS = "blocks"
    RELATED = "related"
    PARENT_CHILD = "parent-child"
    DISCOVERED_FROM = "discovered-from"
