# Phase 3 Implementation Handoff

**Branch**: `002-beads-integration`
**Feature**: Beads Integration Layer
**Current Status**: Phase 3 (User Story 1) - 40% Complete
**Last Updated**: 2025-11-07

---

## What's Been Completed (T033-T037) ✅

### Issue Dataclass Implementation

**Files Modified**:
- `src/beads/models.py` - Added Issue dataclass (+122 lines)
- `tests/unit/test_models.py` - Added 13 tests (+279 lines)
- `specs/002-beads-integration/tasks.md` - Marked T033-T037 complete

**Functionality Delivered**:

1. **Issue Dataclass** (T035):
   - Complete dataclass matching Beads JSON schema
   - All required fields: id, title, description, status, priority, issue_type, timestamps, hashes
   - Optional fields: assignee, labels
   - Validation in `__post_init__`:
     - Empty ID → ValueError
     - Empty title → ValueError
     - Priority out of range (0-4) → ValueError

2. **Issue.from_json() Parser** (T036):
   - Robust datetime parsing handling:
     - RFC3339 format with 'Z' suffix
     - Timezone offsets (e.g., -07:00)
     - Nanosecond precision (truncates to microseconds)
   - Enum conversion for status and issue_type
   - Optional field handling

3. **Test Coverage** (T033-T034):
   - 7 tests for dataclass validation
   - 6 tests for from_json() parsing
   - All 13 tests passing
   - 95% coverage of models.py

**Test Results**:
```
tests/unit/test_models.py::TestIssueDataclass - 7/7 PASSED
tests/unit/test_models.py::TestIssueFromJson - 6/6 PASSED
```

---

## What Needs to Be Done Next (T038-T050) 🔄

### Immediate Next Steps

#### 1. BeadsClient Unit Tests (T038-T042)

**File**: `tests/unit/test_client.py`

Create comprehensive tests for `BeadsClient.get_ready_issues()`:

```python
# T038: Mock-based unit tests
class TestBeadsClientGetReadyIssues:
    """Test BeadsClient.get_ready_issues() with mocked subprocess."""

    @patch("beads.utils._run_bd_command")
    def test_get_ready_issues_returns_issue_list(self, mock_run):
        """Test that get_ready_issues returns list of Issue objects."""
        # Mock bd ready --json output
        mock_run.return_value = [
            {
                "id": "test-abc",
                "title": "Test Issue",
                "status": "open",
                "priority": 1,
                "issue_type": "feature",
                # ... other required fields
            }
        ]

        client = BeadsClient()
        issues = client.get_ready_issues()

        assert len(issues) == 1
        assert isinstance(issues[0], Issue)
        assert issues[0].id == "test-abc"
        mock_run.assert_called_once_with(["ready"])

    @patch("beads.utils._run_bd_command")
    def test_get_ready_issues_with_limit(self, mock_run):
        """Test limit parameter."""
        mock_run.return_value = []
        client = BeadsClient()
        client.get_ready_issues(limit=5)

        # Verify --limit flag passed to bd command
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "--limit" in args
        assert "5" in args

    @patch("beads.utils._run_bd_command")
    def test_get_ready_issues_with_priority_filter(self, mock_run):
        """Test priority parameter."""
        mock_run.return_value = []
        client = BeadsClient()
        client.get_ready_issues(priority=0)

        # Verify --priority flag passed
        args = mock_run.call_args[0][0]
        assert "--priority" in args
        assert "0" in args

    @patch("beads.utils._run_bd_command")
    def test_get_ready_issues_with_type_filter(self, mock_run):
        """Test issue_type parameter."""
        mock_run.return_value = []
        client = BeadsClient()
        client.get_ready_issues(issue_type=IssueType.BUG)

        args = mock_run.call_args[0][0]
        assert "--type" in args
        assert "bug" in args

    @patch("beads.utils._run_bd_command")
    def test_get_ready_issues_empty_list(self, mock_run):
        """Test that empty result returns empty list."""
        mock_run.return_value = []

        client = BeadsClient()
        issues = client.get_ready_issues()

        assert issues == []
```

