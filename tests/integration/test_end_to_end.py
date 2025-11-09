"""Integration tests for end-to-end vector memory operations."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from vector_memory.coordinate import VectorCoordinate
from vector_memory.exceptions import CoordinateValidationError, ImmutableLayerError
from vector_memory.manager import VectorMemoryManager


@pytest.fixture
def temp_repo():
    """Create a temporary Git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize git repository
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path


class TestStoreAndRetrieve:
    """Test basic store and retrieve operations."""

    def test_store_and_retrieve_decision(self, temp_repo, mock_issue_id):
        """Test storing and retrieving a decision at specific coordinates."""
        # Initialize manager
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store a decision
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        decision = manager.store(
            coord=coord,
            content="Use PostgreSQL for persistence",
            issue_context={"issue_id": "test-123"},
        )

        # Verify decision was stored with correct metadata
        assert decision.coordinate == coord
        assert decision.content == "Use PostgreSQL for persistence"
        assert decision.agent_id == "test-agent"
        assert decision.issue_context["issue_id"] == "test-123"

        # Retrieve the decision
        retrieved = manager.get(coord)

        assert retrieved is not None
        assert retrieved.coordinate == coord
        assert retrieved.content == "Use PostgreSQL for persistence"
        assert retrieved.agent_id == "test-agent"

    def test_retrieve_nonexistent_coordinate(self, temp_repo, mock_issue_id):
        """Test retrieving from empty coordinate returns None."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coord = VectorCoordinate(x=mock_issue_id(10), y=3, z=2)
        result = manager.get(coord)

        assert result is None

    def test_exists_check(self, temp_repo, mock_issue_id):
        """Test checking if coordinate has a decision."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)

        # Should not exist initially
        assert not manager.exists(coord)

        # Store decision
        manager.store(coord, "Test content")

        # Should now exist
        assert manager.exists(coord)

    def test_store_multiple_coordinates(self, temp_repo, mock_issue_id):
        """Test storing decisions at multiple coordinates."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coords = [
            VectorCoordinate(x=mock_issue_id(1), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(2), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(3), y=3, z=3),
        ]

        # Store decisions
        for i, coord in enumerate(coords):
            manager.store(coord, f"Decision {i+1}")

        # Retrieve and verify
        for i, coord in enumerate(coords):
            decision = manager.get(coord)
            assert decision is not None
            assert decision.content == f"Decision {i+1}"

    def test_overwrite_mutable_layer(self, temp_repo, mock_issue_id):
        """Test that mutable layers can be overwritten."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coord = VectorCoordinate(x=mock_issue_id(5), y=3, z=3)  # z=3 is mutable

        # Store initial decision
        manager.store(coord, "Version 1")
        decision1 = manager.get(coord)
        assert decision1.content == "Version 1"

        # Overwrite with new decision
        manager.store(coord, "Version 2")
        decision2 = manager.get(coord)
        assert decision2.content == "Version 2"

    def test_immutable_layer_enforcement(self, temp_repo, mock_issue_id):
        """Test that z=1 layer cannot be modified."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)  # z=1 is immutable

        # Store initial decision
        manager.store(coord, "Original decision")

        # Attempt to overwrite should fail
        with pytest.raises(ImmutableLayerError, match="Cannot modify decision"):
            manager.store(coord, "Modified decision")

        # Original decision should still be there
        decision = manager.get(coord)
        assert decision.content == "Original decision"


class TestValidation:
    """Test input validation."""

    def test_empty_content_rejected(self, temp_repo, mock_issue_id):
        """Test that empty content is rejected."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)

        with pytest.raises(ValueError, match="content"):
            manager.store(coord, "")

    def test_content_too_large_rejected(self, temp_repo, mock_issue_id):
        """Test that content over 100KB is rejected."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        large_content = "x" * (100 * 1024 + 1)  # 100KB + 1 byte

        with pytest.raises(ValueError, match="too large"):
            manager.store(coord, large_content)

    def test_invalid_coordinate_rejected(self, temp_repo, mock_issue_id):
        """Test that invalid coordinates are rejected."""
        VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Test invalid issue ID format (x must be a valid Beads ID)
        with pytest.raises(CoordinateValidationError, match="valid Beads issue ID"):
            VectorCoordinate(x="invalid", y=2, z=1)

        # Test invalid y value (must be 1-5)
        with pytest.raises(CoordinateValidationError):
            VectorCoordinate(x=mock_issue_id(5), y=6, z=1)

        # Test invalid z value (must be 1-4)
        with pytest.raises(CoordinateValidationError):
            VectorCoordinate(x=mock_issue_id(5), y=2, z=5)


class TestManagerInitialization:
    """Test VectorMemoryManager initialization."""

    def test_empty_agent_id_rejected(self, temp_repo):
        """Test that empty agent_id is rejected."""
        with pytest.raises(ValueError, match="agent_id"):
            VectorMemoryManager(repo_path=temp_repo, agent_id="")

    def test_nonexistent_repo_rejected(self):
        """Test that nonexistent repo path is rejected."""
        from vector_memory.exceptions import StorageError

        fake_path = Path("/nonexistent/path/to/repo")

        with pytest.raises(StorageError, match="does not exist"):
            VectorMemoryManager(repo_path=fake_path, agent_id="test")

    def test_non_git_repo_rejected(self):
        """Test that non-Git directory is rejected."""
        from vector_memory.exceptions import StorageError

        with tempfile.TemporaryDirectory() as tmpdir:
            non_git_path = Path(tmpdir)

            with pytest.raises(StorageError, match="Not a Git repository"):
                VectorMemoryManager(repo_path=non_git_path, agent_id="test")

    def test_creates_vector_memory_directory(self, temp_repo, mock_issue_id):
        """Test that .vector-memory directory is created."""
        VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        vector_memory_dir = temp_repo / ".vector-memory"
        assert vector_memory_dir.exists()
        assert vector_memory_dir.is_dir()


class TestRollbackScenario:
    """Test rollback scenario using partial ordering (Phase 7 - User Story 5)."""

    def test_rollback_to_safe_state(self, temp_repo, mock_issue_id):
        """
        Test rollback scenario: find all decisions before error point.

        Scenario: Error detected at issue 7, stage 4. Need to find all
        decisions that occurred "before" this point for potential rollback.
        """
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Simulate a development timeline with decisions at various points
        timeline = [
            (1, 2, 1, "Issue 1: Architecture decision - Use PostgreSQL"),
            (1, 3, 3, "Issue 1: Implementation - Database schema created"),
            (2, 2, 1, "Issue 2: Architecture decision - REST API structure"),
            (3, 2, 1, "Issue 3: Architecture decision - Authentication strategy"),
            (3, 4, 2, "Issue 3: Review - API contracts defined"),
            (5, 2, 1, "Issue 5: Architecture decision - Caching strategy"),
            (5, 3, 3, "Issue 5: Implementation - Redis integration"),
            (7, 2, 1, "Issue 7: Architecture decision - Logging framework"),
            (7, 4, 3, "Issue 7: Implementation - ERROR DETECTED HERE"),
        ]

        # Store all decisions
        for x, y, z, content in timeline:
            coord = VectorCoordinate(x=mock_issue_id(x), y=y, z=z)
            manager.store(coord, content)

        # Error detected at (7, 4) - find all decisions before this point
        error_x, error_y = 7, 4
        decisions_before_error = manager.query_partial_order(
            x_threshold=mock_issue_id(error_x), y_threshold=error_y
        )

        # Should get all decisions except (7, 4) itself
        assert len(decisions_before_error) == 8

        # Verify all returned decisions are before error point
        for decision in decisions_before_error:
            x, y = decision.coordinate.x, decision.coordinate.y
            assert x < mock_issue_id(error_x) or (x == mock_issue_id(error_x) and y < error_y)

        # Verify the error decision is NOT included
        error_contents = [d.content for d in decisions_before_error]
        assert not any("ERROR DETECTED" in c for c in error_contents)

    def test_rollback_with_layer_filter(self, temp_repo, mock_issue_id):
        """
        Test rollback with layer filtering.

        Scenario: Need to rollback architecture decisions only (z=1) before
        a specific point, without affecting other layers.
        """
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store decisions at different layers
        decisions = [
            (1, 2, 1, "Architecture: Database choice"),
            (1, 3, 3, "Implementation: DB setup code"),
            (2, 2, 1, "Architecture: API design"),
            (2, 3, 3, "Implementation: API code"),
            (3, 2, 1, "Architecture: Auth strategy"),
            (3, 3, 3, "Implementation: Auth code"),
            (5, 2, 1, "Architecture: Caching"),
            (5, 4, 4, "Ephemeral: Debug notes"),
        ]

        for x, y, z, content in decisions:
            manager.store(VectorCoordinate(x=mock_issue_id(x), y=y, z=z), content)

        # Find only architecture decisions (z=1) before issue 5
        arch_decisions = manager.query_partial_order(
            x_threshold=mock_issue_id(5), y_threshold=1, z_filter=1
        )

        # Should get architecture decisions from issues 1, 2, 3 only
        assert len(arch_decisions) == 3
        assert all(d.coordinate.z == 1 for d in arch_decisions)
        assert all(d.coordinate.x < mock_issue_id(5) for d in arch_decisions)

        # Verify content
        contents = [d.content for d in arch_decisions]
        assert any("Database choice" in c for c in contents)
        assert any("API design" in c for c in contents)
        assert any("Auth strategy" in c for c in contents)

    def test_rollback_preserves_immutable_decisions(self, temp_repo, mock_issue_id):
        """
        Test that rollback query properly identifies immutable architecture
        decisions that must be preserved.
        """
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store mix of decisions
        decisions = [
            (1, 2, 1, "Architecture: Core design"),
            (2, 2, 1, "Architecture: Module structure"),
            (3, 3, 3, "Implementation: Module code"),
            (4, 2, 1, "Architecture: Error handling"),
            (5, 3, 3, "Implementation: Error code - BUG HERE"),
        ]

        for x, y, z, content in decisions:
            manager.store(VectorCoordinate(x=mock_issue_id(x), y=y, z=z), content)

        # Find all immutable architecture decisions before the bug
        safe_arch_decisions = manager.query_partial_order(
            x_threshold=mock_issue_id(5), y_threshold=3, z_filter=1  # Architecture layer only
        )

        # Should get all architecture decisions from issues 1-4
        assert len(safe_arch_decisions) == 3
        assert all(d.coordinate.z == 1 for d in safe_arch_decisions)

        # These decisions are immutable and must remain even after rollback
        for decision in safe_arch_decisions:
            assert "Architecture" in decision.content
            # Verify they're actually immutable by testing we can't modify them
            with pytest.raises(ImmutableLayerError):
                manager.store(decision.coordinate, "Attempted modification")

    def test_incremental_rollback_workflow(self, temp_repo, mock_issue_id):
        """
        Test incremental rollback: find decisions at different thresholds.

        Simulates finding progressively earlier safe states.
        """
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store timeline
        for x in [1, 2, 3, 5, 7, 10]:
            for y in [2, 3]:
                manager.store(
                    VectorCoordinate(x=mock_issue_id(x), y=y, z=1), f"Decision at ({x}, {y})"
                )

        # Error at (10, 3) - try rollback points
        # We stored: [1,2], [1,3], [2,2], [2,3], [3,2], [3,3], [5,2], [5,3], [7,2], [7,3], [10,2], [10,3]
        thresholds = [
            (10, 3, 11),  # Just before error: x<10 or (x==10 and y<3) = 11 decisions
            (7, 5, 10),  # Back to issue 7: x<7 or (x==7 and y<5) = 10 decisions
            (5, 5, 8),  # Back to issue 5: x<5 or (x==5 and y<5) = 8 decisions
            (3, 5, 6),  # Back to issue 3: x<3 or (x==3 and y<5) = 6 decisions
        ]

        for x_thresh, y_thresh, expected_count in thresholds:
            decisions = manager.query_partial_order(
                x_threshold=mock_issue_id(x_thresh), y_threshold=y_thresh
            )
            assert len(decisions) == expected_count

            # Verify all are before threshold
            for d in decisions:
                x, y = d.coordinate.x, d.coordinate.y
                assert x < mock_issue_id(x_thresh) or (
                    x == mock_issue_id(x_thresh) and y < y_thresh
                )
