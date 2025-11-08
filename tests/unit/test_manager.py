"""Unit tests for VectorMemoryManager with focus on immutability."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from vector_memory.coordinate import VectorCoordinate
from vector_memory.exceptions import ImmutableLayerError
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


class TestImmutabilityEnforcement:
    """Test architecture layer (z=1) immutability enforcement."""

    def test_cannot_modify_architecture_layer(self, temp_repo, mock_issue_id):
        """Test that z=1 layer cannot be modified after initial store."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)

        # Store initial architecture decision
        manager.store(coord, "Use PostgreSQL for persistence")

        # Verify it was stored
        decision = manager.get(coord)
        assert decision.content == "Use PostgreSQL for persistence"

        # Attempt to modify should fail with ImmutableLayerError
        with pytest.raises(ImmutableLayerError, match="Cannot modify decision"):
            manager.store(coord, "Use MongoDB instead")

        # Original decision should still be intact
        decision = manager.get(coord)
        assert decision.content == "Use PostgreSQL for persistence"

    def test_cannot_overwrite_architecture_layer(self, temp_repo, mock_issue_id):
        """Test that architecture layer decisions are permanent."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coord = VectorCoordinate(x=mock_issue_id(3), y=2, z=1)

        # Store decision
        manager.store(coord, "Original architecture decision")

        # Multiple attempts to overwrite should all fail
        for i in range(3):
            with pytest.raises(ImmutableLayerError):
                manager.store(coord, f"Attempt {i+1} to modify")

        # Original should still be there
        decision = manager.get(coord)
        assert decision.content == "Original architecture decision"

    def test_architecture_immutability_across_sessions(self, temp_repo, mock_issue_id):
        """Test that immutability persists across manager instances."""
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)

        # First session: store decision
        manager1 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-1")
        manager1.store(coord, "Session 1 decision")

        # Second session: attempt to modify should fail
        manager2 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-2")

        with pytest.raises(ImmutableLayerError):
            manager2.store(coord, "Session 2 modification")

        # Original decision should be intact
        decision = manager2.get(coord)
        assert decision.content == "Session 1 decision"
        assert decision.agent_id == "agent-1"  # From original store

    def test_can_store_new_architecture_decisions(self, temp_repo, mock_issue_id):
        """Test that new z=1 coordinates can be used (just not modified)."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store multiple architecture decisions at different coordinates
        coords = [
            VectorCoordinate(x=mock_issue_id(1), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(2), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(3), y=2, z=1),
        ]

        for i, coord in enumerate(coords):
            manager.store(coord, f"Architecture decision {i+1}")

        # All should be retrievable
        for i, coord in enumerate(coords):
            decision = manager.get(coord)
            assert decision.content == f"Architecture decision {i+1}"

        # But none should be modifiable
        for coord in coords:
            with pytest.raises(ImmutableLayerError):
                manager.store(coord, "Modified")

    def test_mutable_layers_can_be_modified(self, temp_repo, mock_issue_id):
        """Test that layers z=2,3,4 can be modified."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Test each mutable layer
        for z in [2, 3, 4]:
            coord = VectorCoordinate(x=mock_issue_id(1), y=2, z=z)

            # Store initial version
            manager.store(coord, f"Layer {z} v1")
            decision = manager.get(coord)
            assert decision.content == f"Layer {z} v1"

            # Modify should succeed
            manager.store(coord, f"Layer {z} v2")
            decision = manager.get(coord)
            assert decision.content == f"Layer {z} v2"

    def test_error_message_includes_coordinate(self, temp_repo, mock_issue_id):
        """Test that immutability errors include helpful context."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coord = VectorCoordinate(x=mock_issue_id(42), y=3, z=1)
        manager.store(coord, "Original")

        try:
            manager.store(coord, "Modified")
            raise AssertionError("Expected ImmutableLayerError")
        except ImmutableLayerError as e:
            error_msg = str(e)
            # Should mention it's the Architecture layer
            assert "Architecture" in error_msg or "z=1" in error_msg
            # Should mention it's immutable
            assert "immutable" in error_msg.lower()

    def test_immutability_with_different_agents(self, temp_repo, mock_issue_id):
        """Test that immutability applies across different agents."""
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)

        # Agent 1 stores decision
        manager1 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-1")
        manager1.store(coord, "Agent 1 decision")

        # Agent 2 cannot modify
        manager2 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-2")

        with pytest.raises(ImmutableLayerError):
            manager2.store(coord, "Agent 2 modification")

        # Agent 3 also cannot modify
        manager3 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-3")

        with pytest.raises(ImmutableLayerError):
            manager3.store(coord, "Agent 3 modification")


class TestArchitectureLayerBehavior:
    """Test specific behaviors of the architecture layer."""

    def test_architecture_layer_empty_initially(self, temp_repo, mock_issue_id):
        """Test that empty architecture coordinates can be written to."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coord = VectorCoordinate(x=mock_issue_id(10), y=2, z=1)

        # Should not exist initially
        assert not manager.exists(coord)

        # Should be able to write to empty coordinate
        manager.store(coord, "Initial architecture")

        # Now it should exist
        assert manager.exists(coord)

    def test_query_architecture_decisions_separately(self, temp_repo, mock_issue_id):
        """Test querying only architecture layer decisions."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store decisions across multiple layers
        for x in [1, 2, 3]:
            for z in [1, 2, 3, 4]:
                coord = VectorCoordinate(x=mock_issue_id(x), y=2, z=z)
                manager.store(coord, f"x={x},z={z}")

        # Query only architecture layer (z=1)
        arch_decisions = manager.query_range(z_range=(1, 1))

        assert len(arch_decisions) == 3  # x=1,2,3 at z=1
        for decision in arch_decisions:
            assert decision.coordinate.z == 1

    def test_architecture_decisions_permanent_across_overwrites_attempt(self, temp_repo, mock_issue_id):
        """Test that architecture decisions remain permanent even after many overwrite attempts."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        coord = VectorCoordinate(x=mock_issue_id(7), y=2, z=1)
        original_content = "Original immutable decision"

        manager.store(coord, original_content)

        # Try to overwrite 100 times
        for i in range(100):
            try:
                manager.store(coord, f"Attempt {i}")
            except ImmutableLayerError:
                pass  # Expected

        # Original should still be there
        decision = manager.get(coord)
        assert decision.content == original_content