#### 2. BeadsClient Integration Tests (T039-T042)

**File**: `tests/integration/test_queries.py`

Create tests using real bd CLI:

```python
# T039: Integration tests with real .beads/ database
class TestGetReadyIssuesIntegration:
    """Test get_ready_issues() against real Beads database."""

    def test_get_ready_issues_basic(self, test_beads_db, test_issues):
        """Test basic ready issues query."""
        from beads.client import BeadsClient

        # test_issues fixture creates sample issues
        client = BeadsClient(db_path=str(test_beads_db / '.beads'))
        issues = client.get_ready_issues()

        assert isinstance(issues, list)
        assert all(isinstance(issue, Issue) for issue in issues)
        # All returned issues should have no blockers
        for issue in issues:
            # Verify issue is actually ready (would need dep check)
            assert issue.status in [IssueStatus.OPEN, IssueStatus.BLOCKED]

    # T040: Scenario test
    def test_ready_issues_with_dependencies(self, test_beads_db):
        """Test: Issue A has no deps, B blocks C → returns A and B."""
        import subprocess

        # Create issue A (no dependencies)
        result = subprocess.run(
            ['bd', 'create', 'Issue A', '--priority', '0'],
            cwd=test_beads_db, capture_output=True, text=True
        )
        issue_a_id = extract_issue_id(result.stdout)

        # Create issue B (blocker)
        result = subprocess.run(
            ['bd', 'create', 'Issue B', '--priority', '1'],
            cwd=test_beads_db, capture_output=True, text=True
        )
        issue_b_id = extract_issue_id(result.stdout)

        # Create issue C (blocked by B)
        result = subprocess.run(
            ['bd', 'create', 'Issue C', '--priority', '2'],
            cwd=test_beads_db, capture_output=True, text=True
        )
        issue_c_id = extract_issue_id(result.stdout)

        # Add dependency: C depends on B
        subprocess.run(
            ['bd', 'dep', 'add', issue_c_id, issue_b_id, '--type', 'blocks'],
            cwd=test_beads_db, check=True
        )

        # Query ready issues
        client = BeadsClient(db_path=str(test_beads_db / '.beads'))
        ready = client.get_ready_issues()

        ready_ids = {issue.id for issue in ready}
        assert issue_a_id in ready_ids  # A has no deps
        assert issue_b_id in ready_ids  # B is a blocker
        assert issue_c_id not in ready_ids  # C is blocked

    # T041: All blocked scenario
    def test_all_issues_blocked(self, test_beads_db):
        """Test: All issues blocked → returns empty list."""
        # Create circular dependency or all-blocked scenario
        # Verify get_ready_issues() returns []

    # T042: Transition scenario
    def test_issue_transitions_to_ready(self, test_beads_db):
        """Test: Issue transitions from blocked to ready."""
        # Create blocked issue, remove blocker, verify appears in ready
```

#### 3. BeadsClient Implementation (T043-T045)

**File**: `src/beads/client.py`

Replace stub with full implementation:

```python
"""BeadsClient main interface for Beads Integration Layer."""

from typing import List, Optional
from beads.models import Issue, IssueType
from beads.utils import _run_bd_command


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

    def __init__(
        self,
        db_path: Optional[str] = None,
        timeout: int = 30,
        sandbox: bool = False
    ):
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
        limit: Optional[int] = None,
        priority: Optional[int] = None,
        issue_type: Optional[IssueType] = None
    ) -> List[Issue]:
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

        Example:
            >>> client = BeadsClient()
            >>> critical = client.get_ready_issues(priority=0, limit=3)
            >>> next_task = min(critical, key=lambda i: i.priority)
        """
        # Build command arguments
        args = ['ready']

        # T044: Add filters
        if limit is not None:
            args.extend(['--limit', str(limit)])

        if priority is not None:
            if not (0 <= priority <= 4):
                raise ValueError("Priority must be 0-4")
            args.extend(['--priority', str(priority)])

        if issue_type is not None:
            args.extend(['--type', issue_type.value])

        # Execute bd ready command
        # T045: Error handling
        try:
            result = _run_bd_command(args, timeout=self.timeout)
        except Exception as e:
            # Re-raise with context
            raise

        # Parse JSON result into Issue objects
        if not result:
            return []

        # Result should be a list of issue dicts
        issues = []
        for issue_data in result:
            issue = Issue.from_json(issue_data)
            issues.append(issue)

        return issues


def create_beads_client(
    db_path: Optional[str] = None,
    timeout: int = 30,
    sandbox: bool = False
) -> BeadsClient:
    """Factory function to create a BeadsClient instance.

    Args:
        db_path: Path to .beads/ directory (auto-discovered if None)
        timeout: Timeout for bd commands in seconds
        sandbox: If True, disable daemon and Git sync for testing

    Returns:
        BeadsClient instance
    """
    return BeadsClient(db_path=db_path, timeout=timeout, sandbox=sandbox)
```

