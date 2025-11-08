"""Unit tests for data models (Issue, enums, dependencies)."""

import pytest
from datetime import datetime
from enum import Enum


# Tests for T009: IssueStatus enum
class TestIssueStatus:
    """Test IssueStatus enum validation and values."""

    def test_issue_status_values(self):
        """Test that all required status values exist."""
        from beads.models import IssueStatus

        assert hasattr(IssueStatus, 'OPEN')
        assert hasattr(IssueStatus, 'IN_PROGRESS')
        assert hasattr(IssueStatus, 'BLOCKED')
        assert hasattr(IssueStatus, 'CLOSED')

    def test_issue_status_string_values(self):
        """Test that enum values match Beads JSON format."""
        from beads.models import IssueStatus

        assert IssueStatus.OPEN.value == "open"
        assert IssueStatus.IN_PROGRESS.value == "in_progress"
        assert IssueStatus.BLOCKED.value == "blocked"
        assert IssueStatus.CLOSED.value == "closed"

    def test_issue_status_is_string_enum(self):
        """Test that IssueStatus is a string enum."""
        from beads.models import IssueStatus

        # String enums can be compared to strings
        assert IssueStatus.OPEN == "open"
        assert isinstance(IssueStatus.OPEN.value, str)

    def test_issue_status_from_string(self):
        """Test creating IssueStatus from string values."""
        from beads.models import IssueStatus

        assert IssueStatus("open") == IssueStatus.OPEN
        assert IssueStatus("in_progress") == IssueStatus.IN_PROGRESS
        assert IssueStatus("blocked") == IssueStatus.BLOCKED
        assert IssueStatus("closed") == IssueStatus.CLOSED

    def test_issue_status_invalid_value(self):
        """Test that invalid status values raise ValueError."""
        from beads.models import IssueStatus

        with pytest.raises(ValueError):
            IssueStatus("invalid_status")


# Tests for T010: IssueType enum
class TestIssueType:
    """Test IssueType enum validation and values."""

    def test_issue_type_values(self):
        """Test that all required type values exist."""
        from beads.models import IssueType

        assert hasattr(IssueType, 'BUG')
        assert hasattr(IssueType, 'FEATURE')
        assert hasattr(IssueType, 'TASK')
        assert hasattr(IssueType, 'EPIC')
        assert hasattr(IssueType, 'CHORE')

    def test_issue_type_string_values(self):
        """Test that enum values match Beads JSON format."""
        from beads.models import IssueType

        assert IssueType.BUG.value == "bug"
        assert IssueType.FEATURE.value == "feature"
        assert IssueType.TASK.value == "task"
        assert IssueType.EPIC.value == "epic"
        assert IssueType.CHORE.value == "chore"

    def test_issue_type_is_string_enum(self):
        """Test that IssueType is a string enum."""
        from beads.models import IssueType

        assert IssueType.FEATURE == "feature"
        assert isinstance(IssueType.FEATURE.value, str)

    def test_issue_type_from_string(self):
        """Test creating IssueType from string values."""
        from beads.models import IssueType

        assert IssueType("bug") == IssueType.BUG
        assert IssueType("feature") == IssueType.FEATURE
        assert IssueType("task") == IssueType.TASK
        assert IssueType("epic") == IssueType.EPIC
        assert IssueType("chore") == IssueType.CHORE

    def test_issue_type_invalid_value(self):
        """Test that invalid type values raise ValueError."""
        from beads.models import IssueType

        with pytest.raises(ValueError):
            IssueType("invalid_type")


