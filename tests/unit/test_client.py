"""Unit tests for BeadsClient methods with mocked subprocess calls."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from beads.models import Issue, IssueStatus, IssueType
from beads.client import BeadsClient, create_beads_client
from beads.exceptions import BeadsCommandError, BeadsJSONParseError


# Sample issue data for mocking
SAMPLE_ISSUE_JSON = {
    "id": "test-abc123",
    "title": "Test Issue",
    "description": "Test description",
    "status": "open",
    "priority": 1,
    "issue_type": "feature",
    "created_at": "2025-11-07T10:00:00Z",
    "updated_at": "2025-11-07T10:00:00Z",
    "content_hash": "abc123def456",
    "source_repo": "/home/user/project",
    "assignee": None,
    "labels": []
}


# T038: Mock-based unit tests for BeadsClient.get_ready_issues()
class TestBeadsClientGetReadyIssues:
    """Test BeadsClient.get_ready_issues() with mocked subprocess."""

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_returns_issue_list(self, mock_run):
        """Test that get_ready_issues returns list of Issue objects."""
        # Mock bd ready --json output
        mock_run.return_value = [SAMPLE_ISSUE_JSON]

        client = BeadsClient()
        issues = client.get_ready_issues()

        assert len(issues) == 1
        assert isinstance(issues[0], Issue)
        assert issues[0].id == "test-abc123"
        assert issues[0].title == "Test Issue"
        assert issues[0].status == IssueStatus.OPEN
        assert issues[0].priority == 1
        assert issues[0].issue_type == IssueType.FEATURE
        mock_run.assert_called_once_with(["ready"], timeout=30)

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_multiple_issues(self, mock_run):
        """Test that get_ready_issues handles multiple issues correctly."""
        # Mock multiple issues
        issue_1 = SAMPLE_ISSUE_JSON.copy()
        issue_2 = {
            **SAMPLE_ISSUE_JSON,
            "id": "test-def456",
            "title": "Second Issue",
            "priority": 0,
            "issue_type": "bug"
        }
        issue_3 = {
            **SAMPLE_ISSUE_JSON,
            "id": "test-ghi789",
            "title": "Third Issue",
            "priority": 2,
            "issue_type": "task"
        }
        mock_run.return_value = [issue_1, issue_2, issue_3]

        client = BeadsClient()
        issues = client.get_ready_issues()

        assert len(issues) == 3
        assert all(isinstance(issue, Issue) for issue in issues)
        assert issues[0].id == "test-abc123"
        assert issues[1].id == "test-def456"
        assert issues[2].id == "test-ghi789"

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_with_limit(self, mock_run):
        """Test limit parameter is passed correctly."""
        mock_run.return_value = []

        client = BeadsClient()
        client.get_ready_issues(limit=5)

        # Verify --limit flag passed to bd command
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ready" in args
        assert "--limit" in args
        assert "5" in args

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_with_priority_filter(self, mock_run):
        """Test priority parameter is passed correctly."""
        mock_run.return_value = []

        client = BeadsClient()
        client.get_ready_issues(priority=0)

        # Verify --priority flag passed
        args = mock_run.call_args[0][0]
        assert "ready" in args
        assert "--priority" in args
        assert "0" in args

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_with_type_filter(self, mock_run):
        """Test issue_type parameter is passed correctly."""
        mock_run.return_value = []

        client = BeadsClient()
        client.get_ready_issues(issue_type=IssueType.BUG)

        args = mock_run.call_args[0][0]
        assert "ready" in args
        assert "--type" in args
        assert "bug" in args

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_with_all_filters(self, mock_run):
        """Test combining multiple filters."""
        mock_run.return_value = []

        client = BeadsClient()
        client.get_ready_issues(limit=10, priority=1, issue_type=IssueType.FEATURE)

        args = mock_run.call_args[0][0]
        assert "ready" in args
        assert "--limit" in args
        assert "10" in args
        assert "--priority" in args
        assert "1" in args
        assert "--type" in args
        assert "feature" in args

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_empty_list(self, mock_run):
        """Test that empty result returns empty list."""
        mock_run.return_value = []

        client = BeadsClient()
        issues = client.get_ready_issues()

        assert issues == []

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_invalid_priority_raises_error(self, mock_run):
        """Test that invalid priority raises ValueError."""
        client = BeadsClient()

        with pytest.raises(ValueError, match="Priority must be 0-4"):
            client.get_ready_issues(priority=5)

        with pytest.raises(ValueError, match="Priority must be 0-4"):
            client.get_ready_issues(priority=-1)

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_command_error_propagates(self, mock_run):
        """Test that BeadsCommandError is propagated."""
        mock_run.side_effect = BeadsCommandError(
            message="Command failed",
            command=["bd", "--json", "ready"],
            returncode=1,
            stderr="Error message"
        )

        client = BeadsClient()

        with pytest.raises(BeadsCommandError):
            client.get_ready_issues()

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_respects_timeout(self, mock_run):
        """Test that custom timeout is passed to _run_bd_command."""
        mock_run.return_value = []

        client = BeadsClient(timeout=60)
        client.get_ready_issues()

        # Verify timeout was passed
        assert mock_run.call_args[1]["timeout"] == 60

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_with_assignee(self, mock_run):
        """Test parsing issues with assignee field."""
        issue_with_assignee = {
            **SAMPLE_ISSUE_JSON,
            "assignee": "john.doe"
        }
        mock_run.return_value = [issue_with_assignee]

        client = BeadsClient()
        issues = client.get_ready_issues()

        assert len(issues) == 1
        assert issues[0].assignee == "john.doe"

    @patch("beads.client._run_bd_command")
    def test_get_ready_issues_with_labels(self, mock_run):
        """Test parsing issues with labels."""
        issue_with_labels = {
            **SAMPLE_ISSUE_JSON,
            "labels": ["urgent", "backend", "api"]
        }
        mock_run.return_value = [issue_with_labels]

        client = BeadsClient()
        issues = client.get_ready_issues()

        assert len(issues) == 1
        assert issues[0].labels == ["urgent", "backend", "api"]


class TestBeadsClientGetIssue:
    """Test BeadsClient.get_issue() with mocked subprocess."""

    @patch("beads.client._run_bd_command")
    def test_get_issue_returns_issue_object(self, mock_run):
        """Test that get_issue returns a single Issue object."""
        # bd show returns a list with single issue
        mock_run.return_value = [SAMPLE_ISSUE_JSON]

        client = BeadsClient()
        issue = client.get_issue("test-abc123")

        assert isinstance(issue, Issue)
        assert issue.id == "test-abc123"
        assert issue.title == "Test Issue"
        mock_run.assert_called_once_with(["show", "test-abc123"], timeout=30)

    @patch("beads.client._run_bd_command")
    def test_get_issue_with_full_details(self, mock_run):
        """Test get_issue with all fields populated."""
        detailed_issue = {
            **SAMPLE_ISSUE_JSON,
            "assignee": "jane.smith",
            "labels": ["critical", "frontend"],
            "description": "Detailed description with multiple lines\nLine 2\nLine 3"
        }
        mock_run.return_value = [detailed_issue]

        client = BeadsClient()
        issue = client.get_issue("test-abc123")

        assert issue.assignee == "jane.smith"
        assert issue.labels == ["critical", "frontend"]
        assert "Line 2" in issue.description

    @patch("beads.client._run_bd_command")
    def test_get_issue_nonexistent_raises_error(self, mock_run):
        """Test that get_issue raises error for non-existent issue."""
        mock_run.side_effect = BeadsCommandError(
            message="Issue not found",
            command=["bd", "--json", "show", "nonexistent"],
            returncode=1,
            stderr="Issue 'nonexistent' not found"
        )

        client = BeadsClient()

        with pytest.raises(BeadsCommandError, match="Issue not found"):
            client.get_issue("nonexistent")

    @patch("beads.client._run_bd_command")
    def test_get_issue_empty_id_raises_error(self, mock_run):
        """Test that empty issue ID raises ValueError."""
        client = BeadsClient()

        with pytest.raises(ValueError, match="Issue ID cannot be empty"):
            client.get_issue("")

    @patch("beads.client._run_bd_command")
    def test_get_issue_handles_dict_response(self, mock_run):
        """Test get_issue handles dict response (backward compatibility)."""
        # Some bd versions might return dict instead of list
        mock_run.return_value = SAMPLE_ISSUE_JSON

        client = BeadsClient()
        issue = client.get_issue("test-abc123")

        assert isinstance(issue, Issue)
        assert issue.id == "test-abc123"

    @patch("beads.client._run_bd_command")
    def test_get_issue_invalid_response_raises_error(self, mock_run):
        """Test get_issue raises error on invalid response format."""
        mock_run.return_value = "invalid string response"

        client = BeadsClient()

        with pytest.raises(ValueError, match="Unexpected result format"):
            client.get_issue("test-abc123")


class TestBeadsClientUpdateIssue:
    """Test BeadsClient.update_issue() with mocked subprocess."""

    @patch("beads.client._run_bd_command")
    def test_update_issue_status(self, mock_run):
        """Test updating issue status."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "status": "in_progress"
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue("test-abc123", status=IssueStatus.IN_PROGRESS)

        assert isinstance(issue, Issue)
        assert issue.status == IssueStatus.IN_PROGRESS

        # Verify command was called correctly
        args = mock_run.call_args[0][0]
        assert "update" in args
        assert "test-abc123" in args
        assert "--status" in args
        assert "in_progress" in args

    @patch("beads.client._run_bd_command")
    def test_update_issue_priority(self, mock_run):
        """Test updating issue priority."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "priority": 0
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue("test-abc123", priority=0)

        assert issue.priority == 0

        args = mock_run.call_args[0][0]
        assert "update" in args
        assert "test-abc123" in args
        assert "--priority" in args
        assert "0" in args

    @patch("beads.client._run_bd_command")
    def test_update_issue_multiple_fields(self, mock_run):
        """Test updating multiple fields at once."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "status": "blocked",
            "priority": 0,
            "assignee": "team.lead"
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue(
            "test-abc123",
            status=IssueStatus.BLOCKED,
            priority=0,
            assignee="team.lead"
        )

        assert issue.status == IssueStatus.BLOCKED
        assert issue.priority == 0
        assert issue.assignee == "team.lead"

    @patch("beads.client._run_bd_command")
    def test_update_issue_invalid_priority_raises_error(self, mock_run):
        """Test that invalid priority raises ValueError."""
        client = BeadsClient()

        with pytest.raises(ValueError, match="Priority must be 0-4"):
            client.update_issue("test-abc123", priority=5)

    @patch("beads.client._run_bd_command")
    def test_update_issue_no_fields_raises_error(self, mock_run):
        """Test that update with no fields raises ValueError."""
        client = BeadsClient()

        with pytest.raises(ValueError, match="At least one field must be provided"):
            client.update_issue("test-abc123")

    @patch("beads.client._run_bd_command")
    def test_update_issue_handles_dict_response(self, mock_run):
        """Test update_issue handles dict response (backward compatibility)."""
        mock_run.return_value = SAMPLE_ISSUE_JSON

        client = BeadsClient()
        issue = client.update_issue("test-abc123", priority=1)

        assert isinstance(issue, Issue)

    @patch("beads.client._run_bd_command")
    def test_update_issue_invalid_response_raises_error(self, mock_run):
        """Test update_issue raises error on invalid response format."""
        mock_run.return_value = 123  # Invalid response type

        client = BeadsClient()

        with pytest.raises(ValueError, match="Unexpected result format"):
            client.update_issue("test-abc123", priority=1)


