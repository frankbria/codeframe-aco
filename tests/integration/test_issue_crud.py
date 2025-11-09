"""Integration tests for issue CRUD operations with real Beads database."""

import subprocess
import time

import pytest

from beads.client import BeadsClient
from beads.exceptions import BeadsCommandError
from beads.models import IssueStatus, IssueType


@pytest.fixture
def beads_client_with_test_issues(test_beads_db, monkeypatch):
    """Create BeadsClient with pre-populated test issues."""
    # Change to test directory for the duration of the test
    monkeypatch.chdir(test_beads_db)

    # Create test issues directly via bd CLI (will use current directory)
    subprocess.run(
        ["bd", "create", "Test Issue 1", "--type", "task", "--priority", "2"],
        capture_output=True,
        check=True,
    )

    subprocess.run(
        ["bd", "create", "Test Issue 2", "--type", "feature", "--priority", "1"],
        capture_output=True,
        check=True,
    )

    subprocess.run(
        ["bd", "create", "Test Issue 3", "--type", "bug", "--priority", "0"],
        capture_output=True,
        check=True,
    )

    # Create client (will use current directory's .beads/)
    client = BeadsClient(sandbox=True)

    return client


# T054: Integration tests for status updates
class TestIssueStatusUpdates:
    """Integration tests for issue status update operations."""

    def test_update_issue_status_persists_to_database(self, beads_client_with_test_issues):
        """Test that status updates persist in Beads database."""
        client = beads_client_with_test_issues

        # Get first issue
        ready_issues = client.get_ready_issues()
        assert len(ready_issues) > 0

        issue_id = ready_issues[0].id

        # Update status to in_progress
        updated_issue = client.update_issue_status(issue_id, IssueStatus.IN_PROGRESS)

        # Verify update was successful
        assert updated_issue.status == IssueStatus.IN_PROGRESS

        # Verify persistence by querying again
        fetched_issue = client.get_issue(issue_id)
        assert fetched_issue.status == IssueStatus.IN_PROGRESS
        assert fetched_issue.id == issue_id

    def test_update_issue_priority_persists_to_database(self, beads_client_with_test_issues):
        """Test that priority updates persist in Beads database."""
        client = beads_client_with_test_issues

        # Get first issue
        ready_issues = client.get_ready_issues()
        issue_id = ready_issues[0].id

        # Update priority to 0 (critical)
        updated_issue = client.update_issue_priority(issue_id, 0)

        # Verify update
        assert updated_issue.priority == 0

        # Verify persistence
        fetched_issue = client.get_issue(issue_id)
        assert fetched_issue.priority == 0

    def test_close_issue_persists_to_database(self, beads_client_with_test_issues):
        """Test that closing an issue persists in Beads database."""
        client = beads_client_with_test_issues

        # Get first issue
        ready_issues = client.get_ready_issues()
        issue_id = ready_issues[0].id

        # Close the issue
        closed_issue = client.close_issue(issue_id)

        # Verify closure
        assert closed_issue.status == IssueStatus.CLOSED

        # Verify persistence
        fetched_issue = client.get_issue(issue_id)
        assert fetched_issue.status == IssueStatus.CLOSED

    def test_update_nonexistent_issue_raises_error(self, beads_client_with_test_issues):
        """Test that updating non-existent issue raises BeadsCommandError."""
        client = beads_client_with_test_issues

        with pytest.raises(BeadsCommandError):
            client.update_issue_status("nonexistent-issue-id", IssueStatus.IN_PROGRESS)

    def test_close_nonexistent_issue_raises_error(self, beads_client_with_test_issues):
        """Test that closing non-existent issue raises BeadsCommandError."""
        client = beads_client_with_test_issues

        with pytest.raises(BeadsCommandError):
            client.close_issue("nonexistent-issue-id")


