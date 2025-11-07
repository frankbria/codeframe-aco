"""
BeadsClient API Contract

This file defines the public interface for the Beads Integration Layer.
It serves as the contract specification for implementation and testing.

All methods are documented with:
- Purpose and usage
- Parameters with types and validation
- Return types
- Exceptions that may be raised
- Example usage
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


# ============================================================================
# Enumerations
# ============================================================================

class IssueStatus(str, Enum):
    """Valid workflow states for issues."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    CLOSED = "closed"


class IssueType(str, Enum):
    """Categories of work tracked in Beads."""
    BUG = "bug"
    FEATURE = "feature"
    TASK = "task"
    EPIC = "epic"
    CHORE = "chore"


class DependencyType(str, Enum):
    """Types of relationships between issues."""
    BLOCKS = "blocks"
    RELATED = "related"
    PARENT_CHILD = "parent-child"
    DISCOVERED_FROM = "discovered-from"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Issue:
    """Represents a single unit of work in the Beads DAG."""
    id: str
    title: str
    description: str
    status: IssueStatus
    priority: int  # 0-4: 0=critical, 4=backlog
    issue_type: IssueType
    created_at: datetime
    updated_at: datetime
    content_hash: str
    source_repo: str
    assignee: Optional[str] = None
    labels: Optional[List[str]] = None

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'Issue':
        """
        Parse Issue from Beads JSON output.

        Args:
            data: JSON dict from bd command output

        Returns:
            Issue instance

        Raises:
            ValueError: If required fields missing or invalid
        """
        pass


@dataclass
class Dependency:
    """Represents a relationship between two issues."""
    blocked_id: str
    blocker_id: str
    dependency_type: DependencyType


@dataclass
class DependencyTree:
    """Full upstream and downstream dependency graph for an issue."""
    issue_id: str
    blockers: List[str]  # Issues that block this issue
    blocked_by: List[str]  # Issues blocked by this issue


# ============================================================================
# Exceptions
# ============================================================================

class BeadsError(Exception):
    """Base exception for all Beads operations."""
    pass


class BeadsCommandError(BeadsError):
    """CLI command failed (non-zero exit code)."""
    def __init__(self, command: str, returncode: int, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"Command '{command}' failed with code {returncode}: {stderr}")


class BeadsJSONParseError(BeadsError):
    """Failed to parse JSON output from bd command."""
    pass


class BeadsIssueNotFoundError(BeadsError):
    """Issue ID does not exist."""
    def __init__(self, issue_id: str):
        self.issue_id = issue_id
        super().__init__(f"Issue '{issue_id}' not found")


class BeadsDependencyCycleError(BeadsError):
    """Circular dependency detected."""
    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
        super().__init__(f"Circular dependency: {' → '.join(cycle_path)}")


# ============================================================================
# BeadsClient Interface
# ============================================================================