class TestBeadsClientCreateIssue:
    """Test BeadsClient.create_issue() with mocked subprocess."""

    @patch("beads.client._run_bd_command")
    def test_create_issue_basic(self, mock_run):
        """Test creating a basic issue."""
        mock_run.return_value = [SAMPLE_ISSUE_JSON]

        client = BeadsClient()
        issue = client.create_issue(
            title="Test Issue",
            description="Test description",
            issue_type=IssueType.FEATURE
        )

        assert isinstance(issue, Issue)
        assert issue.title == "Test Issue"
        assert issue.issue_type == IssueType.FEATURE

        args = mock_run.call_args[0][0]
        assert "create" in args
        assert "Test Issue" in args
        assert "--type" in args
        assert "feature" in args

    @patch("beads.client._run_bd_command")
    def test_create_issue_with_priority(self, mock_run):
        """Test creating issue with priority."""
        high_priority_issue = {
            **SAMPLE_ISSUE_JSON,
            "priority": 0
        }
        mock_run.return_value = [high_priority_issue]

        client = BeadsClient()
        issue = client.create_issue(
            title="Critical Bug",
            description="Urgent fix needed",
            issue_type=IssueType.BUG,
            priority=0
        )

        assert issue.priority == 0

        args = mock_run.call_args[0][0]
        assert "--priority" in args
        assert "0" in args

    @patch("beads.client._run_bd_command")
    def test_create_issue_with_labels(self, mock_run):
        """Test creating issue with labels."""
        labeled_issue = {
            **SAMPLE_ISSUE_JSON,
            "labels": ["urgent", "backend"]
        }
        mock_run.return_value = [labeled_issue]

        client = BeadsClient()
        issue = client.create_issue(
            title="Labeled Issue",
            description="Issue with labels",
            issue_type=IssueType.TASK,
            labels=["urgent", "backend"]
        )

        assert issue.labels == ["urgent", "backend"]

        args = mock_run.call_args[0][0]
        assert "--labels" in args or "--label" in args

    @patch("beads.client._run_bd_command")
    def test_create_issue_empty_title_raises_error(self, mock_run):
        """Test that empty title raises ValueError."""
        client = BeadsClient()

        with pytest.raises(ValueError, match="Title cannot be empty"):
            client.create_issue(
                title="",
                description="Description",
                issue_type=IssueType.TASK
            )

    @patch("beads.client._run_bd_command")
    def test_create_issue_invalid_priority_raises_error(self, mock_run):
        """Test that invalid priority raises ValueError."""
        client = BeadsClient()

        with pytest.raises(ValueError, match="Priority must be 0-4"):
            client.create_issue(
                title="Test",
                description="Test",
                issue_type=IssueType.TASK,
                priority=5
            )

    @patch("beads.client._run_bd_command")
    def test_create_issue_handles_dict_response(self, mock_run):
        """Test create_issue handles dict response (backward compatibility)."""
        mock_run.return_value = SAMPLE_ISSUE_JSON

        client = BeadsClient()
        issue = client.create_issue(
            title="Test",
            description="Test",
            issue_type=IssueType.TASK
        )

        assert isinstance(issue, Issue)

    @patch("beads.client._run_bd_command")
    def test_create_issue_invalid_response_raises_error(self, mock_run):
        """Test create_issue raises error on invalid response format."""
        mock_run.return_value = []  # Empty list

        client = BeadsClient()

        with pytest.raises(ValueError, match="Unexpected result format"):
            client.create_issue(
                title="Test",
                description="Test",
                issue_type=IssueType.TASK
            )