# T055: Test scenario - Open → in_progress → appears in bd list --status in_progress
class TestStatusTransitionScenarios:
    """Integration tests for specific status transition scenarios."""

    def test_open_to_in_progress_appears_in_status_list(self, beads_client_with_test_issues):
        """Test Open → in_progress → appears in bd list --status in_progress."""
        client = beads_client_with_test_issues

        # Get an open issue
        ready_issues = client.get_ready_issues()
        assert len(ready_issues) > 0

        issue_id = ready_issues[0].id
        assert ready_issues[0].status == IssueStatus.OPEN

        # Update to in_progress
        updated_issue = client.update_issue_status(issue_id, IssueStatus.IN_PROGRESS)
        assert updated_issue.status == IssueStatus.IN_PROGRESS

        # Verify it appears in bd list --status in_progress
        # Use subprocess to verify against actual bd CLI output
        result = subprocess.run(
            ["bd", "--json", "list", "--status", "in_progress"],
            capture_output=True,
            text=True,
            check=True,
        )

        import json

        in_progress_issues = json.loads(result.stdout)

        # Find our issue in the list
        found = False
        for issue_data in in_progress_issues:
            if issue_data["id"] == issue_id:
                found = True
                assert issue_data["status"] == "in_progress"
                break

        assert found, f"Issue {issue_id} not found in bd list --status in_progress"

    # T056: Test scenario - In_progress → closed → no longer in bd ready
    def test_in_progress_to_closed_removed_from_ready(self, beads_client_with_test_issues):
        """Test In_progress → closed → no longer in bd ready."""
        client = beads_client_with_test_issues

        # Get an issue and set it to in_progress
        ready_issues = client.get_ready_issues()
        issue_id = ready_issues[0].id

        client.update_issue_status(issue_id, IssueStatus.IN_PROGRESS)

        # Verify it's still in ready list (in_progress issues can be ready)
        # Actually, in_progress issues are NOT in bd ready - only open/blocked
        # Let's verify the correct behavior

        # Close the issue
        closed_issue = client.close_issue(issue_id)
        assert closed_issue.status == IssueStatus.CLOSED

        # Verify it's no longer in ready list
        ready_after_close = client.get_ready_issues()
        ready_ids = {issue.id for issue in ready_after_close}

        assert issue_id not in ready_ids, f"Closed issue {issue_id} should not be in bd ready"

    # T057: Test scenario - Multiple updates in sequence → current status reflects latest
    def test_multiple_updates_current_status_reflects_latest(self, beads_client_with_test_issues):
        """Test Multiple updates in sequence → current status reflects latest."""
        client = beads_client_with_test_issues

        # Get an issue
        ready_issues = client.get_ready_issues()
        issue_id = ready_issues[0].id

        # Perform multiple status updates
        client.update_issue_status(issue_id, IssueStatus.IN_PROGRESS)
        client.update_issue_status(issue_id, IssueStatus.BLOCKED)
        client.update_issue_status(issue_id, IssueStatus.IN_PROGRESS)
        final_update = client.update_issue_status(issue_id, IssueStatus.CLOSED)

        # Verify final status is closed
        assert final_update.status == IssueStatus.CLOSED

        # Verify persistence
        fetched_issue = client.get_issue(issue_id)
        assert fetched_issue.status == IssueStatus.CLOSED

    def test_multiple_priority_updates_current_reflects_latest(self, beads_client_with_test_issues):
        """Test multiple priority updates - current priority reflects latest."""
        client = beads_client_with_test_issues

        # Get an issue
        ready_issues = client.get_ready_issues()
        issue_id = ready_issues[0].id

        # Perform multiple priority updates
        client.update_issue_priority(issue_id, 0)
        client.update_issue_priority(issue_id, 2)
        client.update_issue_priority(issue_id, 4)
        final_update = client.update_issue_priority(issue_id, 1)

        # Verify final priority is 1
        assert final_update.priority == 1

        # Verify persistence
        fetched_issue = client.get_issue(issue_id)
        assert fetched_issue.priority == 1

    def test_combined_status_and_priority_updates(self, beads_client_with_test_issues):
        """Test updating both status and priority in sequence."""
        client = beads_client_with_test_issues

        # Get an issue
        ready_issues = client.get_ready_issues()
        issue_id = ready_issues[0].id

        # Update status
        client.update_issue_status(issue_id, IssueStatus.IN_PROGRESS)

        # Update priority
        client.update_issue_priority(issue_id, 0)

        # Update status again
        final_update = client.update_issue_status(issue_id, IssueStatus.CLOSED)

        # Verify both fields
        assert final_update.status == IssueStatus.CLOSED
        assert final_update.priority == 0

        # Verify persistence
        fetched_issue = client.get_issue(issue_id)
        assert fetched_issue.status == IssueStatus.CLOSED
        assert fetched_issue.priority == 0


