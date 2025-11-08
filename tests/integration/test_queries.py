"""Integration tests for issue query operations (get_issue and list_issues)."""

import pytest
import subprocess
import time
from datetime import datetime
from pathlib import Path

from beads.client import BeadsClient
from beads.models import IssueStatus, IssueType
from beads.exceptions import BeadsCommandError


# T069: Integration tests for get_issue()
class TestGetIssueIntegration:
    """Integration tests for get_issue() method with real Beads database."""

    def test_get_issue_returns_complete_details(self, beads_client, test_beads_db, monkeypatch):
        """Test that get_issue returns all issue fields correctly."""
        monkeypatch.chdir(test_beads_db)

        # Create an issue with full details
        issue = beads_client.create_issue(
            title="Test Issue with Details",
            description="This is a detailed description",
            issue_type=IssueType.FEATURE,
            priority=0,
            assignee="test-user"
        )

        # Retrieve the issue
        retrieved = beads_client.get_issue(issue.id)

        # Verify all fields
        assert retrieved.id == issue.id
        assert retrieved.title == "Test Issue with Details"
        assert retrieved.description == "This is a detailed description"
        assert retrieved.status == IssueStatus.OPEN
        assert retrieved.priority == 0
        assert retrieved.issue_type == IssueType.FEATURE
        assert retrieved.assignee == "test-user"
        assert isinstance(retrieved.created_at, datetime)
        assert isinstance(retrieved.updated_at, datetime)

    def test_get_issue_nonexistent_raises_error(self, beads_client, test_beads_db, monkeypatch):
        """Test that getting non-existent issue raises BeadsCommandError."""
        monkeypatch.chdir(test_beads_db)

        with pytest.raises(BeadsCommandError):
            beads_client.get_issue("nonexistent-issue-id-12345")

    def test_get_issue_performance(self, beads_client, test_beads_db, monkeypatch):
        """Test that get_issue completes in < 100ms (SC-001)."""
        monkeypatch.chdir(test_beads_db)

        # Create an issue
        issue = beads_client.create_issue(
            title="Performance Test Issue",
            description="Testing get_issue performance",
            issue_type=IssueType.TASK,
            priority=2
        )

        # Time the get operation
        start = time.perf_counter()
        retrieved = beads_client.get_issue(issue.id)
        duration = time.perf_counter() - start

        # Should complete in < 100ms
        assert duration < 0.1, f"get_issue took {duration*1000:.1f}ms (expected < 100ms)"
        assert retrieved.id == issue.id