class TestBeadsClientFactory:
    """Test create_beads_client factory function."""

    def test_create_beads_client_default(self):
        """Test creating client with default parameters."""
        client = create_beads_client()

        assert isinstance(client, BeadsClient)
        assert client.db_path is None
        assert client.timeout == 30
        assert client.sandbox is False

    def test_create_beads_client_custom(self):
        """Test creating client with custom parameters."""
        client = create_beads_client(
            db_path="/custom/path/.beads",
            timeout=60,
            sandbox=True
        )

        assert client.db_path == "/custom/path/.beads"
        assert client.timeout == 60
        assert client.sandbox is True


class TestBeadsClientInit:
    """Test BeadsClient initialization."""

    def test_init_default_values(self):
        """Test BeadsClient initialization with defaults."""
        client = BeadsClient()

        assert client.db_path is None
        assert client.timeout == 30
        assert client.sandbox is False

    def test_init_custom_values(self):
        """Test BeadsClient initialization with custom values."""
        client = BeadsClient(
            db_path="/path/.beads",
            timeout=45,
            sandbox=True
        )

        assert client.db_path == "/path/.beads"
        assert client.timeout == 45
        assert client.sandbox is True


class TestBeadsClientEdgeCases:
    """Test edge cases and additional code paths."""

    @patch("beads.client._run_bd_command")
    def test_update_issue_with_all_fields(self, mock_run):
        """Test updating issue with all possible fields."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "status": "closed",
            "priority": 4,
            "assignee": "bot",
            "labels": ["automated", "test"]
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue(
            "test-abc123",
            status=IssueStatus.CLOSED,
            priority=4,
            assignee="bot",
            labels=["automated", "test"]
        )

        assert issue.status == IssueStatus.CLOSED
        assert issue.priority == 4
        assert issue.assignee == "bot"
        assert issue.labels == ["automated", "test"]

        # Verify all flags present
        args = mock_run.call_args[0][0]
        assert "--status" in args
        assert "--priority" in args
        assert "--assignee" in args
        assert "--label" in args

    @patch("beads.client._run_bd_command")
    def test_create_issue_with_empty_description(self, mock_run):
        """Test creating issue with empty description."""
        mock_run.return_value = [SAMPLE_ISSUE_JSON]

        client = BeadsClient()
        issue = client.create_issue(
            title="No Description",
            description="",
            issue_type=IssueType.TASK
        )

        assert isinstance(issue, Issue)
        # Description should not be passed in args if empty
        args = mock_run.call_args[0][0]
        # Empty description should still work

    @patch("beads.client._run_bd_command")
    def test_create_issue_all_optional_fields(self, mock_run):
        """Test creating issue with all optional fields."""
        full_issue = {
            **SAMPLE_ISSUE_JSON,
            "priority": 1,
            "assignee": "developer",
            "labels": ["v2", "backend"]
        }
        mock_run.return_value = [full_issue]

        client = BeadsClient()
        issue = client.create_issue(
            title="Full Issue",
            description="Complete description",
            issue_type=IssueType.FEATURE,
            priority=1,
            assignee="developer",
            labels=["v2", "backend"]
        )

        assert issue.priority == 1
        assert issue.assignee == "developer"
        assert issue.labels == ["v2", "backend"]

    @patch("beads.client._run_bd_command")
    def test_update_issue_with_empty_label_list(self, mock_run):
        """Test updating issue with empty labels list."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "labels": []
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue("test-abc123", labels=[])

        # Should not add any --label flags for empty list
        args = mock_run.call_args[0][0]
        # Labels parameter was provided but empty