# Performance tests
class TestStatusUpdatePerformance:
    """Performance tests for status update operations."""

    def test_update_status_completes_quickly(self, beads_client_with_test_issues):
        """Test that status update completes in < 100ms."""
        client = beads_client_with_test_issues

        # Get an issue
        ready_issues = client.get_ready_issues()
        issue_id = ready_issues[0].id

        # Time the status update
        start = time.perf_counter()
        client.update_issue_status(issue_id, IssueStatus.IN_PROGRESS)
        duration = time.perf_counter() - start

        # Should complete in < 100ms (0.1 seconds)
        assert duration < 0.1, f"Status update took {duration*1000:.1f}ms (expected < 100ms)"

    def test_update_priority_completes_quickly(self, beads_client_with_test_issues):
        """Test that priority update completes in < 100ms."""
        client = beads_client_with_test_issues

        # Get an issue
        ready_issues = client.get_ready_issues()
        issue_id = ready_issues[0].id

        # Time the priority update
        start = time.perf_counter()
        client.update_issue_priority(issue_id, 0)
        duration = time.perf_counter() - start

        # Should complete in < 100ms (0.1 seconds)
        assert duration < 0.1, f"Priority update took {duration*1000:.1f}ms (expected < 100ms)"

    def test_close_issue_completes_quickly(self, beads_client_with_test_issues):
        """Test that close_issue completes in < 100ms."""
        client = beads_client_with_test_issues

        # Get an issue
        ready_issues = client.get_ready_issues()
        issue_id = ready_issues[0].id

        # Time the close operation
        start = time.perf_counter()
        client.close_issue(issue_id)
        duration = time.perf_counter() - start

        # Should complete in < 100ms (0.1 seconds)
        assert duration < 0.1, f"Close issue took {duration*1000:.1f}ms (expected < 100ms)"


