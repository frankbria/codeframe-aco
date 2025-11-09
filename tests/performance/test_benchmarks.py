"""Performance benchmarks for Vector Memory Manager.

Success Criteria from spec.md:
- SC-001: Store/retrieve operations < 50ms (99th percentile)
- SC-004: Handles 10,000 stored decisions
- SC-005: Git sync < 5s for 1000 decisions
- SC-006: Recovery < 10s
- SC-007: Partial ordering queries < 100ms
- SC-008: Content search < 200ms
"""

import tempfile
import time
from pathlib import Path
from statistics import quantiles

import pytest

from vector_memory import VectorCoordinate, VectorMemoryManager


class TestPerformanceBenchmarks:
    """Performance benchmarks to validate success criteria."""

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

    def test_store_operation_performance(self, temp_repo, mock_issue_id):
        """
        SC-001: Store/retrieve operations < 50ms (99th percentile)
        """
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="benchmark")

        # Measure store operations
        store_times = []
        for i in range(1, 101):
            coord = VectorCoordinate(x=mock_issue_id(i), y=2, z=2)

            start = time.perf_counter()
            manager.store(
                coord=coord,
                content=f"Benchmark decision {i}",
                issue_context={"issue_id": f"bench-{i}"},
            )
            end = time.perf_counter()

            store_times.append((end - start) * 1000)  # Convert to ms

        # Calculate percentiles
        p50 = quantiles(store_times, n=100)[49]  # 50th percentile
        p99 = quantiles(store_times, n=100)[98]  # 99th percentile

        print("\nStore Performance:")
        print(f"  50th percentile: {p50:.2f}ms")
        print(f"  99th percentile: {p99:.2f}ms")
        print(f"  Max: {max(store_times):.2f}ms")
        print(f"  Min: {min(store_times):.2f}ms")

        # Assert success criteria
        assert p99 < 50, f"99th percentile store time ({p99:.2f}ms) exceeds 50ms threshold"

    def test_retrieve_operation_performance(self, temp_repo, mock_issue_id):
        """
        SC-001: Store/retrieve operations < 50ms (99th percentile)
        """
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="benchmark")

        # Pre-populate data
        coords = []
        for i in range(1, 101):
            coord = VectorCoordinate(x=mock_issue_id(i), y=2, z=2)
            manager.store(
                coord=coord,
                content=f"Benchmark decision {i}",
                issue_context={"issue_id": f"bench-{i}"},
            )
            coords.append(coord)

        # Measure retrieve operations
        retrieve_times = []
        for coord in coords:
            start = time.perf_counter()
            decision = manager.get(coord)
            end = time.perf_counter()

            assert decision is not None
            retrieve_times.append((end - start) * 1000)  # Convert to ms

        # Calculate percentiles
        p50 = quantiles(retrieve_times, n=100)[49]
        p99 = quantiles(retrieve_times, n=100)[98]

        print("\nRetrieve Performance:")
        print(f"  50th percentile: {p50:.2f}ms")
        print(f"  99th percentile: {p99:.2f}ms")
        print(f"  Max: {max(retrieve_times):.2f}ms")
        print(f"  Min: {min(retrieve_times):.2f}ms")

        # Assert success criteria
        assert p99 < 50, f"99th percentile retrieve time ({p99:.2f}ms) exceeds 50ms threshold"

    def test_handles_10k_decisions(self, temp_repo, mock_issue_id):
        """
        SC-004: Handles 10,000 stored decisions
        """
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="benchmark")

        print("\nStoring 10,000 decisions...")
        start = time.perf_counter()

        # Store 10,000 decisions (using x=0-999, y=1-5, z=2-3 combinations)
        # With 1000 x values × 5 y values × 2 z values = 10,000 combinations
        count = 0
        for x in range(0, 1000):
            for y in [1, 2, 3, 4, 5]:
                for z in [2, 3]:  # Use 2 z values
                    if count >= 10000:
                        break
                    coord = VectorCoordinate(x=mock_issue_id(x), y=y, z=z)
                    manager.store(
                        coord=coord,
                        content=f"Decision at ({x}, {y}, {z})",
                        issue_context={"issue_id": f"bench-{x}"},
                    )
                    count += 1
                if count >= 10000:
                    break
            if count >= 10000:
                break

        end = time.perf_counter()

        print(f"  Stored {count} decisions in {end - start:.2f}s")
        print(f"  Average: {((end - start) / count) * 1000:.2f}ms per decision")

        # Verify we can query them
        start = time.perf_counter()
        results = manager.query_range(x_range=(mock_issue_id(0), mock_issue_id(999)))
        end = time.perf_counter()

        print(f"  Query returned {len(results)} decisions in {(end - start) * 1000:.2f}ms")

        assert len(results) >= 10000, "Should handle 10,000 decisions"

    def test_git_sync_performance(self, temp_repo, mock_issue_id):
        """
        SC-005: Git sync < 5s for 1000 decisions
        """
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="benchmark")

        # Store 1000 decisions (use i from 0-999)
        for i in range(0, 1000):
            coord = VectorCoordinate(x=mock_issue_id(i), y=2, z=2)
            manager.store(
                coord=coord,
                content=f"Decision {i}",
                issue_context={"issue_id": f"bench-{i}"},
            )

        # Measure sync time
        start = time.perf_counter()
        manager.sync(message="Benchmark sync of 1000 decisions")
        end = time.perf_counter()

        sync_time = end - start
        print("\nGit Sync Performance:")
        print(f"  1000 decisions synced in {sync_time:.2f}s")

        # Assert success criteria
        assert sync_time < 5.0, f"Git sync time ({sync_time:.2f}s) exceeds 5s threshold"

    def test_recovery_performance(self, temp_repo, mock_issue_id):
        """
        SC-006: Recovery < 10s
        """
        # First, create and sync data (use i from 0-999)
        manager1 = VectorMemoryManager(repo_path=temp_repo, agent_id="setup")
        for i in range(0, 1000):
            coord = VectorCoordinate(x=mock_issue_id(i), y=2, z=2)
            manager1.store(
                coord=coord,
                content=f"Decision {i}",
                issue_context={"issue_id": f"bench-{i}"},
            )
        manager1.sync()

        # Simulate crash by creating new manager and loading from git
        start = time.perf_counter()
        manager2 = VectorMemoryManager(repo_path=temp_repo, agent_id="recovery")
        manager2.load_from_git()
        end = time.perf_counter()

        recovery_time = end - start
        print("\nRecovery Performance:")
        print(f"  Loaded 1000 decisions in {recovery_time:.2f}s")

        # Verify data integrity
        test_coord = VectorCoordinate(x=mock_issue_id(500), y=2, z=2)
        decision = manager2.get(test_coord)
        assert decision is not None

        # Assert success criteria
        assert recovery_time < 10.0, f"Recovery time ({recovery_time:.2f}s) exceeds 10s threshold"

    def test_partial_order_query_performance(self, temp_repo, mock_issue_id):
        """
        SC-007: Partial ordering queries < 100ms
        """
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="benchmark")

        # Pre-populate data
        for x in range(1, 101):
            for y in [1, 2, 3, 4]:
                coord = VectorCoordinate(x=mock_issue_id(x), y=y, z=2)
                manager.store(
                    coord=coord,
                    content=f"Decision at ({x}, {y})",
                    issue_context={"issue_id": f"bench-{x}"},
                )

        # Measure partial order queries
        query_times = []
        for _ in range(10):
            start = time.perf_counter()
            results = manager.query_partial_order(x_threshold=mock_issue_id(50), y_threshold=3)
            end = time.perf_counter()

            query_times.append((end - start) * 1000)  # Convert to ms

        avg_time = sum(query_times) / len(query_times)
        max_time = max(query_times)

        print("\nPartial Order Query Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  Results per query: {len(results)}")

        # Assert success criteria
        assert (
            avg_time < 100
        ), f"Average partial order query time ({avg_time:.2f}ms) exceeds 100ms threshold"
        assert (
            max_time < 100
        ), f"Max partial order query time ({max_time:.2f}ms) exceeds 100ms threshold"

    def test_content_search_performance(self, temp_repo, mock_issue_id):
        """
        SC-008: Content search < 200ms
        """
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="benchmark")

        # Pre-populate with searchable content
        keywords = ["database", "network", "storage", "compute", "security"]
        for i in range(1, 201):
            coord = VectorCoordinate(x=mock_issue_id(i), y=2, z=2)
            keyword = keywords[i % len(keywords)]
            manager.store(
                coord=coord,
                content=f"This is a decision about {keyword} for issue {i}",
                issue_context={"issue_id": f"bench-{i}"},
            )

        # Measure content search
        search_times = []
        for keyword in keywords:
            start = time.perf_counter()
            results = manager.search_content([keyword])
            end = time.perf_counter()

            search_times.append((end - start) * 1000)  # Convert to ms
            assert len(results) > 0

        avg_time = sum(search_times) / len(search_times)
        max_time = max(search_times)

        print("\nContent Search Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")

        # Assert success criteria
        assert (
            avg_time < 200
        ), f"Average content search time ({avg_time:.2f}ms) exceeds 200ms threshold"
        assert max_time < 200, f"Max content search time ({max_time:.2f}ms) exceeds 200ms threshold"

    def test_range_query_performance(self, temp_repo, mock_issue_id):
        """Test range query performance across different result sizes."""
        manager = VectorMemoryManager(repo_path=temp_repo, agent_id="benchmark")

        # Pre-populate data
        for x in range(1, 201):
            for z in [1, 2, 3]:
                coord = VectorCoordinate(x=mock_issue_id(x), y=2, z=z)
                manager.store(
                    coord=coord,
                    content=f"Decision at ({x}, 2, {z})",
                    issue_context={"issue_id": f"bench-{x}"},
                )

        # Test different query sizes
        test_cases = [
            ("Small", (mock_issue_id(1), mock_issue_id(10))),
            ("Medium", (mock_issue_id(1), mock_issue_id(50))),
            ("Large", (mock_issue_id(1), mock_issue_id(200))),
        ]

        print("\nRange Query Performance:")
        for name, x_range in test_cases:
            start = time.perf_counter()
            results = manager.query_range(x_range=x_range)
            end = time.perf_counter()

            query_time = (end - start) * 1000
            print(f"  {name} ({x_range}): {query_time:.2f}ms ({len(results)} results)")

            # All queries should be reasonably fast
            assert query_time < 100, f"{name} query took {query_time:.2f}ms"