# T051: Unit tests for update_issue_status()
class TestBeadsClientUpdateIssueStatus:
    """Test BeadsClient.update_issue_status() convenience method."""

    @patch("beads.client._run_bd_command")
    def test_update_issue_status_to_in_progress(self, mock_run):
        """Test updating issue status to in_progress."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "status": "in_progress"
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue_status("test-abc123", IssueStatus.IN_PROGRESS)

        assert isinstance(issue, Issue)
        assert issue.status == IssueStatus.IN_PROGRESS
        assert issue.id == "test-abc123"

        # Verify command was called correctly
        args = mock_run.call_args[0][0]
        assert "update" in args
        assert "test-abc123" in args
        assert "--status" in args
        assert "in_progress" in args

    @patch("beads.client._run_bd_command")
    def test_update_issue_status_to_closed(self, mock_run):
        """Test updating issue status to closed."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "status": "closed"
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue_status("test-abc123", IssueStatus.CLOSED)

        assert issue.status == IssueStatus.CLOSED

    @patch("beads.client._run_bd_command")
    def test_update_issue_status_to_blocked(self, mock_run):
        """Test updating issue status to blocked."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "status": "blocked"
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue_status("test-abc123", IssueStatus.BLOCKED)

        assert issue.status == IssueStatus.BLOCKED

    @patch("beads.client._run_bd_command")
    def test_update_issue_status_to_open(self, mock_run):
        """Test updating issue status to open."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "status": "open"
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue_status("test-abc123", IssueStatus.OPEN)

        assert issue.status == IssueStatus.OPEN

    @patch("beads.client._run_bd_command")
    def test_update_issue_status_empty_id_raises_error(self, mock_run):
        """Test that empty issue ID raises ValueError."""
        client = BeadsClient()

        with pytest.raises(ValueError, match="Issue ID cannot be empty"):
            client.update_issue_status("", IssueStatus.IN_PROGRESS)

    @patch("beads.client._run_bd_command")
    def test_update_issue_status_command_error_propagates(self, mock_run):
        """Test that BeadsCommandError is propagated."""
        mock_run.side_effect = BeadsCommandError(
            message="Issue not found",
            command=["bd", "--json", "update", "nonexistent", "--status", "in_progress"],
            returncode=1,
            stderr="Issue 'nonexistent' not found"
        )

        client = BeadsClient()

        with pytest.raises(BeadsCommandError, match="Issue not found"):
            client.update_issue_status("nonexistent", IssueStatus.IN_PROGRESS)


