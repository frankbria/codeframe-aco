"""BeadsClient main interface for Beads Integration Layer."""

from pathlib import Path

from beads.exceptions import BeadsDependencyCycleError
from beads.models import Dependency, DependencyTree, DependencyType, Issue, IssueStatus, IssueType
from beads.utils import _run_bd_command


def _find_beads_directory(start_path: Path | None = None) -> Path | None:
    """Find .beads/ directory by searching current and parent directories.

    Args:
        start_path: Directory to start search from (defaults to current directory)

    Returns:
        Path to .beads/ directory if found, None otherwise

    Example:
        >>> beads_dir = _find_beads_directory()
        >>> if beads_dir:
        ...     print(f"Found .beads at: {beads_dir}")
    """
    current = start_path or Path.cwd()

    # Search up to root directory
    while True:
        beads_dir = current / ".beads"
        if beads_dir.is_dir():
            return beads_dir

        # Check if we've reached the root
        parent = current.parent
        if parent == current:
            return None

        current = parent


class BeadsClient:
    """Main interface for programmatic Beads operations.

    Provides high-level methods for querying issues, managing
    dependencies, and synchronizing state with Beads CLI.

    Example:
        >>> client = BeadsClient()
        >>> ready = client.get_ready_issues(limit=5)
        >>> for issue in ready:
        ...     print(f"{issue.id}: {issue.title}")
    """

    def __init__(self, db_path: str | None = None, timeout: int = 30, sandbox: bool = False):
        """Initialize BeadsClient.

        Args:
            db_path: Path to .beads/ directory (auto-discovered if None)
            timeout: Timeout for bd commands in seconds
            sandbox: If True, disable daemon and Git sync for testing
        """
        self.db_path = db_path
        self.timeout = timeout
        self.sandbox = sandbox

    # T043: Core get_ready_issues implementation
    def get_ready_issues(
        self,
        limit: int | None = None,
        priority: int | None = None,
        issue_type: IssueType | None = None,
    ) -> list[Issue]:
        """Query unblocked issues ready for work.

        Returns issues that have no blocking dependencies and are
        in open or blocked status. Agents can select from these
        issues for autonomous work assignment.

        Args:
            limit: Maximum number of issues to return
            priority: Filter by priority (0-4)
            issue_type: Filter by issue type

        Returns:
            List of Issue objects representing ready work

        Raises:
            BeadsCommandError: If bd ready command fails
            BeadsJSONParseError: If output cannot be parsed
            ValueError: If priority is out of range (0-4)

        Example:
            >>> client = BeadsClient()
            >>> critical = client.get_ready_issues(priority=0, limit=3)
            >>> next_task = min(critical, key=lambda i: i.priority)
        """
        # Build command arguments
        args = ["ready"]

        # T044: Add filters
        if limit is not None:
            args.extend(["--limit", str(limit)])

        if priority is not None:
            if not (0 <= priority <= 4):
                raise ValueError("Priority must be 0-4")
            args.extend(["--priority", str(priority)])

        if issue_type is not None:
            args.extend(["--type", issue_type.value])

        # Execute bd ready command
        # T045: Error handling
        result = _run_bd_command(args, timeout=self.timeout)

        # Parse JSON result into Issue objects
        if not result:
            return []

        # Result should be a list of issue dicts
        issues = []
        for issue_data in result:
            issue = Issue.from_json(issue_data)
            issues.append(issue)

        return issues

    def get_issue(self, issue_id: str) -> Issue:
        """Retrieve a single issue by ID.

        Args:
            issue_id: The unique identifier for the issue

        Returns:
            Issue object with full details

        Raises:
            ValueError: If issue_id is empty
            BeadsCommandError: If issue not found or command fails
            BeadsJSONParseError: If output cannot be parsed

        Example:
            >>> client = BeadsClient()
            >>> issue = client.get_issue("codeframe-aco-abc")
            >>> print(f"{issue.title}: {issue.status}")
        """
        if not issue_id:
            raise ValueError("Issue ID cannot be empty")

        args = ["show", issue_id]
        result = _run_bd_command(args, timeout=self.timeout)

        # bd show returns a list with a single issue dict
        if isinstance(result, list) and len(result) > 0:
            return Issue.from_json(result[0])
        elif isinstance(result, dict):
            return Issue.from_json(result)
        else:
            raise ValueError(f"Unexpected result format from bd show: {type(result)}")

    def update_issue(
        self,
        issue_id: str,
        status: IssueStatus | None = None,
        priority: int | None = None,
        assignee: str | None = None,
        labels: list[str] | None = None,
    ) -> Issue:
        """Update an existing issue's fields.

        Args:
            issue_id: The unique identifier for the issue
            status: New status for the issue
            priority: New priority (0-4)
            assignee: New assignee username
            labels: New list of labels

        Returns:
            Updated Issue object

        Raises:
            ValueError: If no fields provided or invalid values
            BeadsCommandError: If update fails

        Example:
            >>> client = BeadsClient()
            >>> issue = client.update_issue(
            ...     "test-abc",
            ...     status=IssueStatus.IN_PROGRESS,
            ...     priority=0
            ... )
        """
        if not any([status, priority is not None, assignee, labels is not None]):
            raise ValueError("At least one field must be provided for update")

        if priority is not None and not (0 <= priority <= 4):
            raise ValueError("Priority must be 0-4")

        args = ["update", issue_id]

        if status is not None:
            args.extend(["--status", status.value])

        if priority is not None:
            args.extend(["--priority", str(priority)])

        if assignee is not None:
            args.extend(["--assignee", assignee])

        if labels is not None:
            # Join labels with commas or add multiple --label flags
            for label in labels:
                args.extend(["--label", label])

        result = _run_bd_command(args, timeout=self.timeout)

        # bd update returns a list with the updated issue dict
        if isinstance(result, list) and len(result) > 0:
            return Issue.from_json(result[0])
        elif isinstance(result, dict):
            return Issue.from_json(result)
        else:
            raise ValueError(f"Unexpected result format from bd update: {type(result)}")

    def create_issue(
        self,
        title: str,
        description: str,
        issue_type: IssueType,
        priority: int = 2,
        assignee: str | None = None,
        labels: list[str] | None = None,
    ) -> Issue:
        """Create a new issue in Beads.

        Args:
            title: Issue title (non-empty)
            description: Issue description
            issue_type: Type of issue (bug, feature, task, etc.)
            priority: Priority level (0-4, default: 2)
            assignee: Username to assign issue to
            labels: List of label strings

        Returns:
            Newly created Issue object

        Raises:
            ValueError: If title is empty or priority invalid
            BeadsCommandError: If creation fails

        Example:
            >>> client = BeadsClient()
            >>> issue = client.create_issue(
            ...     title="Fix authentication bug",
            ...     description="Users cannot log in",
            ...     issue_type=IssueType.BUG,
            ...     priority=0
            ... )
        """
        if not title:
            raise ValueError("Title cannot be empty")

        if not (0 <= priority <= 4):
            raise ValueError("Priority must be 0-4")

        args = ["create", title]

        if description:
            args.extend(["--description", description])

        args.extend(["--type", issue_type.value])
        args.extend(["--priority", str(priority)])

        if assignee:
            args.extend(["--assignee", assignee])

        if labels:
            for label in labels:
                args.extend(["--label", label])

        result = _run_bd_command(args, timeout=self.timeout)

        # bd create returns a list with the newly created issue dict
        if isinstance(result, list) and len(result) > 0:
            return Issue.from_json(result[0])
        elif isinstance(result, dict):
            return Issue.from_json(result)
        else:
            raise ValueError(f"Unexpected result format from bd create: {type(result)}")

    # T058: Convenience method for updating issue status
    def update_issue_status(self, issue_id: str, status: IssueStatus) -> Issue:
        """Update an issue's status.

        Convenience method that wraps update_issue() for status-only updates.

        Args:
            issue_id: The unique identifier for the issue
            status: New status for the issue

        Returns:
            Updated Issue object

        Raises:
            ValueError: If issue_id is empty
            BeadsCommandError: If update fails or issue not found

        Example:
            >>> client = BeadsClient()
            >>> issue = client.update_issue_status(
            ...     "test-abc",
            ...     IssueStatus.IN_PROGRESS
            ... )
        """
        if not issue_id:
            raise ValueError("Issue ID cannot be empty")

        return self.update_issue(issue_id, status=status)

    # T059: Convenience method for updating issue priority
    def update_issue_priority(self, issue_id: str, priority: int) -> Issue:
        """Update an issue's priority.

        Convenience method that wraps update_issue() for priority-only updates.

        Args:
            issue_id: The unique identifier for the issue
            priority: New priority (0-4)

        Returns:
            Updated Issue object

        Raises:
            ValueError: If issue_id is empty or priority out of range
            BeadsCommandError: If update fails or issue not found

        Example:
            >>> client = BeadsClient()
            >>> issue = client.update_issue_priority("test-abc", 0)
        """
        if not issue_id:
            raise ValueError("Issue ID cannot be empty")

        # Validation happens in update_issue
        return self.update_issue(issue_id, priority=priority)

    # T060: Convenience method for closing issues
    def close_issue(self, issue_id: str) -> Issue:
        """Close an issue by setting its status to closed.

        Convenience method that wraps update_issue_status() for closing issues.

        Args:
            issue_id: The unique identifier for the issue

        Returns:
            Updated Issue object with status=CLOSED

        Raises:
            ValueError: If issue_id is empty
            BeadsCommandError: If update fails or issue not found

        Example:
            >>> client = BeadsClient()
            >>> issue = client.close_issue("test-abc")
            >>> assert issue.status == IssueStatus.CLOSED
        """
        if not issue_id:
            raise ValueError("Issue ID cannot be empty")

        return self.update_issue_status(issue_id, IssueStatus.CLOSED)

    # T075-T076: List issues with filtering support
    def list_issues(
        self,
        status: IssueStatus | None = None,
        priority: int | None = None,
        issue_type: IssueType | None = None,
        assignee: str | None = None,
        limit: int | None = None,
    ) -> list[Issue]:
        """List issues with optional filtering.

        Query all issues or filter by status, priority, type, or assignee.
        Supports combining multiple filters for precise queries.

        Args:
            status: Filter by issue status (open, in_progress, blocked, closed)
            priority: Filter by priority (0-4)
            issue_type: Filter by issue type (bug, feature, task, epic, chore)
            assignee: Filter by assignee username
            limit: Maximum number of issues to return

        Returns:
            List of Issue objects matching the filters

        Raises:
            ValueError: If priority is out of range (0-4)
            BeadsCommandError: If bd list command fails

        Example:
            >>> client = BeadsClient()
            >>> # Get all open bugs
            >>> bugs = client.list_issues(
            ...     status=IssueStatus.OPEN,
            ...     issue_type=IssueType.BUG
            ... )
            >>> # Get top 5 critical issues
            >>> critical = client.list_issues(priority=0, limit=5)
        """
        # Build command arguments
        args = ["list"]

        # Add filters
        if status is not None:
            args.extend(["--status", status.value])

        if priority is not None:
            if not (0 <= priority <= 4):
                raise ValueError("Priority must be 0-4")
            args.extend(["--priority", str(priority)])

        if issue_type is not None:
            args.extend(["--type", issue_type.value])

        if assignee is not None:
            args.extend(["--assignee", assignee])

        if limit is not None:
            args.extend(["--limit", str(limit)])

        # Execute bd list command
        result = _run_bd_command(args, timeout=self.timeout)

        # Parse JSON result into Issue objects
        if not result:
            return []

        # Result should be a list of issue dicts
        issues = []
        for issue_data in result:
            issue = Issue.from_json(issue_data)
            issues.append(issue)

        return issues

    # T109: Dependency management - add_dependency()
    def add_dependency(
        self, blocked_id: str, blocker_id: str, dep_type: DependencyType = DependencyType.BLOCKS
    ) -> Dependency:
        """Add a dependency between two issues.

        Creates a relationship where blocker_id must complete before
        blocked_id can proceed. Supports all 4 dependency types.

        Args:
            blocked_id: ID of the issue that is blocked
            blocker_id: ID of the issue that blocks
            dep_type: Type of dependency (blocks, related, parent-child, discovered-from)

        Returns:
            Dependency object representing the created relationship

        Raises:
            ValueError: If blocked_id equals blocker_id (self-dependency)
            BeadsDependencyCycleError: If adding this dependency would create a cycle
            BeadsCommandError: If bd dep add fails

        Example:
            >>> client = BeadsClient()
            >>> dep = client.add_dependency(
            ...     blocked_id="issue-A",
            ...     blocker_id="issue-B",
            ...     dep_type=DependencyType.BLOCKS
            ... )
        """
        # T110: Validate no self-dependencies
        if blocked_id == blocker_id:
            raise ValueError("Issue cannot depend on itself")

        # bd dep add <blocked> <blocker> --type <type>
        args = ["dep", "add", blocked_id, blocker_id, "--type", dep_type.value]

        try:
            _run_bd_command(args, timeout=self.timeout)
        except Exception as e:
            # Check if error is due to cycle creation
            error_msg = str(e).lower()
            if "cycle" in error_msg or "circular" in error_msg:
                raise BeadsDependencyCycleError(
                    message="Adding dependency would create a cycle",
                    cycle_path=[blocked_id, blocker_id, blocked_id],
                ) from e
            raise

        # Return Dependency object
        return Dependency(blocked_id=blocked_id, blocker_id=blocker_id, dependency_type=dep_type)

    # T111: Dependency management - remove_dependency()
    def remove_dependency(self, blocked_id: str, blocker_id: str) -> None:
        """Remove a dependency between two issues.

        Idempotent operation - removing a non-existent dependency does not error.

        Args:
            blocked_id: ID of the blocked issue
            blocker_id: ID of the blocker issue

        Raises:
            BeadsCommandError: If bd dep remove fails for reasons other than non-existence

        Example:
            >>> client = BeadsClient()
            >>> client.remove_dependency("issue-A", "issue-B")
        """
        # bd dep remove <blocked> <blocker>
        args = ["dep", "remove", blocked_id, blocker_id]

        try:
            _run_bd_command(args, timeout=self.timeout)
        except Exception as e:
            # Idempotent: ignore if dependency doesn't exist
            error_msg = str(e).lower()
            if "not found" in error_msg or "does not exist" in error_msg:
                return
            raise

    # T112: Dependency management - get_dependency_tree()
    def get_dependency_tree(self, issue_id: str) -> DependencyTree:
        """Get the full dependency tree for an issue.

        Returns both upstream (blockers) and downstream (blocked by) dependencies
        as a transitive closure.

        Args:
            issue_id: ID of the issue to query

        Returns:
            DependencyTree with all upstream and downstream dependencies

        Raises:
            BeadsCommandError: If bd dep tree fails

        Example:
            >>> client = BeadsClient()
            >>> tree = client.get_dependency_tree("issue-A")
            >>> print(f"Blocked by {len(tree.blockers)} issues")
        """
        # bd dep tree <issue_id> returns flat list with depth information
        args = ["dep", "tree", issue_id]
        result = _run_bd_command(args, timeout=self.timeout)

        if not result:
            # No dependencies
            return DependencyTree(issue_id=issue_id, blockers=[], blocked_by=[])

        # Parse tree structure
        # depth=0 is the root issue
        # depth>0 are dependencies (blockers of root)
        blockers = []
        for item in result:
            if item["id"] != issue_id and item.get("depth", 0) > 0:
                blockers.append(item["id"])

        # For blocked_by, we need to check what this issue blocks
        # This would require a separate query or parsing logic
        # For now, return empty list (to be enhanced)
        blocked_by = []

        return DependencyTree(issue_id=issue_id, blockers=blockers, blocked_by=blocked_by)

    # T113-T114: Dependency management - detect_dependency_cycles()
    def detect_dependency_cycles(self) -> list[list[str]]:
        """Detect circular dependencies in the entire DAG.

        Returns all cycles found in the dependency graph. Each cycle is
        represented as a list of issue IDs forming the cycle.

        Returns:
            List of cycles, where each cycle is a list of issue IDs.
            Empty list if no cycles exist.

        Raises:
            BeadsCommandError: If bd dep cycles fails

        Example:
            >>> client = BeadsClient()
            >>> cycles = client.detect_dependency_cycles()
            >>> if cycles:
            ...     print(f"Found {len(cycles)} cycles!")
            ...     for cycle in cycles:
            ...         print(" → ".join(cycle))
        """
        # bd dep cycles returns JSON array of cycles
        args = ["dep", "cycles"]
        result = _run_bd_command(args, timeout=self.timeout)

        if not result:
            return []

        # Result is a list of cycle paths
        # Each cycle is a list of issue IDs
        cycles = []
        for cycle_data in result:
            if isinstance(cycle_data, list):
                cycles.append(cycle_data)
            elif isinstance(cycle_data, dict) and "path" in cycle_data:
                cycles.append(cycle_data["path"])

        return cycles


def create_beads_client(
    db_path: str | None = None, timeout: int = 30, sandbox: bool = False
) -> BeadsClient:
    """Factory function to create a BeadsClient instance.

    If db_path is not provided, automatically searches for .beads/ directory
    in current and parent directories.

    Args:
        db_path: Path to .beads/ directory (auto-discovered if None)
        timeout: Timeout for bd commands in seconds
        sandbox: If True, disable daemon and Git sync for testing

    Returns:
        BeadsClient instance

    Example:
        >>> # Auto-discover .beads/ directory
        >>> client = create_beads_client(timeout=60)
        >>> issues = client.get_ready_issues()
        >>>
        >>> # Explicitly specify path
        >>> client = create_beads_client(db_path="/path/to/.beads")
    """
    # Auto-discover .beads/ directory if not provided
    resolved_db_path = db_path
    if db_path is None:
        beads_dir = _find_beads_directory()
        if beads_dir:
            resolved_db_path = str(beads_dir)

    return BeadsClient(db_path=resolved_db_path, timeout=timeout, sandbox=sandbox)
