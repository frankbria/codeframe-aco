"""Test that all examples from quickstart.md work correctly."""

import tempfile
from pathlib import Path

import pytest

from vector_memory import VectorMemoryManager, VectorCoordinate
from vector_memory.exceptions import ImmutableLayerError


class TestQuickstartExamples:
    """Validate all code examples from quickstart.md."""

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

    def test_quickstart_example_1_initialize(self, temp_repo):
        """Test: Initialize the Manager example."""
        # From quickstart.md section "1. Initialize the Manager"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="claude-code-01")

        assert manager is not None
        assert manager.agent_id == "claude-code-01"

    def test_quickstart_example_2_store_decision(self, temp_repo):
        """Test: Store a Decision example."""
        # From quickstart.md section "2. Store a Decision"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="claude-code-01")

        coord = VectorCoordinate(x=5, y=2, z=1)

        decision = manager.store(
            coord=coord,
            content="Use PostgreSQL for persistence layer",
            issue_context={"issue_id": "codeframe-aco-t49", "issue_title": "Vector Memory Manager"},
        )

        assert decision is not None
        assert decision.content == "Use PostgreSQL for persistence layer"

    def test_quickstart_example_3_retrieve_decision(self, temp_repo):
        """Test: Retrieve a Decision example."""
        # From quickstart.md section "3. Retrieve a Decision"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="claude-code-01")

        coord = VectorCoordinate(x=5, y=2, z=1)
        manager.store(
            coord=coord,
            content="Use PostgreSQL for persistence layer",
            issue_context={"issue_id": "codeframe-aco-t49"},
        )

        decision = manager.get(coord)

        assert decision is not None
        assert decision.content == "Use PostgreSQL for persistence layer"
        assert decision.agent_id == "claude-code-01"
        assert decision.timestamp is not None

    def test_quickstart_example_4_sync_to_git(self, temp_repo):
        """Test: Sync to Git example."""
        # From quickstart.md section "4. Sync to Git"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="claude-code-01")

        coord = VectorCoordinate(x=5, y=2, z=1)
        manager.store(coord=coord, content="Test decision", issue_context={"issue_id": "test-5"})

        manager.sync(message="Store architecture decisions for issue 5")

        # Verify sync worked
        assert (temp_repo / ".vector-memory").exists()

    def test_use_case_1_store_architectural_decision(self, temp_repo):
        """Test: Use Case 1 - Store Architectural Decision."""
        # From quickstart.md "Use Case 1"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="claude-code-01")

        coord = VectorCoordinate(x=10, y=2, z=1)
        manager.store(coord, "Use REST API with JSON for all endpoints")

        # Verify it's stored
        decision = manager.get(coord)
        assert decision is not None
        assert "REST API" in decision.content

        # Try to modify (should fail for z=1)
        with pytest.raises(ImmutableLayerError):
            manager.store(coord, "Modified decision")

    def test_use_case_2_query_architecture_decisions(self, temp_repo):
        """Test: Use Case 2 - Query Architecture Decisions."""
        # From quickstart.md "Use Case 2"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="claude-code-01")

        # Store decisions for issues 1-20
        for x in range(1, 21):
            coord = VectorCoordinate(x=x, y=2, z=1)
            manager.store(
                coord=coord,
                content=f"Architecture decision for issue {x}",
                issue_context={"issue_id": f"test-{x}"},
            )

        # Query all architecture decisions
        arch_decisions = manager.query_range(x_range=(1, 20), z_range=(1, 1))

        assert len(arch_decisions) == 20
        for decision in arch_decisions:
            assert decision.coordinate.z == 1
            assert "Architecture decision" in decision.content

    def test_use_case_3_find_decisions_for_rollback(self, temp_repo):
        """Test: Use Case 3 - Find Decisions for Rollback."""
        # From quickstart.md "Use Case 3"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="claude-code-01")

        # Store some decisions
        for x in [1, 5, 10, 15, 20]:
            for y in [1, 2, 3]:
                coord = VectorCoordinate(x=x, y=y, z=2)
                manager.store(
                    coord=coord,
                    content=f"Decision at ({x}, {y})",
                    issue_context={"issue_id": f"test-{x}"},
                )

        # Error occurred at issue 15, implement stage
        decisions_before = manager.query_partial_order(x_threshold=15, y_threshold=3)

        # Should include all decisions before (15, 3)
        assert len(decisions_before) > 0
        for decision in decisions_before:
            x, y, z = decision.coordinate.to_tuple()
            # All should satisfy (x, y) < (15, 3)
            assert x < 15 or (x == 15 and y < 3)

    def test_use_case_4_search_for_specific_topics(self, temp_repo):
        """Test: Use Case 4 - Search for Specific Topics."""
        # From quickstart.md "Use Case 4"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="claude-code-01")

        # Store decisions with database keywords
        manager.store(
            VectorCoordinate(x=1, y=2, z=1),
            "Use PostgreSQL database for storage",
            issue_context={"issue_id": "test-1"},
        )
        manager.store(
            VectorCoordinate(x=2, y=2, z=1),
            "Database schema with users table",
            issue_context={"issue_id": "test-2"},
        )
        manager.store(
            VectorCoordinate(x=3, y=2, z=2),
            "API endpoint for fetching data",
            issue_context={"issue_id": "test-3"},
        )

        # Search for database decisions
        db_decisions = manager.search_content(["database", "PostgreSQL", "SQL"])

        assert len(db_decisions) >= 2
        for decision in db_decisions:
            content_lower = decision.content.lower()
            assert "database" in content_lower or "postgresql" in content_lower

    def test_use_case_5_update_implementation_details(self, temp_repo):
        """Test: Use Case 5 - Update Implementation Details."""
        # From quickstart.md "Use Case 5"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="claude-code-01")

        coord = VectorCoordinate(x=10, y=3, z=3)

        # First version
        manager.store(coord, "Use simple linear search")
        manager.sync()

        # Verify first version
        decision1 = manager.get(coord)
        assert "linear search" in decision1.content

        # Later, optimize (z=3 is mutable)
        manager.store(coord, "Use binary search for better performance")
        manager.sync()

        # Verify update
        decision2 = manager.get(coord)
        assert "binary search" in decision2.content
        assert decision2.content != decision1.content

    def test_pattern_start_of_new_issue(self, temp_repo):
        """Test: Pattern - Start of New Issue."""
        # From quickstart.md "Pattern: Start of New Issue"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="claude-code-01")

        issue_num = 42

        # Store architectural decisions early
        arch_coord = VectorCoordinate(x=issue_num, y=2, z=1)
        manager.store(arch_coord, "Follow REST API patterns from issue #5")

        # Store test decisions
        test_coord = VectorCoordinate(x=issue_num, y=2, z=2)
        manager.store(test_coord, "Test all endpoints with integration tests")

        # Sync before implementation
        manager.sync()

        # Verify both decisions exist
        arch_decision = manager.get(arch_coord)
        test_decision = manager.get(test_coord)

        assert arch_decision is not None
        assert test_decision is not None

    def test_pattern_context_retrieval_for_new_agent(self, temp_repo):
        """Test: Pattern - Context Retrieval for New Agent."""
        # From quickstart.md "Pattern: Context Retrieval for New Agent"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="setup")

        # Store architecture decisions for issues 1-49
        for x in range(1, 50):
            coord = VectorCoordinate(x=x, y=2, z=1)
            manager.store(
                coord=coord,
                content=f"Architecture for issue {x}",
                issue_context={"issue_id": f"test-{x}"},
            )

        # Agent starting on issue 50 needs context
        context = manager.query_range(x_range=(1, 49), z_range=(1, 1))

        # Build context string
        context_text = "\n".join([f"Issue {d.coordinate.x}: {d.content}" for d in context])

        assert len(context) == 49
        assert "Issue 1:" in context_text
        assert "Issue 49:" in context_text

    def test_error_handling_immutable_layer_error(self, temp_repo):
        """Test: Error Handling - ImmutableLayerError."""
        # From quickstart.md "Error Handling"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="claude-code-01")

        coord = VectorCoordinate(x=5, y=2, z=1)
        manager.store(coord, "Original decision")

        # Try to modify immutable layer
        with pytest.raises(ImmutableLayerError):
            manager.store(coord, "Modified decision")

        # Solution: Store at different coordinate
        new_coord = VectorCoordinate(x=10, y=2, z=1)
        manager.store(new_coord, "New decision superseding old one")

        # Verify both exist
        assert manager.exists(coord)
        assert manager.exists(new_coord)

    def test_coordinate_system_layers(self, temp_repo):
        """Test: Coordinate System - Memory Layers."""
        # From quickstart.md "Z-Axis: Memory Layers"
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test")

        # Test each layer
        layers = {
            1: ("Architecture", "Foundational decision", False),  # Immutable
            2: ("Interfaces", "API contract", True),  # Mutable
            3: ("Implementation", "Code detail", True),  # Mutable
            4: ("Ephemeral", "Temporary note", True),  # Mutable
        }

        for z, (name, content, is_mutable) in layers.items():
            coord = VectorCoordinate(x=1, y=2, z=z)
            manager.store(coord, content)

            # Verify stored
            decision = manager.get(coord)
            assert decision is not None

            # Test mutability
            if is_mutable:
                # Should allow overwrite
                manager.store(coord, f"Updated {content}")
                updated = manager.get(coord)
                assert "Updated" in updated.content
            else:
                # Should not allow overwrite
                with pytest.raises(ImmutableLayerError):
                    manager.store(coord, f"Updated {content}")
