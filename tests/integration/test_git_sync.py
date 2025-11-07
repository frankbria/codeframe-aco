"""Integration tests for Git synchronization."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from vector_memory.coordinate import VectorCoordinate
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


class TestGitSync:
    """Test Git synchronization functionality."""

    def test_sync_creates_commit(self, temp_repo):
        """Test that sync() creates a Git commit."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store some decisions
        manager.store(VectorCoordinate(x=1, y=2, z=1), "Decision 1")
        manager.store(VectorCoordinate(x=2, y=2, z=1), "Decision 2")

        # Sync to Git
        manager.sync(message="Test commit message")

        # Verify commit was created
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Test commit message" in result.stdout or "vector-memory" in result.stdout

    def test_sync_includes_vector_memory_files(self, temp_repo):
        """Test that sync() commits .vector-memory/ files."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store decision
        coord = VectorCoordinate(x=5, y=2, z=1)
        manager.store(coord, "Architecture decision")

        # Sync
        manager.sync()

        # Verify files are tracked in Git
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )

        assert ".vector-memory" in result.stdout

    def test_load_from_git_after_restart(self, temp_repo):
        """Test that decisions persist across manager instances."""
        coord = VectorCoordinate(x=5, y=2, z=1)

        # First session: store and sync
        manager1 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-1")
        manager1.store(coord, "Persisted decision")
        manager1.sync()

        # Second session: load from Git
        manager2 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-2")

        # Should load the decision from Git
        decision = manager2.get(coord)
        assert decision is not None
        assert decision.content == "Persisted decision"

    def test_sync_multiple_times(self, temp_repo):
        """Test syncing multiple times creates multiple commits."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # First sync
        manager.store(VectorCoordinate(x=1, y=2, z=1), "First")
        manager.sync(message="First commit")

        # Second sync
        manager.store(VectorCoordinate(x=2, y=2, z=1), "Second")
        manager.sync(message="Second commit")

        # Third sync
        manager.store(VectorCoordinate(x=3, y=2, z=1), "Third")
        manager.sync(message="Third commit")

        # Verify all commits exist
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )

        commits = result.stdout.strip().split("\n")
        # Should have at least 3 commits
        assert len(commits) >= 3

    def test_sync_with_custom_message(self, temp_repo):
        """Test that custom commit messages are used."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        manager.store(VectorCoordinate(x=1, y=2, z=1), "Test")

        custom_message = "Custom commit: added architecture decisions"
        manager.sync(message=custom_message)

        # Verify custom message is in Git log
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )

        assert custom_message in result.stdout

    def test_sync_without_custom_message(self, temp_repo):
        """Test that sync generates default message when none provided."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        manager.store(VectorCoordinate(x=1, y=2, z=1), "Test")
        manager.sync()  # No custom message

        # Verify default message is generated
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )

        # Should have some automatic message about vector-memory
        assert "vector-memory" in result.stdout.lower() or "decision" in result.stdout.lower()

    def test_load_from_git_initializes_index(self, temp_repo):
        """Test that load_from_git() rebuilds the index correctly."""
        # First session: store decisions
        manager1 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-1")

        coords = [
            VectorCoordinate(x=1, y=2, z=1),
            VectorCoordinate(x=2, y=3, z=2),
            VectorCoordinate(x=3, y=2, z=1),
        ]

        for coord in coords:
            manager1.store(coord, f"Decision at {coord.to_tuple()}")

        manager1.sync()

        # Second session: load from Git
        manager2 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-2")

        # All decisions should be accessible
        for coord in coords:
            assert manager2.exists(coord)
            decision = manager2.get(coord)
            assert decision is not None

    def test_recovery_after_crash(self, temp_repo):
        """Test that system recovers from crash by loading from Git."""
        # Store and sync decisions
        manager1 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-1")

        for x in range(1, 6):
            coord = VectorCoordinate(x=x, y=2, z=1)
            manager1.store(coord, f"Decision {x}")

        manager1.sync()

        # Simulate crash: create new manager instance
        manager2 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-2")

        # Verify all data is recovered
        recovered_count = manager2.load_from_git()
        assert recovered_count == 5

        # Verify decisions are accessible
        for x in range(1, 6):
            coord = VectorCoordinate(x=x, y=2, z=1)
            decision = manager2.get(coord)
            assert decision is not None
            assert decision.content == f"Decision {x}"


class TestGitIntegration:
    """Test Git integration edge cases."""

    def test_sync_empty_changes(self, temp_repo):
        """Test syncing when there are no new changes."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store and sync
        manager.store(VectorCoordinate(x=1, y=2, z=1), "Test")
        manager.sync()

        # Get commit count
        result1 = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )
        count1 = int(result1.stdout.strip())

        # Sync again without changes
        manager.sync()

        # Commit count should not increase (or handle gracefully)
        result2 = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )
        count2 = int(result2.stdout.strip())

        # Either no new commit or handled gracefully
        assert count2 == count1 or count2 == count1 + 1

    def test_load_from_empty_repository(self, temp_repo):
        """Test loading when .vector-memory/ doesn't exist yet."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Load from empty Git
        count = manager.load_from_git()

        # Should return 0 (no decisions)
        assert count == 0

    def test_concurrent_access_same_repo(self, temp_repo):
        """Test that multiple managers can work with same repo."""
        # Manager 1 stores some decisions
        manager1 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-1")
        manager1.store(VectorCoordinate(x=1, y=2, z=1), "From agent 1")
        manager1.sync()

        # Manager 2 stores different decisions
        manager2 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-2")
        manager2.store(VectorCoordinate(x=2, y=2, z=1), "From agent 2")
        manager2.sync()

        # Manager 3 should see both decisions
        manager3 = VectorMemoryManager(repo_path=temp_repo, agent_id="agent-3")

        decision1 = manager3.get(VectorCoordinate(x=1, y=2, z=1))
        decision2 = manager3.get(VectorCoordinate(x=2, y=2, z=1))

        assert decision1 is not None
        assert decision2 is not None
        assert decision1.agent_id == "agent-1"
        assert decision2.agent_id == "agent-2"