# Tests for T011: DependencyType enum
class TestDependencyType:
    """Test DependencyType enum validation and values."""

    def test_dependency_type_values(self):
        """Test that all required dependency type values exist."""
        from beads.models import DependencyType

        assert hasattr(DependencyType, 'BLOCKS')
        assert hasattr(DependencyType, 'RELATED')
        assert hasattr(DependencyType, 'PARENT_CHILD')
        assert hasattr(DependencyType, 'DISCOVERED_FROM')

    def test_dependency_type_string_values(self):
        """Test that enum values match Beads JSON format."""
        from beads.models import DependencyType

        assert DependencyType.BLOCKS.value == "blocks"
        assert DependencyType.RELATED.value == "related"
        assert DependencyType.PARENT_CHILD.value == "parent-child"
        assert DependencyType.DISCOVERED_FROM.value == "discovered-from"

    def test_dependency_type_is_string_enum(self):
        """Test that DependencyType is a string enum."""
        from beads.models import DependencyType

        assert DependencyType.BLOCKS == "blocks"
        assert isinstance(DependencyType.BLOCKS.value, str)

    def test_dependency_type_from_string(self):
        """Test creating DependencyType from string values."""
        from beads.models import DependencyType

        assert DependencyType("blocks") == DependencyType.BLOCKS
        assert DependencyType("related") == DependencyType.RELATED
        assert DependencyType("parent-child") == DependencyType.PARENT_CHILD
        assert DependencyType("discovered-from") == DependencyType.DISCOVERED_FROM

    def test_dependency_type_invalid_value(self):
        """Test that invalid dependency type values raise ValueError."""
        from beads.models import DependencyType

        with pytest.raises(ValueError):
            DependencyType("invalid_dependency")


# Tests for T033: Issue dataclass validation
class TestIssueDataclass:
    """Test Issue dataclass validation and required fields."""

    def test_issue_dataclass_exists(self):
        """Test that Issue dataclass is defined."""
        from beads.models import Issue

        assert Issue is not None

    def test_issue_with_valid_data(self):
        """Test creating Issue with all valid required fields."""
        from beads.models import Issue, IssueStatus, IssueType
        from datetime import datetime

        issue = Issue(
            id="test-123",
            title="Test Issue",
            description="Test description",
            status=IssueStatus.OPEN,
            priority=1,
            issue_type=IssueType.FEATURE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            content_hash="abc123",
            source_repo="."
        )

        assert issue.id == "test-123"
        assert issue.title == "Test Issue"
        assert issue.description == "Test description"
        assert issue.status == IssueStatus.OPEN
        assert issue.priority == 1
        assert issue.issue_type == IssueType.FEATURE
        assert issue.content_hash == "abc123"
        assert issue.source_repo == "."

    def test_issue_with_optional_fields(self):
        """Test Issue with optional assignee and labels."""
        from beads.models import Issue, IssueStatus, IssueType
        from datetime import datetime

        issue = Issue(
            id="test-123",
            title="Test Issue",
            description="Test description",
            status=IssueStatus.OPEN,
            priority=1,
            issue_type=IssueType.FEATURE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            content_hash="abc123",
            source_repo=".",
            assignee="user@example.com",
            labels=["bug", "urgent"]
        )

        assert issue.assignee == "user@example.com"
        assert issue.labels == ["bug", "urgent"]

    def test_issue_validation_empty_id(self):
        """Test that empty ID raises ValueError."""
        from beads.models import Issue, IssueStatus, IssueType
        from datetime import datetime

        with pytest.raises(ValueError, match="Issue ID cannot be empty"):
            Issue(
                id="",
                title="Test Issue",
                description="Test description",
                status=IssueStatus.OPEN,
                priority=1,
                issue_type=IssueType.FEATURE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                content_hash="abc123",
                source_repo="."
            )

    def test_issue_validation_empty_title(self):
        """Test that empty title raises ValueError."""
        from beads.models import Issue, IssueStatus, IssueType
        from datetime import datetime

        with pytest.raises(ValueError, match="Title cannot be empty"):
            Issue(
                id="test-123",
                title="",
                description="Test description",
                status=IssueStatus.OPEN,
                priority=1,
                issue_type=IssueType.FEATURE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                content_hash="abc123",
                source_repo="."
            )

    def test_issue_validation_invalid_priority_low(self):
        """Test that priority < 0 raises ValueError."""
        from beads.models import Issue, IssueStatus, IssueType
        from datetime import datetime

        with pytest.raises(ValueError, match="Priority must be 0-4"):
            Issue(
                id="test-123",
                title="Test Issue",
                description="Test description",
                status=IssueStatus.OPEN,
                priority=-1,
                issue_type=IssueType.FEATURE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                content_hash="abc123",
                source_repo="."
            )

    def test_issue_validation_invalid_priority_high(self):
        """Test that priority > 4 raises ValueError."""
        from beads.models import Issue, IssueStatus, IssueType
        from datetime import datetime

        with pytest.raises(ValueError, match="Priority must be 0-4"):
            Issue(
                id="test-123",
                title="Test Issue",
                description="Test description",
                status=IssueStatus.OPEN,
                priority=5,
                issue_type=IssueType.FEATURE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                content_hash="abc123",
                source_repo="."
            )


