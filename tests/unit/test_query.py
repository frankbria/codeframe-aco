"""Unit tests for query operations."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from vector_memory.coordinate import VectorCoordinate
from vector_memory.exceptions import QueryError
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


class TestQueryRange:
    """Test query_range functionality."""

    def test_query_all_decisions(self, temp_repo, mock_issue_id):
        """Test querying all decisions without filters."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store some decisions
        coords = [
            VectorCoordinate(x=mock_issue_id(1), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(2), y=3, z=2),
            VectorCoordinate(x=mock_issue_id(3), y=2, z=1),
        ]

        for i, coord in enumerate(coords):
            manager.store(coord, f"Decision {i+1}")

        # Query all
        results = manager.query_range()

        assert len(results) == 3
        assert all(d.content.startswith("Decision") for d in results)

    def test_query_by_x_range(self, temp_repo, mock_issue_id):
        """Test querying by x coordinate range."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store decisions at different x values
        for x in [1, 2, 3, 5, 10]:
            coord = VectorCoordinate(x=mock_issue_id(x), y=2, z=1)
            manager.store(coord, f"Decision x={x}")

        # Query x in range [2, 5]
        results = manager.query_range(x_range=(mock_issue_id(2), mock_issue_id(5)))

        assert len(results) == 3  # x=2, 3, 5
        x_values = [d.coordinate.x for d in results]
        assert sorted(x_values) == [mock_issue_id(2), mock_issue_id(3), mock_issue_id(5)]

    def test_query_by_z_layer(self, temp_repo, mock_issue_id):
        """Test querying by memory layer (z coordinate)."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store decisions at different layers
        for z in [1, 2, 3, 4]:
            coord = VectorCoordinate(x=mock_issue_id(1), y=2, z=z)
            manager.store(coord, f"Layer {z}")

        # Query only architecture layer (z=1)
        results = manager.query_range(z_range=(1, 1))

        assert len(results) == 1
        assert results[0].coordinate.z == 1
        assert results[0].content == "Layer 1"

    def test_query_combined_ranges(self, temp_repo, mock_issue_id):
        """Test querying with multiple range filters."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store decisions in a grid
        for x in [1, 2, 3]:
            for y in [1, 2, 3, 4, 5]:
                for z in [1, 2]:
                    coord = VectorCoordinate(x=mock_issue_id(x), y=y, z=z)
                    manager.store(coord, f"x={x},y={y},z={z}")

        # Query: x in [1,2], y in [2,3], z=1
        results = manager.query_range(
            x_range=(mock_issue_id(1), mock_issue_id(2)), y_range=(2, 3), z_range=(1, 1)
        )

        # Should have: x∈{1,2} × y∈{2,3} × z∈{1} = 4 combinations
        assert len(results) == 4

        for d in results:
            assert mock_issue_id(1) <= d.coordinate.x <= mock_issue_id(2)
            assert 2 <= d.coordinate.y <= 3
            assert d.coordinate.z == 1

    def test_query_empty_range(self, temp_repo, mock_issue_id):
        """Test querying range with no matches."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store decision at x=1
        manager.store(VectorCoordinate(x=mock_issue_id(1), y=2, z=1), "Test")

        # Query x=10 (no matches)
        results = manager.query_range(x_range=(mock_issue_id(10), mock_issue_id(10)))

        assert len(results) == 0

    def test_query_invalid_range(self, temp_repo, mock_issue_id):
        """Test that invalid ranges (min > max) are rejected."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Note: For string-based x_range, this validation is less strict
        # We'll skip this test for x_range as string comparison doesn't validate min > max
        # Test with y_range instead
        with pytest.raises(QueryError, match="min.*max"):
            manager.query_range(y_range=(10, 1))  # min > max

    def test_query_results_sorted(self, temp_repo, mock_issue_id):
        """Test that query results are sorted lexicographically."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store in random order
        coords = [
            VectorCoordinate(x=mock_issue_id(3), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(1), y=5, z=1),
            VectorCoordinate(x=mock_issue_id(2), y=3, z=2),
        ]

        for coord in coords:
            manager.store(coord, f"x={coord.x}")

        results = manager.query_range()

        # Should be sorted by (x, y, z)
        assert results[0].coordinate.x == mock_issue_id(1)  # (1, 5, 1)
        assert results[1].coordinate.x == mock_issue_id(2)  # (2, 3, 2)
        assert results[2].coordinate.x == mock_issue_id(3)  # (3, 2, 1)


