"""Integration tests for issue CRUD operations with real Beads database."""

import pytest
import subprocess
import time
import os
from pathlib import Path

from beads.client import BeadsClient
from beads.models import IssueStatus, IssueType
from beads.exceptions import BeadsCommandError


@pytest.fixture
def beads_client_with_test_issues(test_beads_db, monkeypatch):
    """Create BeadsClient with pre-populated test issues."""
    # Change to test directory for the duration of the test
    monkeypatch.chdir(test_beads_db)

    # Create test issues directly via bd CLI (will use current directory)
    subprocess.run(
        ['bd', 'create', 'Test Issue 1', '--type', 'task', '--priority', '2'],
        capture_output=True,
        check=True
    )

    subprocess.run(
        ['bd', 'create', 'Test Issue 2', '--type', 'feature', '--priority', '1'],
        capture_output=True,
        check=True
    )

    subprocess.run(
        ['bd', 'create', 'Test Issue 3', '--type', 'bug', '--priority', '0'],
        capture_output=True,
        check=True
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
        original_status = ready_issues[0].status

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
            ['bd', '--json', 'list', '--status', 'in_progress'],
            capture_output=True,
            text=True,
            check=True
        )

        import json
        in_progress_issues = json.loads(result.stdout)

        # Find our issue in the list
        found = False
        for issue_data in in_progress_issues:
            if issue_data['id'] == issue_id:
                found = True
                assert issue_data['status'] == 'in_progress'
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
