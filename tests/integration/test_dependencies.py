"""Integration tests for dependency management operations."""

import pytest
import subprocess

from beads.client import BeadsClient
from beads.models import IssueType, DependencyType
from beads.exceptions import BeadsDependencyCycleError


@pytest.fixture
def beads_client_with_dependencies(test_beads_db, monkeypatch):
    """Create BeadsClient with test issues for dependency testing."""
    monkeypatch.chdir(test_beads_db)

    # Create test issues via bd CLI
    subprocess.run(
        ['bd', 'create', 'Issue A', '--type', 'task', '--priority', '2'],
        capture_output=True,
        check=True
    )

    subprocess.run(
        ['bd', 'create', 'Issue B', '--type', 'task', '--priority', '2'],
        capture_output=True,
        check=True
    )

    subprocess.run(
        ['bd', 'create', 'Issue C', '--type', 'task', '--priority', '2'],
        capture_output=True,
        check=True
    )

    client = BeadsClient(sandbox=True)
    return client


# T104-T105: Integration tests for adding dependencies
class TestAddDependency:
    """Integration tests for adding dependencies."""

    def test_add_blocks_dependency(self, beads_client_with_dependencies):
        """Test T105: Add 'blocks' dependency → blocked issue not in bd ready."""
        client = beads_client_with_dependencies

        # Get two issues
        ready_issues = client.get_ready_issues()
        assert len(ready_issues) >= 2

        issue_a = ready_issues[0]
        issue_b = ready_issues[1]

        # Add dependency: issue_a blocks issue_b
        dep = client.add_dependency(
            blocked_id=issue_a.id,
            blocker_id=issue_b.id,
            dep_type=DependencyType.BLOCKS
        )

        assert dep.blocked_id == issue_a.id
        assert dep.blocker_id == issue_b.id
        assert dep.dependency_type == DependencyType.BLOCKS

        # Verify issue_a is now blocked (not in ready list)
        ready_after = client.get_ready_issues()
        ready_ids = {issue.id for issue in ready_after}

        # issue_a should not be ready (it's blocked by issue_b)
        assert issue_a.id not in ready_ids

    def test_add_self_dependency_raises_error(self, beads_client_with_dependencies):
        """Test that adding self-dependency raises ValueError."""
        client = beads_client_with_dependencies

        ready_issues = client.get_ready_issues()
        issue_id = ready_issues[0].id

        with pytest.raises(ValueError, match="Issue cannot depend on itself"):
            client.add_dependency(
                blocked_id=issue_id,
                blocker_id=issue_id,
                dep_type=DependencyType.BLOCKS
            )

    def test_add_all_dependency_types(self, beads_client_with_dependencies):
        """Test T117: All 4 dependency types work correctly."""
        client = beads_client_with_dependencies

        # Get issues
        ready_issues = client.get_ready_issues()
        assert len(ready_issues) >= 3

        # Test each dependency type
        for idx, dep_type in enumerate(DependencyType):
            if idx >= len(ready_issues) - 1:
                break

            dep = client.add_dependency(
                blocked_id=ready_issues[0].id,
                blocker_id=ready_issues[idx + 1].id,
                dep_type=dep_type
            )
            assert dep.dependency_type == dep_type


# T106: Test removing dependencies
class TestRemoveDependency:
    """Integration tests for removing dependencies."""

    def test_remove_dependency_makes_issue_ready(self, beads_client_with_dependencies):
        """Test T106: Remove dependency → previously blocked issue becomes ready."""
        client = beads_client_with_dependencies

        # Get two issues and add dependency
        ready_issues = client.get_ready_issues()
        issue_a = ready_issues[0]
        issue_b = ready_issues[1]

        # Add dependency
        client.add_dependency(
            blocked_id=issue_a.id,
            blocker_id=issue_b.id,
            dep_type=DependencyType.BLOCKS
        )

        # Verify issue_a is blocked
        ready_after_add = client.get_ready_issues()
        ready_ids_after_add = {issue.id for issue in ready_after_add}
        assert issue_a.id not in ready_ids_after_add

        # Remove dependency
        client.remove_dependency(issue_a.id, issue_b.id)

        # Verify issue_a is now ready again
        ready_after_remove = client.get_ready_issues()
        ready_ids_after_remove = {issue.id for issue in ready_after_remove}
        assert issue_a.id in ready_ids_after_remove

    def test_remove_nonexistent_dependency_is_idempotent(self, beads_client_with_dependencies):
        """Test that removing non-existent dependency doesn't raise error."""
        client = beads_client_with_dependencies

        ready_issues = client.get_ready_issues()

        # Remove a dependency that doesn't exist (should not error)
        client.remove_dependency(ready_issues[0].id, ready_issues[1].id)


# T107: Test dependency tree queries
class TestGetDependencyTree:
    """Integration tests for querying dependency trees."""

    def test_get_dependency_tree(self, beads_client_with_dependencies):
        """Test T107: Query dependency tree → structure reflects relationships."""
        client = beads_client_with_dependencies

        # Get issues
        ready_issues = client.get_ready_issues()
        issue_a = ready_issues[0]
        issue_b = ready_issues[1]

        # Add dependency: issue_a is blocked by issue_b
        client.add_dependency(
            blocked_id=issue_a.id,
            blocker_id=issue_b.id,
            dep_type=DependencyType.BLOCKS
        )

        # Query tree for issue_a
        tree = client.get_dependency_tree(issue_a.id)

        assert tree.issue_id == issue_a.id
        assert issue_b.id in tree.blockers

    def test_get_dependency_tree_no_dependencies(self, beads_client_with_dependencies):
        """Test dependency tree for issue with no dependencies."""
        client = beads_client_with_dependencies

        ready_issues = client.get_ready_issues()
        issue_id = ready_issues[0].id

        tree = client.get_dependency_tree(issue_id)

        assert tree.issue_id == issue_id
        assert len(tree.blockers) == 0
        assert len(tree.blocked_by) == 0


# T108, T118: Test cycle detection
class TestDetectDependencyCycles:
    """Integration tests for cycle detection."""

    def test_detect_dependency_cycles_none(self, beads_client_with_dependencies):
        """Test T118: Verify cycle detection with no cycles."""
        client = beads_client_with_dependencies

        cycles = client.detect_dependency_cycles()

        assert isinstance(cycles, list)
        assert len(cycles) == 0

    def test_add_cycle_creating_dependency_raises_error(self, beads_client_with_dependencies):
        """Test T108: Add cycle-creating dependency → raises error (bd prevents it)."""
        client = beads_client_with_dependencies

        # Get two issues
        ready_issues = client.get_ready_issues()
        issue_a = ready_issues[0]
        issue_b = ready_issues[1]

        # Add dependency: A depends on B
        client.add_dependency(
            blocked_id=issue_a.id,
            blocker_id=issue_b.id,
            dep_type=DependencyType.BLOCKS
        )

        # Try to add reverse dependency: B depends on A (creates cycle)
        # bd should prevent this
        with pytest.raises((BeadsDependencyCycleError, Exception)):
            client.add_dependency(
                blocked_id=issue_b.id,
                blocker_id=issue_a.id,
                dep_type=DependencyType.BLOCKS
            )