# T052: Unit tests for update_issue_priority()
class TestBeadsClientUpdateIssuePriority:
    """Test BeadsClient.update_issue_priority() convenience method."""

    @patch("beads.client._run_bd_command")
    def test_update_issue_priority_to_zero(self, mock_run):
        """Test updating issue priority to 0 (critical)."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "priority": 0
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue_priority("test-abc123", 0)

        assert isinstance(issue, Issue)
        assert issue.priority == 0
        assert issue.id == "test-abc123"

        # Verify command was called correctly
        args = mock_run.call_args[0][0]
        assert "update" in args
        assert "test-abc123" in args
        assert "--priority" in args
        assert "0" in args

    @patch("beads.client._run_bd_command")
    def test_update_issue_priority_to_four(self, mock_run):
        """Test updating issue priority to 4 (backlog)."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "priority": 4
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue_priority("test-abc123", 4)

        assert issue.priority == 4

    @patch("beads.client._run_bd_command")
    def test_update_issue_priority_to_two(self, mock_run):
        """Test updating issue priority to 2 (medium)."""
        updated_issue = {
            **SAMPLE_ISSUE_JSON,
            "priority": 2
        }
        mock_run.return_value = [updated_issue]

        client = BeadsClient()
        issue = client.update_issue_priority("test-abc123", 2)

        assert issue.priority == 2

    @patch("beads.client._run_bd_command")
    def test_update_issue_priority_invalid_high_raises_error(self, mock_run):
        """Test that priority > 4 raises ValueError."""
        client = BeadsClient()

        with pytest.raises(ValueError, match="Priority must be 0-4"):
            client.update_issue_priority("test-abc123", 5)

    @patch("beads.client._run_bd_command")
    def test_update_issue_priority_invalid_negative_raises_error(self, mock_run):
        """Test that priority < 0 raises ValueError."""
        client = BeadsClient()

        with pytest.raises(ValueError, match="Priority must be 0-4"):
            client.update_issue_priority("test-abc123", -1)

    @patch("beads.client._run_bd_command")
    def test_update_issue_priority_empty_id_raises_error(self, mock_run):
        """Test that empty issue ID raises ValueError."""
        client = BeadsClient()

        with pytest.raises(ValueError, match="Issue ID cannot be empty"):
            client.update_issue_priority("", 2)

    @patch("beads.client._run_bd_command")
    def test_update_issue_priority_command_error_propagates(self, mock_run):
        """Test that BeadsCommandError is propagated."""
        mock_run.side_effect = BeadsCommandError(
            message="Issue not found",
            command=["bd", "--json", "update", "nonexistent", "--priority", "2"],
            returncode=1,
            stderr="Issue 'nonexistent' not found"
        )

        client = BeadsClient()

        with pytest.raises(BeadsCommandError, match="Issue not found"):
            client.update_issue_priority("nonexistent", 2)


