"""Data models for Beads Integration Layer.

This module contains all data entities, enums, and dataclasses for
representing Beads issues, dependencies, and related structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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


# T035: Issue dataclass with validation
@dataclass
class Issue:
    """Represents a single unit of work in the Beads DAG.

    This dataclass maps directly to Beads JSON output and provides
    type-safe interfaces for working with issues in Python.

    Attributes:
        id: Unique issue identifier (e.g., "codeframe-aco-xon")
        title: Human-readable issue title (non-empty, max 500 chars)
        description: Detailed issue description (can be empty string)
        status: Current workflow state
        priority: Priority level (0=critical, 4=backlog)
        issue_type: Category of work
        created_at: When issue was created
        updated_at: When issue was last modified
        content_hash: SHA256 hash of issue content (Beads internal)
        source_repo: Repository path where issue was created
        assignee: Username of assigned person (optional)
        labels: List of label strings (optional)

    State Transitions:
        open → in_progress → closed
          ↓         ↓
        blocked → in_progress → closed

    Business Rules:
        - Issue ID is immutable after creation
        - status cannot transition from closed back to open
        - priority can change at any time
        - created_at is immutable, updated_at changes on modification
    """

    id: str
    title: str
    description: str
    status: IssueStatus
    priority: int
    issue_type: IssueType
    created_at: datetime
    updated_at: datetime
    content_hash: str
    source_repo: str
    assignee: str | None = None
    labels: list[str] | None = field(default=None)

    def __post_init__(self) -> None:
        """Validate Issue fields after initialization.

        Raises:
            ValueError: If validation fails for any field
        """
        # Validate ID
        if not self.id:
            raise ValueError("Issue ID cannot be empty")

        # Validate title
        if not self.title:
            raise ValueError("Title cannot be empty")

        # Validate priority range
        if not (0 <= self.priority <= 4):
            raise ValueError("Priority must be 0-4")

    # T036: Issue.from_json() with datetime parsing
    @classmethod
    def from_json(cls, data: dict) -> "Issue":
        """Parse Issue from Beads JSON output.

        Args:
            data: Raw JSON dict from bd command

        Returns:
            Issue instance with parsed and validated data

        Raises:
            ValueError: If required fields are missing or invalid
            KeyError: If required fields are missing from JSON

        Example:
            >>> json_data = {"id": "test-123", "title": "Bug fix", ...}
            >>> issue = Issue.from_json(json_data)
        """
        # Parse datetime strings to datetime objects
        # Beads uses RFC3339 format: 2025-11-07T12:00:00Z or with timezone offset
        created_at_str = data["created_at"]
        updated_at_str = data["updated_at"]

        # Handle both formats: with 'Z' suffix and with timezone offset
        # Python's fromisoformat can handle most ISO 8601 formats
        # Replace 'Z' with '+00:00' for Python 3.11+ compatibility
        if created_at_str.endswith("Z"):
            created_at_str = created_at_str[:-1] + "+00:00"
        if updated_at_str.endswith("Z"):
            updated_at_str = updated_at_str[:-1] + "+00:00"

        # Remove sub-second precision beyond 6 digits if present
        # (Beads sometimes outputs nanoseconds which Python can't parse)
        import re

        created_at_str = re.sub(r"(\.\d{6})\d+", r"\1", created_at_str)
        updated_at_str = re.sub(r"(\.\d{6})\d+", r"\1", updated_at_str)

        created_at = datetime.fromisoformat(created_at_str)
        updated_at = datetime.fromisoformat(updated_at_str)

        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            status=IssueStatus(data["status"]),
            priority=data["priority"],
            issue_type=IssueType(data["issue_type"]),
            created_at=created_at,
            updated_at=updated_at,
            content_hash=data["content_hash"],
            source_repo=data.get("source_repo", "."),
            assignee=data.get("assignee"),
            labels=data.get("labels", []),
        )


# T097: Dependency dataclass
@dataclass
class Dependency:
    """Represents a relationship between two issues in the DAG.

    A dependency connects two issues where one (blocker) must be resolved
    before the other (blocked) can proceed.

    Attributes:
        blocked_id: ID of the issue that is blocked
        blocker_id: ID of the issue that blocks
        dependency_type: Nature of the relationship (blocks, related, etc.)

    Business Rules:
        - blocked_id and blocker_id must be different (no self-dependencies)
        - Dependencies persist even if issues are closed

    Example:
        >>> dep = Dependency(
        ...     blocked_id="issue-A",
        ...     blocker_id="issue-B",
        ...     dependency_type=DependencyType.BLOCKS
        ... )
    """

    blocked_id: str
    blocker_id: str
    dependency_type: DependencyType

    def __post_init__(self):
        """Validate dependency after initialization."""
        if self.blocked_id == self.blocker_id:
            raise ValueError("Issue cannot depend on itself")


# T098: DependencyTree dataclass
@dataclass
class DependencyTree:
    """Represents the full upstream and downstream dependency graph for an issue.

    Contains the transitive closure of all dependencies - both issues that
    block this one (upstream) and issues that this one blocks (downstream).

    Attributes:
        issue_id: Root issue for tree query
        blockers: Issues that block this issue (upstream dependencies)
        blocked_by: Issues blocked by this issue (downstream dependencies)

    Business Rules:
        - Tree query returns transitive closure (all ancestors and descendants)
        - Empty lists if no dependencies exist
        - Includes all dependency types (not filtered)

    Example:
        >>> tree = DependencyTree(
        ...     issue_id="issue-A",
        ...     blockers=["issue-B", "issue-C"],
        ...     blocked_by=["issue-D", "issue-E"]
        ... )
        >>> print(f"Issue {tree.issue_id} is blocked by {len(tree.blockers)} issues")
    """

    issue_id: str
    blockers: list[str]
    blocked_by: list[str]