#### 4. Final Validation (T046-T050)

- **T046**: Run all Phase 3 tests together
- **T047**: Run integration tests with real Beads database
- **T048**: Performance test: 100-issue query < 500ms
- **T049**: Update `src/beads/__init__.py` exports:
  ```python
  from beads.models import Issue, IssueStatus, IssueType, DependencyType
  from beads.client import BeadsClient, create_beads_client

  __all__ = [
      'Issue', 'IssueStatus', 'IssueType', 'DependencyType',
      'BeadsClient', 'create_beads_client'
  ]
  ```
- **T050**: Create `examples/select_task.py` demonstrating autonomous work selection

---

## Quick Start Command for Next Session

```bash
# Switch to correct branch
git checkout 002-beads-integration

# Activate virtual environment
source .venv/bin/activate

# Verify current state
python -m pytest tests/unit/test_models.py::TestIssueDataclass -v
python -m pytest tests/unit/test_models.py::TestIssueFromJson -v

# Start with BeadsClient tests
# Create tests/unit/test_client.py following examples above
```

---

## Context for Next AI Agent

**Task**: Complete Phase 3 (User Story 1 - Query Ready Issues)

**What to do**:
1. Read this handoff document
2. Implement T038-T042 (BeadsClient tests)
3. Implement T043-T045 (BeadsClient.get_ready_issues())
4. Complete T046-T050 (validation, exports, examples)

**Key files to create/modify**:
- `tests/unit/test_client.py` - BeadsClient unit tests
- `tests/integration/test_queries.py` - Integration tests
- `src/beads/client.py` - Full BeadsClient implementation
- `src/beads/__init__.py` - Update exports
- `examples/select_task.py` - Example usage

**Success criteria**:
- All T038-T050 tests passing
- Coverage ≥ 80%
- Performance: 100-issue query < 500ms
- Example script demonstrates work selection

**Starter prompt**:
```
Continue Phase 3 implementation for feature 002-beads-integration.
I've completed T033-T037 (Issue dataclass). Please implement
T038-T050 following the plan in PHASE3_HANDOFF.md. Start by
creating comprehensive tests for BeadsClient.get_ready_issues()
in tests/unit/test_client.py.
```

---

## Technical Notes

### DateTime Parsing Gotchas
The Issue.from_json() implementation handles:
- RFC3339 'Z' suffix → converts to '+00:00'
- Nanosecond precision → truncates to 6 digits
- Multiple timezone formats

### Test Fixtures Available
From `tests/conftest.py`:
- `test_beads_db` - Isolated .beads/ database in tmp directory
- `beads_client` - BeadsClient instance pointing to test DB
- `test_issues` - Pre-created sample issues

### CLI Command Reference
```bash
bd ready --json                  # Get all ready issues
bd ready --json --limit 5        # Limit results
bd ready --json --priority 0     # Filter by priority
bd ready --json --type bug       # Filter by type
```

---

## Questions or Issues?

If you encounter problems:
1. Check test output for specific failures
2. Verify bd CLI is installed: `which bd`
3. Review research.md for implementation decisions
4. Check data-model.md for Issue schema details

**Architecture decisions**: See `specs/002-beads-integration/research.md`
**Data models**: See `specs/002-beads-integration/data-model.md`
**Full task list**: See `specs/002-beads-integration/tasks.md`
