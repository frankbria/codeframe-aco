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
