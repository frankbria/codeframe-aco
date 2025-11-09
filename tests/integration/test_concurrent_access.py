"""Integration tests for concurrent access to VectorMemoryManager."""

import tempfile
import threading
from pathlib import Path

import pytest

from vector_memory import VectorCoordinate, VectorMemoryManager
from vector_memory.exceptions import ImmutableLayerError


class TestConcurrentAccess:
    """Test concurrent access patterns with VectorMemoryManager."""

    @pytest.fixture
    def temp_repo(self):
        """Create temporary repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            # Initialize git repo
            import subprocess

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

    def test_concurrent_stores_different_coordinates(self, temp_repo, mock_issue_id):
        """Test multiple agents storing to different coordinates concurrently."""
        errors = []
        stored_coords = []

        def agent_store(agent_id: str, start_x: int, count: int):
            try:
                manager = VectorMemoryManager(repo_path=temp_repo, agent_id=agent_id)
                for i in range(count):
                    coord = VectorCoordinate(x=mock_issue_id(start_x + i), y=2, z=3)
                    decision = manager.store(
                        coord=coord,
                        content=f"Decision from {agent_id} at issue {start_x + i}",
                        issue_context={"issue_id": f"test-{start_x + i}"},
                    )
                    stored_coords.append(decision.coordinate)
            except Exception as e:
                errors.append((agent_id, e))

        # Create 5 agents, each storing 10 decisions
        threads = []
        for i in range(5):
            agent_id = f"agent-{i}"
            t = threading.Thread(target=agent_store, args=(agent_id, i * 10 + 1, 10))
            threads.append(t)
            t.start()

        # Wait for all agents
        for t in threads:
            t.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Check all 50 coordinates were stored
        assert len(stored_coords) == 50

        # Verify all decisions can be retrieved
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="verifier")
        for coord in stored_coords:
            decision = manager.get(coord)
            assert decision is not None
            assert decision.content != ""

    def test_concurrent_stores_with_immutable_layer(self, temp_repo, mock_issue_id):
        """Test concurrent access to immutable architecture layer."""
        # Note: Each manager instance has its own in-memory index, so they
        # don't see each other's writes until they reload. This test verifies
        # that once persisted, immutability is enforced.

        # First, establish an immutable decision
        setup_manager = VectorMemoryManager(repo_path=temp_repo, agent_id="setup")
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        setup_manager.store(
            coord=coord,
            content="Initial architecture decision",
            issue_context={"issue_id": "test-5"},
        )

        errors = []
        immutable_errors = []

        def try_modify_architecture(agent_id: str):
            try:
                # Fresh manager that loads existing state
                manager = VectorMemoryManager(repo_path=temp_repo, agent_id=agent_id)
                manager.load_from_git()  # Load existing decisions

                # Try to modify immutable coordinate
                manager.store(
                    coord=coord,
                    content=f"Modified decision from {agent_id}",
                    issue_context={"issue_id": "test-5"},
                )
            except ImmutableLayerError:
                # Expected - immutability enforced
                immutable_errors.append(agent_id)
            except Exception as e:
                errors.append((agent_id, e))

        # Create 10 agents trying to write to same architecture coordinate
        threads = []
        for i in range(10):
            agent_id = f"agent-{i}"
            t = threading.Thread(target=try_modify_architecture, args=(agent_id,))
            threads.append(t)
            t.start()

        # Wait for all agents
        for t in threads:
            t.join()

        # Check no unexpected errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # All 10 agents should get immutability errors (since one was already written)
        assert len(immutable_errors) == 10

        # Verify the decision exists and is immutable
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="verifier")
        decision = manager.get(coord)
        assert decision is not None

    def test_concurrent_read_while_writing(self, temp_repo, mock_issue_id):
        """Test concurrent reads while writing."""
        # Pre-populate some decisions
        setup_manager = VectorMemoryManager(repo_path=temp_repo, agent_id="setup")
        for x in range(1, 21):
            coord = VectorCoordinate(x=mock_issue_id(x), y=2, z=2)
            setup_manager.store(
                coord=coord,
                content=f"Decision for issue {x}",
                issue_context={"issue_id": f"test-{x}"},
            )

        errors = []
        read_counts = []

        def writer_agent(count: int):
            try:
                manager = VectorMemoryManager(repo_path=temp_repo, agent_id="writer")
                for i in range(count):
                    coord = VectorCoordinate(x=mock_issue_id(21 + i), y=2, z=2)
                    manager.store(
                        coord=coord,
                        content=f"New decision {i}",
                        issue_context={"issue_id": f"new-{i}"},
                    )
            except Exception as e:
                errors.append(("writer", e))

        def reader_agent(iterations: int):
            try:
                manager = VectorMemoryManager(repo_path=temp_repo, agent_id="reader")
                for _ in range(iterations):
                    decisions = manager.query_range(
                        x_range=(mock_issue_id(1), mock_issue_id(50)), z_range=(2, 2)
                    )
                    read_counts.append(len(decisions))
            except Exception as e:
                errors.append(("reader", e))

        # Start one writer and three readers
        writer = threading.Thread(target=writer_agent, args=(30,))
        readers = [threading.Thread(target=reader_agent, args=(20,)) for _ in range(3)]

        writer.start()
        for r in readers:
            r.start()

        writer.join()
        for r in readers:
            r.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Readers should have seen between 20 and 50 decisions
        assert all(20 <= count <= 50 for count in read_counts)

        # Final count should be 50
        final_manager = VectorMemoryManager(repo_path=temp_repo, agent_id="final")
        final_decisions = final_manager.query_range(
            x_range=(mock_issue_id(1), mock_issue_id(50)), z_range=(2, 2)
        )
        assert len(final_decisions) == 50

    def test_concurrent_query_operations(self, temp_repo, mock_issue_id):
        """Test multiple concurrent query operations."""
        # Setup data
        setup_manager = VectorMemoryManager(repo_path=temp_repo, agent_id="setup")
        for x in range(1, 51):
            for z in [1, 2, 3]:
                coord = VectorCoordinate(x=mock_issue_id(x), y=2, z=z)
                setup_manager.store(
                    coord=coord,
                    content=f"Decision at x={x}, z={z}",
                    issue_context={"issue_id": f"test-{x}"},
                )

        errors = []
        query_results = {
            "range": [],
            "partial_order": [],
            "search": [],
        }

        def range_query_agent(iterations: int):
            try:
                manager = VectorMemoryManager(repo_path=temp_repo, agent_id="range-query")
                for _ in range(iterations):
                    results = manager.query_range(
                        x_range=(mock_issue_id(1), mock_issue_id(25)), z_range=(1, 1)
                    )
                    query_results["range"].append(len(results))
            except Exception as e:
                errors.append(("range-query", e))

        def partial_order_agent(iterations: int):
            try:
                manager = VectorMemoryManager(repo_path=temp_repo, agent_id="partial-order")
                for _ in range(iterations):
                    results = manager.query_partial_order(
                        x_threshold=mock_issue_id(30), y_threshold=3
                    )
                    query_results["partial_order"].append(len(results))
            except Exception as e:
                errors.append(("partial-order", e))

        def search_agent(iterations: int):
            try:
                manager = VectorMemoryManager(repo_path=temp_repo, agent_id="search")
                for _ in range(iterations):
                    results = manager.search_content(["decision"], match_all=False)
                    query_results["search"].append(len(results))
            except Exception as e:
                errors.append(("search", e))

        # Create query threads
        threads = [
            threading.Thread(target=range_query_agent, args=(30,)),
            threading.Thread(target=partial_order_agent, args=(30,)),
            threading.Thread(target=search_agent, args=(30,)),
        ]

        # Start all
        for t in threads:
            t.start()

        # Wait for all
        for t in threads:
            t.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # All queries should return consistent results (no writes happening)
        assert all(c == query_results["range"][0] for c in query_results["range"])
        assert all(c == query_results["partial_order"][0] for c in query_results["partial_order"])
        assert all(c == query_results["search"][0] for c in query_results["search"])

    def test_concurrent_exists_checks(self, temp_repo, mock_issue_id):
        """Test concurrent exists() checks work correctly."""
        # Pre-populate some coordinates
        setup_manager = VectorMemoryManager(repo_path=temp_repo, agent_id="setup")
        for x in [1, 3, 5, 7, 9]:
            coord = VectorCoordinate(x=mock_issue_id(x), y=2, z=2)
            setup_manager.store(
                coord=coord,
                content=f"Decision {x}",
                issue_context={"issue_id": f"test-{x}"},
            )

        errors = []
        exists_counts = []

        def checker_agent(agent_id: str, iterations: int):
            try:
                manager = VectorMemoryManager(repo_path=temp_repo, agent_id=agent_id)
                manager.load_from_git()  # Load existing decisions

                exists_count = 0
                # Check coordinates 1-10
                for x in range(1, 11):
                    coord = VectorCoordinate(x=mock_issue_id(x), y=2, z=2)
                    if manager.exists(coord):
                        exists_count += 1

                exists_counts.append(exists_count)
            except Exception as e:
                errors.append((agent_id, e))

        # Create 5 agents, each checking 10 times
        threads = []
        for i in range(5):
            agent_id = f"agent-{i}"
            t = threading.Thread(target=checker_agent, args=(agent_id, 10))
            threads.append(t)
            t.start()

        # Wait for all agents
        for t in threads:
            t.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify counts are correct
        assert all(count == 5 for count in exists_counts)

    def test_file_locking_prevents_corruption(self, temp_repo, mock_issue_id):
        """Test that file locking prevents data corruption."""
        coord = VectorCoordinate(x=mock_issue_id(15), y=2, z=3)

        errors = []
        stored_agents = []

        def concurrent_writer(agent_id: str):
            try:
                manager = VectorMemoryManager(repo_path=temp_repo, agent_id=agent_id)
                manager.store(
                    coord=coord,
                    content=f"Decision from {agent_id}",
                    issue_context={"issue_id": "test-15"},
                )
                stored_agents.append(agent_id)
            except Exception as e:
                errors.append((agent_id, e))

        # Create 10 writers trying to write to same coordinate
        threads = []
        for i in range(10):
            agent_id = f"agent-{i}"
            t = threading.Thread(target=concurrent_writer, args=(agent_id,))
            threads.append(t)
            t.start()

        # Wait for all
        for t in threads:
            t.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # All agents should have written (last one wins)
        assert len(stored_agents) == 10

        # Verify file is not corrupted
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="verifier")
        decision = manager.get(coord)
        assert decision is not None
        assert decision.content.startswith("Decision from agent-")
        # agent_id should be one of the writers
        assert decision.agent_id in [f"agent-{i}" for i in range(10)]

    def test_multiple_managers_same_repo(self, temp_repo, mock_issue_id):
        """Test multiple manager instances accessing same repository."""
        errors = []
        stored_decisions = []

        def agent_with_own_manager(agent_id: str, start_x: int, count: int):
            try:
                # Each agent creates its own manager instance
                manager = VectorMemoryManager(repo_path=temp_repo, agent_id=agent_id)

                for i in range(count):
                    coord = VectorCoordinate(x=mock_issue_id(start_x + i), y=2, z=2)
                    decision = manager.store(
                        coord=coord,
                        content=f"Decision from {agent_id}",
                        issue_context={"issue_id": f"test-{start_x + i}"},
                    )
                    stored_decisions.append(decision)
            except Exception as e:
                errors.append((agent_id, e))

        # Create 5 agents with separate manager instances
        threads = []
        for i in range(5):
            agent_id = f"agent-{i}"
            t = threading.Thread(target=agent_with_own_manager, args=(agent_id, i * 5 + 1, 5))
            threads.append(t)
            t.start()

        # Wait for all
        for t in threads:
            t.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # All 25 decisions should be stored
        assert len(stored_decisions) == 25

        # Create new manager and verify all decisions present
        verifier = VectorMemoryManager(repo_path=temp_repo, agent_id="verifier")
        all_decisions = verifier.query_range(
            x_range=(mock_issue_id(1), mock_issue_id(25)), z_range=(2, 2)
        )
        assert len(all_decisions) == 25