class BeadsClientInterface(ABC):
    """
    Abstract interface for Beads issue tracker operations.

    This defines the contract that all implementations must fulfill.
    Implementations wrap the `bd` CLI tool with a Python interface.
    """

    # ------------------------------------------------------------------------
    # Query Operations (Read)
    # ------------------------------------------------------------------------

    @abstractmethod
    def get_ready_issues(
        self,
        limit: Optional[int] = None,
        priority: Optional[int] = None,
        issue_type: Optional[IssueType] = None
    ) -> List[Issue]:
        """
        Get issues that are ready to work on (no blocking dependencies).

        Wraps: bd ready --json

        Args:
            limit: Maximum number of issues to return (default: 10)
            priority: Filter by specific priority level (0-4)
            issue_type: Filter by issue type

        Returns:
            List of Issue objects with no blockers

        Raises:
            BeadsCommandError: If bd command fails
            BeadsJSONParseError: If JSON output invalid

        Example:
            >>> client = BeadsClient()
            >>> ready = client.get_ready_issues(limit=5, priority=0)
            >>> for issue in ready:
            ...     print(f"{issue.id}: {issue.title}")
        """
        pass

    @abstractmethod
    def get_issue(self, issue_id: str) -> Issue:
        """
        Get detailed information about a specific issue.

        Wraps: bd show <issue_id> --json

        Args:
            issue_id: Unique issue identifier

        Returns:
            Issue object with all fields populated

        Raises:
            BeadsIssueNotFoundError: If issue ID doesn't exist
            BeadsCommandError: If bd command fails
            BeadsJSONParseError: If JSON output invalid

        Example:
            >>> issue = client.get_issue("codeframe-aco-xon")
            >>> print(f"Status: {issue.status}")
        """
        pass

    @abstractmethod
    def list_issues(
        self,
        status: Optional[IssueStatus] = None,
        priority: Optional[int] = None,
        issue_type: Optional[IssueType] = None,
        limit: Optional[int] = None
    ) -> List[Issue]:
        """
        List issues with optional filtering.

        Wraps: bd list --json

        Args:
            status: Filter by status (open, in_progress, closed, blocked)
            priority: Filter by priority level (0-4)
            issue_type: Filter by type (bug, feature, task, epic, chore)
            limit: Maximum number of issues to return

        Returns:
            List of Issue objects matching filters

        Raises:
            BeadsCommandError: If bd command fails
            BeadsJSONParseError: If JSON output invalid

        Example:
            >>> open_bugs = client.list_issues(
            ...     status=IssueStatus.OPEN,
            ...     issue_type=IssueType.BUG
            ... )
        """
        pass

    # ------------------------------------------------------------------------
    # Issue Operations (Create, Update, Delete)
    # ------------------------------------------------------------------------

    @abstractmethod
    def create_issue(
        self,
        title: str,
        issue_type: IssueType,
        priority: int = 2,
        description: str = "",
        assignee: Optional[str] = None
    ) -> str:
        """
        Create a new issue.

        Wraps: bd create <title> --type <type> --priority <priority>

        Args:
            title: Issue title (max 500 chars)
            issue_type: Category of work
            priority: Priority level 0-4 (default: 2=medium)
            description: Detailed description (optional)
            assignee: Username to assign (optional)

        Returns:
            Newly created issue ID

        Raises:
            ValueError: If title empty or priority out of range
            BeadsCommandError: If bd command fails

        Example:
            >>> issue_id = client.create_issue(
            ...     title="Fix login bug",
            ...     issue_type=IssueType.BUG,
            ...     priority=0
            ... )
            >>> print(f"Created: {issue_id}")
        """
        pass

    @abstractmethod
    def update_issue_status(self, issue_id: str, status: IssueStatus) -> None:
        """
        Update the status of an issue.

        Wraps: bd update <issue_id> --status <status>

        Args:
            issue_id: Issue to update
            status: New status value

        Raises:
            BeadsIssueNotFoundError: If issue doesn't exist
            BeadsCommandError: If bd command fails

        Example:
            >>> client.update_issue_status(
            ...     "codeframe-aco-xon",
            ...     IssueStatus.IN_PROGRESS
            ... )
        """
        pass

    @abstractmethod
    def update_issue_priority(self, issue_id: str, priority: int) -> None:
        """
        Update the priority of an issue.

        Wraps: bd update <issue_id> --priority <priority>

        Args:
            issue_id: Issue to update
            priority: New priority (0-4)

        Raises:
            ValueError: If priority out of range
            BeadsIssueNotFoundError: If issue doesn't exist
            BeadsCommandError: If bd command fails

        Example:
            >>> client.update_issue_priority("codeframe-aco-xon", 0)
        """
        pass

    @abstractmethod
    def close_issue(self, issue_id: str) -> None:
        """
        Close an issue.

        Wraps: bd close <issue_id>

        Args:
            issue_id: Issue to close

        Raises:
            BeadsIssueNotFoundError: If issue doesn't exist
            BeadsCommandError: If bd command fails

        Example:
            >>> client.close_issue("codeframe-aco-xon")
        """
        pass

    # ------------------------------------------------------------------------
    # Dependency Operations
    # ------------------------------------------------------------------------

    @abstractmethod
    def add_dependency(
        self,
        blocked_id: str,
        blocker_id: str,
        dep_type: DependencyType = DependencyType.BLOCKS
    ) -> None:
        """
        Add a dependency between two issues.

        Wraps: bd dep add <blocked> <blocker> --type <type>

        Args:
            blocked_id: Issue that will be blocked
            blocker_id: Issue that blocks
            dep_type: Type of dependency (default: blocks)

        Raises:
            ValueError: If blocked_id == blocker_id (self-dependency)
            BeadsIssueNotFoundError: If either issue doesn't exist
            BeadsDependencyCycleError: If dependency creates cycle
            BeadsCommandError: If bd command fails

        Example:
            >>> client.add_dependency(
            ...     blocked_id="codeframe-aco-p1a",
            ...     blocker_id="codeframe-aco-xon",
            ...     dep_type=DependencyType.BLOCKS
            ... )
        """
        pass

    @abstractmethod
    def remove_dependency(self, blocked_id: str, blocker_id: str) -> None:
        """
        Remove a dependency between two issues.

        Wraps: bd dep remove <blocked> <blocker>

        Args:
            blocked_id: Blocked issue
            blocker_id: Blocker issue

        Raises:
            BeadsCommandError: If bd command fails

        Note: Removing non-existent dependency is idempotent (no error)

        Example:
            >>> client.remove_dependency(
            ...     "codeframe-aco-p1a",
            ...     "codeframe-aco-xon"
            ... )
        """
        pass

    @abstractmethod
    def get_dependency_tree(self, issue_id: str) -> DependencyTree:
        """
        Get full dependency tree for an issue.

        Wraps: bd dep tree <issue_id> --json

        Args:
            issue_id: Root issue to query

        Returns:
            DependencyTree with upstream blockers and downstream blocked issues

        Raises:
            BeadsIssueNotFoundError: If issue doesn't exist
            BeadsCommandError: If bd command fails
            BeadsJSONParseError: If JSON output invalid

        Example:
            >>> tree = client.get_dependency_tree("codeframe-aco-p1a")
            >>> print(f"Blocked by: {tree.blockers}")
            >>> print(f"Blocks: {tree.blocked_by}")
        """
        pass

    @abstractmethod
    def detect_dependency_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies in the entire DAG.

        Wraps: bd dep cycles --json

        Returns:
            List of cycle paths, where each path is a list of issue IDs.
            Empty list if no cycles exist.

        Raises:
            BeadsCommandError: If bd command fails
            BeadsJSONParseError: If JSON output invalid

        Example:
            >>> cycles = client.detect_dependency_cycles()
            >>> if cycles:
            ...     print(f"WARNING: {len(cycles)} cycles detected!")
            ...     for cycle in cycles:
            ...         print(" → ".join(cycle))
        """
        pass


# ============================================================================
# Factory Function
# ============================================================================

def create_beads_client(
    db_path: Optional[str] = None,
    timeout: int = 30,
    sandbox: bool = False
) -> BeadsClientInterface:
    """
    Factory function to create BeadsClient instance.

    Args:
        db_path: Path to .beads/ directory (default: auto-discover)
        timeout: Subprocess timeout in seconds (default: 30)
        sandbox: Enable sandbox mode (disable daemon/auto-sync) for testing

    Returns:
        BeadsClientInterface implementation

    Example:
        >>> # Production usage (auto-discover .beads/ directory)
        >>> client = create_beads_client()

        >>> # Test usage with isolated database
        >>> client = create_beads_client(
        ...     db_path="/tmp/test-beads",
        ...     sandbox=True
        ... )
    """
    pass