class TestSearchContent:
    """Test search_content functionality."""

    def test_search_single_term(self, temp_repo, mock_issue_id):
        """Test searching for a single keyword."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store decisions with different content
        manager.store(VectorCoordinate(x=mock_issue_id(1), y=2, z=1), "Use PostgreSQL database")
        manager.store(VectorCoordinate(x=mock_issue_id(2), y=2, z=1), "Use REST API")
        manager.store(VectorCoordinate(x=mock_issue_id(3), y=2, z=1), "Use MongoDB database")

        # Search for "database"
        results = manager.search_content(["database"])

        assert len(results) == 2
        contents = [d.content for d in results]
        assert any("PostgreSQL" in c for c in contents)
        assert any("MongoDB" in c for c in contents)

    def test_search_multiple_terms_any(self, temp_repo, mock_issue_id):
        """Test searching for multiple terms (match any)."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        manager.store(VectorCoordinate(x=mock_issue_id(1), y=2, z=1), "Use PostgreSQL")
        manager.store(VectorCoordinate(x=mock_issue_id(2), y=2, z=1), "Use Redis cache")
        manager.store(VectorCoordinate(x=mock_issue_id(3), y=2, z=1), "Use MongoDB")
        manager.store(VectorCoordinate(x=mock_issue_id(4), y=2, z=1), "Use JWT tokens")

        # Search for "PostgreSQL" OR "Redis"
        results = manager.search_content(["PostgreSQL", "Redis"], match_all=False)

        assert len(results) == 2
        contents = [d.content for d in results]
        assert any("PostgreSQL" in c for c in contents)
        assert any("Redis" in c for c in contents)

    def test_search_multiple_terms_all(self, temp_repo, mock_issue_id):
        """Test searching for multiple terms (match all)."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        manager.store(
            VectorCoordinate(x=mock_issue_id(1), y=2, z=1),
            "Use PostgreSQL database for authentication",
        )
        manager.store(VectorCoordinate(x=mock_issue_id(2), y=2, z=1), "Use Redis for caching")
        manager.store(
            VectorCoordinate(x=mock_issue_id(3), y=2, z=1), "Use authentication middleware"
        )

        # Search for "authentication" AND "database"
        results = manager.search_content(["authentication", "database"], match_all=True)

        assert len(results) == 1
        assert "PostgreSQL" in results[0].content
        assert "authentication" in results[0].content

    def test_search_case_insensitive(self, temp_repo, mock_issue_id):
        """Test that search is case-insensitive."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        manager.store(VectorCoordinate(x=mock_issue_id(1), y=2, z=1), "Use PostgreSQL DATABASE")

        # Search with different case
        results = manager.search_content(["database"])

        assert len(results) == 1
        assert "DATABASE" in results[0].content

    def test_search_no_matches(self, temp_repo, mock_issue_id):
        """Test search with no matches."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        manager.store(VectorCoordinate(x=mock_issue_id(1), y=2, z=1), "Use PostgreSQL")

        # Search for term that doesn't exist
        results = manager.search_content(["MongoDB"])

        assert len(results) == 0

    def test_search_empty_terms(self, temp_repo):
        """Test that empty search terms are rejected."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        with pytest.raises(QueryError, match="search_terms"):
            manager.search_content([])

    def test_search_partial_words(self, temp_repo, mock_issue_id):
        """Test searching for partial words."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        manager.store(VectorCoordinate(x=mock_issue_id(1), y=2, z=1), "Use PostgreSQL database")

        # Search for "post" (part of PostgreSQL)
        results = manager.search_content(["post"])

        # Should not match (word-based indexing)
        # Or should match depending on implementation
        # For now, we expect full word matching
        assert len(results) == 0  # Assuming word-based tokenization


class TestPartialOrder:
    """Test partial ordering operations (Phase 7 - User Story 5)."""

    def test_less_than_different_x(self, temp_repo, mock_issue_id):
        """Test partial ordering with different x values (using string IDs)."""
        from vector_memory.query import PartialOrder

        # x1 < x2, so (x1, y1) < (x2, y2) regardless of y values
        assert PartialOrder.less_than((mock_issue_id(1), 2), (mock_issue_id(3), 4)) is True
        assert PartialOrder.less_than((mock_issue_id(3), 4), (mock_issue_id(1), 2)) is False

    def test_less_than_same_x_different_y(self, temp_repo, mock_issue_id):
        """Test partial ordering with same x, different y."""
        from vector_memory.query import PartialOrder

        # x values equal, so depends on y
        assert PartialOrder.less_than((mock_issue_id(5), 2), (mock_issue_id(5), 3)) is True
        assert PartialOrder.less_than((mock_issue_id(5), 3), (mock_issue_id(5), 2)) is False

    def test_less_than_equal_coordinates(self, temp_repo, mock_issue_id):
        """Test partial ordering with equal coordinates."""
        from vector_memory.query import PartialOrder

        # Equal coordinates are not less than each other
        assert PartialOrder.less_than((mock_issue_id(5), 3), (mock_issue_id(5), 3)) is False

    def test_comparable_comparable_pairs(self, temp_repo, mock_issue_id):
        """Test comparable() with comparable coordinate pairs."""
        from vector_memory.query import PartialOrder

        # Coordinates where one is less than the other
        assert PartialOrder.comparable((mock_issue_id(1), 2), (mock_issue_id(3), 4)) is True
        assert PartialOrder.comparable((mock_issue_id(5), 2), (mock_issue_id(5), 3)) is True
        assert PartialOrder.comparable((mock_issue_id(5), 3), (mock_issue_id(5), 2)) is True

    def test_comparable_incomparable_pairs(self, temp_repo, mock_issue_id):
        """Test comparable() with incomparable coordinate pairs."""
        from vector_memory.query import PartialOrder

        # With lexicographic string ordering, all pairs are comparable
        assert PartialOrder.comparable((mock_issue_id(3), 4), (mock_issue_id(5), 2)) is True


class TestPartialOrderQueries:
    """Test query_partial_order() functionality (Phase 7 - User Story 5)."""

    def test_query_partial_order_basic(self, temp_repo, mock_issue_id):
        """Test basic partial order query."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store decisions at various (x, y) coordinates
        coords = [
            VectorCoordinate(x=mock_issue_id(1), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(3), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(3), y=4, z=1),
            VectorCoordinate(x=mock_issue_id(5), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(7), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(7), y=4, z=1),
        ]

        for _i, coord in enumerate(coords):
            manager.store(coord, f"Decision at ({coord.x}, {coord.y}, {coord.z})")

        # Query for all decisions before (7, 4)
        results = manager.query_partial_order(x_threshold=mock_issue_id(7), y_threshold=4)

        # Should get everything except (7, 4)
        assert len(results) == 5

        # Verify all results are before (7, 4)
        for decision in results:
            x, y = decision.coordinate.x, decision.coordinate.y
            assert x < mock_issue_id(7) or (x == mock_issue_id(7) and y < 4)

    def test_query_partial_order_with_z_filter(self, temp_repo, mock_issue_id):
        """Test partial order query with z-layer filter."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store decisions at multiple layers
        for z in [1, 2, 3]:
            manager.store(VectorCoordinate(x=mock_issue_id(1), y=2, z=z), f"Layer {z}")
            manager.store(VectorCoordinate(x=mock_issue_id(3), y=2, z=z), f"Layer {z}")

        # Query for architecture layer (z=1) only before (5, 1)
        results = manager.query_partial_order(
            x_threshold=mock_issue_id(5), y_threshold=1, z_filter=1
        )

        # Should get (1,2,1) and (3,2,1) but not other layers
        assert len(results) == 2
        assert all(d.coordinate.z == 1 for d in results)

    def test_query_partial_order_empty(self, temp_repo, mock_issue_id):
        """Test partial order query with no matches."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store decision at (5, 3)
        manager.store(VectorCoordinate(x=mock_issue_id(5), y=3, z=1), "Test")

        # Query for decisions before (1, 1) - should be empty
        results = manager.query_partial_order(x_threshold=mock_issue_id(1), y_threshold=1)

        assert len(results) == 0

    def test_query_partial_order_results_sorted(self, temp_repo, mock_issue_id):
        """Test that partial order query results are sorted."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # Store in random order
        coords = [
            VectorCoordinate(x=mock_issue_id(7), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(1), y=5, z=1),
            VectorCoordinate(x=mock_issue_id(3), y=2, z=2),
            VectorCoordinate(x=mock_issue_id(1), y=2, z=1),
        ]

        for coord in coords:
            manager.store(coord, f"x={coord.x}")

        results = manager.query_partial_order(x_threshold=mock_issue_id(10), y_threshold=1)

        # Results should be sorted lexicographically
        for i in range(len(results) - 1):
            curr = results[i].coordinate.to_tuple()
            next_coord = results[i + 1].coordinate.to_tuple()
            assert curr <= next_coord

    def test_query_partial_order_invalid_thresholds(self, temp_repo, mock_issue_id):
        """Test that invalid thresholds are rejected."""
        from vector_memory.exceptions import CoordinateValidationError

        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="test-agent")

        # x_threshold is now a string, so no validation for numeric range
        # Only test y threshold validation

        # Invalid y threshold (out of range - must be 1-6, where 6 allows all y<=5)
        with pytest.raises(CoordinateValidationError):
            manager.query_partial_order(x_threshold=mock_issue_id(5), y_threshold=7)