# T082: Integration tests for create_issue()
class TestIssueCreation:
    """Integration tests for issue creation operations."""

    def test_create_issue_persists_to_database(self, test_beads_db, monkeypatch):
        """Test T083: Create issue with title, type, priority → appears in Beads."""
        monkeypatch.chdir(test_beads_db)
        client = BeadsClient(sandbox=True)

        # Create a new issue
        new_issue = client.create_issue(
            title="Integration Test Issue",
            description="This is a test issue created via Python API",
            issue_type=IssueType.FEATURE,
            priority=1,
        )

        # Verify the issue was created
        assert new_issue.id is not None
        assert new_issue.title == "Integration Test Issue"
        assert new_issue.description == "This is a test issue created via Python API"
        assert new_issue.issue_type == IssueType.FEATURE
        assert new_issue.priority == 1
        assert new_issue.status == IssueStatus.OPEN

        # Verify persistence by fetching the issue
        fetched_issue = client.get_issue(new_issue.id)
        assert fetched_issue.id == new_issue.id
        assert fetched_issue.title == new_issue.title
        assert fetched_issue.description == new_issue.description

    def test_create_issue_with_all_optional_fields(self, test_beads_db, monkeypatch):
        """Test T086: Create with description and assignee → fields persisted."""
        monkeypatch.chdir(test_beads_db)
        client = BeadsClient(sandbox=True)

        # Create issue with all optional fields
        new_issue = client.create_issue(
            title="Fully Configured Issue",
            description="Issue with all optional fields set",
            issue_type=IssueType.BUG,
            priority=0,
            assignee="testuser",
            labels=["urgent", "backend", "security"],
        )

        # Verify basic fields were set (note: bd create doesn't return labels in JSON)
        assert new_issue.title == "Fully Configured Issue"
        assert new_issue.description == "Issue with all optional fields set"
        assert new_issue.issue_type == IssueType.BUG
        assert new_issue.priority == 0
        assert new_issue.assignee == "testuser"

        # Verify persistence by fetching the issue (bd show returns full details including labels)
        fetched_issue = client.get_issue(new_issue.id)
        assert fetched_issue.assignee == "testuser"
        assert set(fetched_issue.labels or []) == {"urgent", "backend", "security"}

    def test_created_issue_appears_in_ready_list(self, test_beads_db, monkeypatch):
        """Test T093: Verify created issues appear in subsequent queries."""
        monkeypatch.chdir(test_beads_db)
        client = BeadsClient(sandbox=True)

        # Create a new issue
        new_issue = client.create_issue(
            title="Ready Issue Test",
            description="Should appear in ready list",
            issue_type=IssueType.TASK,
            priority=2,
        )

        # Verify it appears in ready issues
        ready_issues = client.get_ready_issues()
        ready_ids = {issue.id for issue in ready_issues}

        assert (
            new_issue.id in ready_ids
        ), f"Newly created issue {new_issue.id} should appear in ready list"

    def test_created_issue_appears_in_list_queries(self, test_beads_db, monkeypatch):
        """Test that created issues appear in various list queries."""
        monkeypatch.chdir(test_beads_db)
        client = BeadsClient(sandbox=True)

        # Create a bug with priority 0
        new_bug = client.create_issue(
            title="Critical Bug",
            description="High priority bug",
            issue_type=IssueType.BUG,
            priority=0,
        )

        # Verify it appears in list queries
        all_bugs = client.list_issues(issue_type=IssueType.BUG)
        bug_ids = {issue.id for issue in all_bugs}
        assert new_bug.id in bug_ids

        critical_issues = client.list_issues(priority=0)
        critical_ids = {issue.id for issue in critical_issues}
        assert new_bug.id in critical_ids

        open_issues = client.list_issues(status=IssueStatus.OPEN)
        open_ids = {issue.id for issue in open_issues}
        assert new_bug.id in open_ids

    def test_create_multiple_issues_sequentially(self, test_beads_db, monkeypatch):
        """Test creating multiple issues in sequence."""
        monkeypatch.chdir(test_beads_db)
        client = BeadsClient(sandbox=True)

        # Create two issues (reduced from 3 to avoid timeout)
        issue1 = client.create_issue(
            title="Issue 1", description="First issue", issue_type=IssueType.FEATURE, priority=1
        )

        issue2 = client.create_issue(
            title="Issue 2", description="Second issue", issue_type=IssueType.BUG, priority=0
        )

        # Verify both issues were created with unique IDs
        assert issue1.id != issue2.id

        # Verify both can be fetched
        fetched1 = client.get_issue(issue1.id)
        fetched2 = client.get_issue(issue2.id)

        assert fetched1.title == "Issue 1"
        assert fetched2.title == "Issue 2"

    def test_create_issue_verifies_via_bd_cli(self, test_beads_db, monkeypatch):
        """Test that created issues are visible via direct bd CLI query."""
        monkeypatch.chdir(test_beads_db)
        client = BeadsClient(sandbox=True)

        # Create an issue via Python API
        new_issue = client.create_issue(
            title="CLI Verification Test",
            description="Should be visible via bd CLI",
            issue_type=IssueType.TASK,
            priority=3,
        )

        # Verify via direct bd CLI call
        result = subprocess.run(
            ["bd", "--json", "show", new_issue.id], capture_output=True, text=True, check=True
        )

        import json

        cli_result = json.loads(result.stdout)

        # bd show returns a list with one element
        issue_data = cli_result[0] if isinstance(cli_result, list) else cli_result

        assert issue_data["id"] == new_issue.id
        assert issue_data["title"] == "CLI Verification Test"
        assert issue_data["issue_type"] == "task"
        assert issue_data["priority"] == 3
