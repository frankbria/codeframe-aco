"""Integration tests for DAG-based ordering with non-lexicographic issue IDs."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from vector_memory import VectorCoordinate, VectorMemoryManager


class TestDAGOrdering:
    """Test that dag_order parameter enables correct ordering for non-lexicographic IDs."""

    @pytest.fixture
    def temp_repo(self):
        """Create temporary repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            # Initialize git repo
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

    def test_query_range_with_dag_order(self, temp_repo):
        """Test query_range with non-lexicographic IDs using dag_order."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test")

        # Issue IDs that DON'T sort lexicographically the same as their DAG order
        # Lexicographic: issue-b02 < issue-c03 < issue-d10 < issue-e05
        # DAG order:     issue-b02 (0) < issue-c03 (1) < issue-e05 (2) < issue-d10 (3)
        issue_ids = ["issue-b02", "issue-c03", "issue-e05", "issue-d10"]
        dag_order = {
            "issue-b02": 0,
            "issue-c03": 1,
            "issue-e05": 2,
            "issue-d10": 3,
        }

        # Store decisions
        for idx, issue_id in enumerate(issue_ids):
            coord = VectorCoordinate(x=issue_id, y=2, z=1)
            manager.store(coord, f"Decision for {issue_id}", issue_context={"issue_id": issue_id})

        # Query range WITHOUT dag_order (lexicographic fallback)
        # Lexicographic range: "issue-b02" to "issue-e05"
        # Lex order: issue-b02 < issue-c03 < issue-d10 < issue-e05
        results_lex = manager.query_range(x_range=("issue-b02", "issue-e05"))
        lex_ids = [d.coordinate.x for d in results_lex]

        # With lexicographic comparison, should get all four issues
        assert len(lex_ids) == 4, f"Expected 4 results, got {len(lex_ids)}"
        assert set(lex_ids) == {"issue-b02", "issue-c03", "issue-d10", "issue-e05"}

        # Query range WITH dag_order (topological ordering)
        # DAG range (issue-d10, issue-e05) means positions (3, 2), which is invalid
        # Let's use a valid range: (issue-b02, issue-e05) = positions (0, 2)
        # Should return: issue-b02 (0), issue-c03 (1), issue-e05 (2)
        results_dag = manager.query_range(x_range=("issue-b02", "issue-e05"), dag_order=dag_order)
        dag_ids = [d.coordinate.x for d in results_dag]

        assert dag_ids == [
            "issue-b02",
            "issue-c03",
            "issue-e05",
        ], f"DAG ordering should return [issue-b02, issue-c03, issue-e05], got {dag_ids}"

        # Verify issue-d10 is NOT in the result (it's outside the DAG range)
        assert "issue-d10" not in dag_ids, "issue-d10 should not be in DAG range (0, 2)"

    def test_query_partial_order_with_dag_order(self, temp_repo):
        """Test query_partial_order with non-lexicographic IDs using dag_order."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test")

        # Same non-lexicographic issue IDs
        issue_ids = ["issue-b02", "issue-c03", "issue-e05", "issue-d10"]
        dag_order = {
            "issue-b02": 0,
            "issue-c03": 1,
            "issue-e05": 2,
            "issue-d10": 3,
        }

        # Store decisions at different y positions
        for idx, issue_id in enumerate(issue_ids):
            for y in [1, 2, 3]:
                coord = VectorCoordinate(x=issue_id, y=y, z=1)
                manager.store(coord, f"Decision {issue_id} y={y}")

        # Query partial order WITHOUT dag_order (lexicographic fallback)
        # (x,y) < ("issue-e05", 3) with lexicographic comparison
        results_lex = manager.query_partial_order(x_threshold="issue-e05", y_threshold=3)

        # Query partial order WITH dag_order (topological ordering)
        # (x,y) < ("issue-e05", 3) means position < 2, or (position == 2 and y < 3)
        # Should return: all decisions for issue-b02 (pos 0), issue-c03 (pos 1),
        #                and issue-e05 with y < 3 (pos 2, y in [1, 2])
        results_dag = manager.query_partial_order(
            x_threshold="issue-e05", y_threshold=3, dag_order=dag_order
        )

        dag_coords = [(d.coordinate.x, d.coordinate.y) for d in results_dag]

        # Should include all y values for issue-b02 and issue-c03
        assert ("issue-b02", 1) in dag_coords
        assert ("issue-b02", 2) in dag_coords
        assert ("issue-b02", 3) in dag_coords
        assert ("issue-c03", 1) in dag_coords
        assert ("issue-c03", 2) in dag_coords
        assert ("issue-c03", 3) in dag_coords

        # Should include y < 3 for issue-e05
        assert ("issue-e05", 1) in dag_coords
        assert ("issue-e05", 2) in dag_coords
        assert (
            "issue-e05",
            3,
        ) not in dag_coords, "issue-e05 y=3 should be excluded (not < threshold)"

        # Should NOT include any issue-d10 (position 3 > position 2)
        assert not any(
            x == "issue-d10" for x, _ in dag_coords
        ), "issue-d10 should not be in partial order results"

    def test_dag_order_enables_correct_rollback(self, temp_repo):
        """Test that dag_order enables correct rollback for non-sequential IDs."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test")

        # Simulate a DAG where issues were created in this order:
        # issue-a00 (0) -> issue-b01 (1) -> issue-c02 (2) -> issue-d10 (3)
        # But lexicographically: issue-d10 < issue-a00 < issue-b01 < issue-c02
        dag_order = {
            "issue-a00": 0,
            "issue-b01": 1,
            "issue-c02": 2,
            "issue-d10": 3,
        }

        # Store decisions in DAG order
        for issue_id, position in sorted(dag_order.items(), key=lambda x: x[1]):
            coord = VectorCoordinate(x=issue_id, y=2, z=1)
            manager.store(coord, f"Decision at DAG position {position}")

        # Rollback to before issue-c02 y=3 (position 2, y < 3)
        # (x,y) < ("issue-c02", 3) means:
        # - x position < 2 (includes issue-a00, issue-b01)
        # - OR x position == 2 AND y < 3 (includes issue-c02 with y < 3)
        # Since we stored only y=2, issue-c02 y=2 is included
        rollback_decisions = manager.query_partial_order(
            x_threshold="issue-c02", y_threshold=3, dag_order=dag_order
        )

        rollback_ids = {d.coordinate.x for d in rollback_decisions}

        assert "issue-a00" in rollback_ids, "Should include issue-a00 (position 0)"
        assert "issue-b01" in rollback_ids, "Should include issue-b01 (position 1)"
        # issue-c02 IS included because y=2 < y_threshold=3
        assert "issue-c02" in rollback_ids, "Should include issue-c02 y=2 (< threshold y=3)"
        assert "issue-d10" not in rollback_ids, "Should not include issue-d10 (position 3 > 2)"

        # This test demonstrates that dag_order enables correct DAG-based rollback
        # even when issue IDs don't follow sequential naming patterns