# Tests for T034: Issue.from_json() parsing
class TestIssueFromJson:
    """Test Issue.from_json() class method for parsing JSON."""

    def test_from_json_valid_data(self):
        """Test parsing valid JSON into Issue dataclass."""
        from beads.models import Issue, IssueStatus, IssueType

        json_data = {
            "id": "test-abc",
            "title": "Test Issue",
            "description": "Test description",
            "status": "open",
            "priority": 1,
            "issue_type": "feature",
            "created_at": "2025-11-07T12:00:00Z",
            "updated_at": "2025-11-07T13:00:00Z",
            "content_hash": "hash123",
            "source_repo": "."
        }

        issue = Issue.from_json(json_data)

        assert issue.id == "test-abc"
        assert issue.title == "Test Issue"
        assert issue.description == "Test description"
        assert issue.status == IssueStatus.OPEN
        assert issue.priority == 1
        assert issue.issue_type == IssueType.FEATURE
        assert issue.content_hash == "hash123"
        assert issue.source_repo == "."

    def test_from_json_with_optional_fields(self):
        """Test parsing JSON with optional assignee and labels."""
        from beads.models import Issue

        json_data = {
            "id": "test-abc",
            "title": "Test Issue",
            "description": "Test description",
            "status": "open",
            "priority": 1,
            "issue_type": "feature",
            "created_at": "2025-11-07T12:00:00Z",
            "updated_at": "2025-11-07T13:00:00Z",
            "content_hash": "hash123",
            "source_repo": ".",
            "assignee": "user@example.com",
            "labels": ["bug", "urgent"]
        }

        issue = Issue.from_json(json_data)

        assert issue.assignee == "user@example.com"
        assert issue.labels == ["bug", "urgent"]

    def test_from_json_datetime_parsing(self):
        """Test that datetime strings are properly parsed."""
        from beads.models import Issue
        from datetime import datetime

        json_data = {
            "id": "test-abc",
            "title": "Test Issue",
            "description": "Test description",
            "status": "open",
            "priority": 1,
            "issue_type": "feature",
            "created_at": "2025-11-07T12:30:45.123Z",
            "updated_at": "2025-11-07T13:45:30.456Z",
            "content_hash": "hash123",
            "source_repo": "."
        }

        issue = Issue.from_json(json_data)

        assert isinstance(issue.created_at, datetime)
        assert isinstance(issue.updated_at, datetime)

    def test_from_json_missing_optional_fields(self):
        """Test parsing JSON without optional fields."""
        from beads.models import Issue

        json_data = {
            "id": "test-abc",
            "title": "Test Issue",
            "description": "Test description",
            "status": "open",
            "priority": 1,
            "issue_type": "feature",
            "created_at": "2025-11-07T12:00:00Z",
            "updated_at": "2025-11-07T13:00:00Z",
            "content_hash": "hash123",
            "source_repo": "."
        }

        issue = Issue.from_json(json_data)

        assert issue.assignee is None
        assert issue.labels is None or issue.labels == []

    def test_from_json_invalid_status(self):
        """Test that invalid status raises ValueError."""
        from beads.models import Issue

        json_data = {
            "id": "test-abc",
            "title": "Test Issue",
            "description": "Test description",
            "status": "invalid_status",
            "priority": 1,
            "issue_type": "feature",
            "created_at": "2025-11-07T12:00:00Z",
            "updated_at": "2025-11-07T13:00:00Z",
            "content_hash": "hash123",
            "source_repo": "."
        }

        with pytest.raises(ValueError):
            Issue.from_json(json_data)

    def test_from_json_invalid_type(self):
        """Test that invalid issue_type raises ValueError."""
        from beads.models import Issue

        json_data = {
            "id": "test-abc",
            "title": "Test Issue",
            "description": "Test description",
            "status": "open",
            "priority": 1,
            "issue_type": "invalid_type",
            "created_at": "2025-11-07T12:00:00Z",
            "updated_at": "2025-11-07T13:00:00Z",
            "content_hash": "hash123",
            "source_repo": "."
        }

        with pytest.raises(ValueError):
            Issue.from_json(json_data)