# T070: Integration tests for list_issues() filters
class TestListIssuesIntegration:
    """Integration tests for list_issues() method with various filters."""

    @pytest.fixture
    def populated_db(self, test_beads_db, monkeypatch):
        """Create a database populated with diverse issues."""
        monkeypatch.chdir(test_beads_db)
        client = BeadsClient(sandbox=True)

        # Create issues with different attributes
        issues = []

        # P0 feature
        issues.append(client.create_issue(
            title="Critical Feature",
            description="High priority feature",
            issue_type=IssueType.FEATURE,
            priority=0,
            assignee="alice"
        ))

        # P2 bug
        issues.append(client.create_issue(
            title="Medium Bug",
            description="Medium priority bug",
            issue_type=IssueType.BUG,
            priority=2,
            assignee="bob"
        ))

        # P1 task
        issues.append(client.create_issue(
            title="High Priority Task",
            description="Important task",
            issue_type=IssueType.TASK,
            priority=1,
            assignee="alice"
        ))

        # P3 chore
        issues.append(client.create_issue(
            title="Low Priority Chore",
            description="Maintenance work",
            issue_type=IssueType.CHORE,
            priority=3
        ))

        # Update one to in_progress
        client.update_issue_status(issues[1].id, IssueStatus.IN_PROGRESS)

        # Close one
        client.close_issue(issues[3].id)

        return client, issues

    def test_list_issues_no_filter_returns_all(self, populated_db):
        """Test that list_issues with no filters returns all issues."""
        client, created_issues = populated_db

        all_issues = client.list_issues()

        # Should have at least the 4 we created (might have more from fixture)
        created_ids = {issue.id for issue in created_issues}
        retrieved_ids = {issue.id for issue in all_issues}

        assert created_ids.issubset(retrieved_ids)

    def test_list_issues_filter_by_status(self, populated_db):
        """Test filtering issues by status."""
        client, created_issues = populated_db

        # Get open issues
        open_issues = client.list_issues(status=IssueStatus.OPEN)
        assert len(open_issues) >= 2  # At least 2 open issues

        # Get in_progress issues
        in_progress = client.list_issues(status=IssueStatus.IN_PROGRESS)
        assert any(i.id == created_issues[1].id for i in in_progress)

        # Get closed issues
        closed = client.list_issues(status=IssueStatus.CLOSED)
        assert any(i.id == created_issues[3].id for i in closed)

    def test_list_issues_filter_by_priority(self, populated_db):
        """Test filtering issues by priority."""
        client, created_issues = populated_db

        # Get P0 issues
        p0_issues = client.list_issues(priority=0)
        assert any(i.id == created_issues[0].id for i in p0_issues)
        assert all(i.priority == 0 for i in p0_issues)

        # Get P2 issues
        p2_issues = client.list_issues(priority=2)
        assert any(i.id == created_issues[1].id for i in p2_issues)

    def test_list_issues_filter_by_type(self, populated_db):
        """Test filtering issues by issue type."""
        client, created_issues = populated_db

        # Get bugs
        bugs = client.list_issues(issue_type=IssueType.BUG)
        assert any(i.id == created_issues[1].id for i in bugs)
        assert all(i.issue_type == IssueType.BUG for i in bugs)

        # Get features
        features = client.list_issues(issue_type=IssueType.FEATURE)
        assert any(i.id == created_issues[0].id for i in features)

    def test_list_issues_filter_by_assignee(self, populated_db):
        """Test filtering issues by assignee."""
        client, created_issues = populated_db

        # Get alice's issues
        alice_issues = client.list_issues(assignee="alice")
        assert len(alice_issues) >= 2
        assert all(i.assignee == "alice" for i in alice_issues)

        # Get bob's issues
        bob_issues = client.list_issues(assignee="bob")
        assert any(i.id == created_issues[1].id for i in bob_issues)

    # T071: Test scenario - Issue with priority P0, type "feature"
    def test_issue_with_p0_feature_type(self, populated_db):
        """Test scenario: Issue with priority P0, type 'feature' → all fields correct."""
        client, created_issues = populated_db

        # Query for P0 features
        p0_features = client.list_issues(priority=0, issue_type=IssueType.FEATURE)

        # Find our specific issue
        our_issue = next((i for i in p0_features if i.id == created_issues[0].id), None)
        assert our_issue is not None

        # Verify all fields are correct
        assert our_issue.priority == 0
        assert our_issue.issue_type == IssueType.FEATURE
        assert our_issue.title == "Critical Feature"
        assert our_issue.description == "High priority feature"
        assert our_issue.assignee == "alice"
        assert our_issue.status == IssueStatus.OPEN

    # T078: Multiple filter combinations
    def test_list_issues_combined_filters(self, populated_db):
        """Test combining multiple filters."""
        client, created_issues = populated_db

        # Open issues assigned to alice
        alice_open = client.list_issues(
            status=IssueStatus.OPEN,
            assignee="alice"
        )
        assert len(alice_open) >= 1
        assert all(i.status == IssueStatus.OPEN for i in alice_open)
        assert all(i.assignee == "alice" for i in alice_open)

        # P0-P1 features
        high_priority_features = client.list_issues(
            issue_type=IssueType.FEATURE,
            priority=0
        )
        assert any(i.id == created_issues[0].id for i in high_priority_features)

    def test_list_issues_with_limit(self, populated_db):
        """Test limit parameter."""
        client, created_issues = populated_db

        # Get only 2 issues
        limited = client.list_issues(limit=2)
        assert len(limited) == 2

        # Get only 1 issue
        single = client.list_issues(limit=1)
        assert len(single) == 1

    def test_list_issues_performance(self, populated_db):
        """Test that list_issues completes in < 100ms (SC-001)."""
        client, created_issues = populated_db

        # Time the list operation
        start = time.perf_counter()
        issues = client.list_issues()
        duration = time.perf_counter() - start

        # Should complete in < 100ms
        assert duration < 0.1, f"list_issues took {duration*1000:.1f}ms (expected < 100ms)"
        assert len(issues) > 0


# T073: Test scenario - Issue with metadata (dates and author)
class TestIssueMetadata:
    """Test scenarios for issue metadata (dates, hashes, etc)."""

    def test_issue_metadata_dates_correctly_parsed(self, beads_client, test_beads_db, monkeypatch):
        """Test scenario: Issue with metadata → dates and author correctly parsed."""
        monkeypatch.chdir(test_beads_db)

        # Create issue
        created = beads_client.create_issue(
            title="Metadata Test Issue",
            description="Testing datetime parsing",
            issue_type=IssueType.TASK,
            priority=2
        )

        # Retrieve and verify dates
        retrieved = beads_client.get_issue(created.id)

        # Dates should be datetime objects
        assert isinstance(retrieved.created_at, datetime)
        assert isinstance(retrieved.updated_at, datetime)

        # created_at and updated_at should be close (same second)
        time_diff = abs((retrieved.updated_at - retrieved.created_at).total_seconds())
        assert time_diff < 2.0  # Within 2 seconds

        # Update the issue to change updated_at
        time.sleep(0.1)  # Small delay
        beads_client.update_issue_status(created.id, IssueStatus.IN_PROGRESS)

        # Retrieve again
        updated_issue = beads_client.get_issue(created.id)

        # created_at should be unchanged
        assert updated_issue.created_at == retrieved.created_at

        # updated_at should be different (or at least not earlier)
        assert updated_issue.updated_at >= retrieved.updated_at

        # content_hash should exist and be non-empty
        assert updated_issue.content_hash
        assert len(updated_issue.content_hash) > 0

        # source_repo should exist
        assert updated_issue.source_repo