# T053: Unit tests for close_issue()
class TestBeadsClientCloseIssue:
    """Test BeadsClient.close_issue() convenience method."""

    @patch("beads.client._run_bd_command")
    def test_close_issue_success(self, mock_run):
        """Test closing an issue."""
        closed_issue = {
            **SAMPLE_ISSUE_JSON,
            "status": "closed"
        }
        mock_run.return_value = [closed_issue]

        client = BeadsClient()
        issue = client.close_issue("test-abc123")

        assert isinstance(issue, Issue)
        assert issue.status == IssueStatus.CLOSED
        assert issue.id == "test-abc123"

        # Verify command was called correctly
        args = mock_run.call_args[0][0]
        assert "update" in args
        assert "test-abc123" in args
        assert "--status" in args
        assert "closed" in args

    @patch("beads.client._run_bd_command")
    def test_close_issue_already_closed(self, mock_run):
        """Test closing an issue that is already closed (idempotent)."""
        closed_issue = {
            **SAMPLE_ISSUE_JSON,
            "status": "closed"
        }
        mock_run.return_value = [closed_issue]

        client = BeadsClient()
        issue = client.close_issue("test-abc123")

        # Should still work and return closed issue
        assert issue.status == IssueStatus.CLOSED

    @patch("beads.client._run_bd_command")
    def test_close_issue_from_in_progress(self, mock_run):
        """Test closing an issue that is in_progress."""
        closed_issue = {
            **SAMPLE_ISSUE_JSON,
            "status": "closed"
        }
        mock_run.return_value = [closed_issue]

        client = BeadsClient()
        issue = client.close_issue("test-abc123")

        assert issue.status == IssueStatus.CLOSED

    @patch("beads.client._run_bd_command")
    def test_close_issue_empty_id_raises_error(self, mock_run):
        """Test that empty issue ID raises ValueError."""
        client = BeadsClient()

        with pytest.raises(ValueError, match="Issue ID cannot be empty"):
            client.close_issue("")

    @patch("beads.client._run_bd_command")
    def test_close_issue_nonexistent_raises_error(self, mock_run):
        """Test that closing non-existent issue raises BeadsCommandError."""
        mock_run.side_effect = BeadsCommandError(
            message="Issue not found",
            command=["bd", "--json", "update", "nonexistent", "--status", "closed"],
            returncode=1,
            stderr="Issue 'nonexistent' not found"
        )

        client = BeadsClient()

        with pytest.raises(BeadsCommandError, match="Issue not found"):
            client.close_issue("nonexistent")

    @patch("beads.client._run_bd_command")
    def test_close_issue_respects_timeout(self, mock_run):
        """Test that custom timeout is passed to _run_bd_command."""
        closed_issue = {
            **SAMPLE_ISSUE_JSON,
            "status": "closed"
        }
        mock_run.return_value = [closed_issue]

        client = BeadsClient(timeout=60)
        client.close_issue("test-abc123")

        # Verify timeout was passed
        assert mock_run.call_args[1]["timeout"] == 60