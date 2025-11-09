"""Unit tests for MemoryIndex with concurrency scenarios."""

import threading

from vector_memory.coordinate import VectorCoordinate
from vector_memory.validation import MemoryIndex


class TestMemoryIndexBasic:
    """Test basic MemoryIndex operations."""

    def test_create_empty_index(self, mock_issue_id):
        """Test creating empty index."""
        index = MemoryIndex()
        assert len(index.coords) == 0
        assert len(index.metadata) == 0
        assert len(index.content_index) == 0

    def test_add_single_coordinate(self, mock_issue_id):
        """Test adding a single coordinate."""
        index = MemoryIndex()
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        metadata = {"timestamp": "2025-01-06T12:00:00Z", "agent_id": "test"}

        index.add(coord, metadata)

        assert coord.to_tuple() in index.coords
        assert index.metadata[coord.to_tuple()] == metadata

    def test_remove_coordinate(self, mock_issue_id):
        """Test removing a coordinate."""
        index = MemoryIndex()
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        metadata = {"timestamp": "2025-01-06T12:00:00Z", "agent_id": "test"}

        index.add(coord, metadata)
        assert coord.to_tuple() in index.coords

        index.remove(coord)
        assert coord.to_tuple() not in index.coords
        assert coord.to_tuple() not in index.metadata


class TestMemoryIndexConcurrency:
    """Test concurrency scenarios for MemoryIndex."""

    def test_concurrent_adds_same_layer(self, mock_issue_id):
        """Test multiple threads adding coordinates to the same layer."""
        index = MemoryIndex()
        errors = []

        def add_coordinates(start_idx: int, count: int):
            try:
                for i in range(count):
                    coord = VectorCoordinate(x=mock_issue_id(start_idx + i), y=2, z=1)
                    metadata = {
                        "timestamp": f"2025-01-06T12:00:{i:02d}Z",
                        "agent_id": f"agent-{start_idx}",
                    }
                    index.add(coord, metadata)
            except Exception as e:
                errors.append(e)

        # Create 4 threads, each adding 25 coordinates
        threads = []
        for i in range(4):
            t = threading.Thread(target=add_coordinates, args=(i * 25, 25))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Check all 100 coordinates were added
        assert len(index.coords) == 100

    def test_concurrent_adds_different_layers(self, mock_issue_id):
        """Test multiple threads adding coordinates to different layers."""
        index = MemoryIndex()
        errors = []

        def add_layer_coordinates(z: int, count: int):
            try:
                for i in range(count):
                    coord = VectorCoordinate(x=mock_issue_id(i), y=2, z=z)
                    metadata = {
                        "timestamp": f"2025-01-06T12:00:{i:02d}Z",
                        "agent_id": f"agent-layer-{z}",
                    }
                    index.add(coord, metadata)
            except Exception as e:
                errors.append(e)

        # Create 4 threads, one per layer
        threads = []
        for z in [1, 2, 3, 4]:
            t = threading.Thread(target=add_layer_coordinates, args=(z, 10))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Check coordinates per layer
        for z in [1, 2, 3, 4]:
            layer_coords = [c for c in index.coords if c[2] == z]
            assert len(layer_coords) == 10

    def test_concurrent_add_and_query(self, mock_issue_id, mock_issue_batch):
        """Test concurrent adds while querying."""
        index = MemoryIndex()
        errors = []
        query_results = []

        def add_coordinates(count: int):
            try:
                for i in range(count):
                    coord = VectorCoordinate(x=mock_issue_id(i), y=2, z=1)
                    metadata = {"timestamp": f"2025-01-06T12:00:{i:02d}Z", "agent_id": "adder"}
                    index.add(coord, metadata)
            except Exception as e:
                errors.append(e)

        def query_coordinates():
            try:
                batch_ids = mock_issue_batch(0, 50)
                for _ in range(50):
                    # x_range expects (min, max) tuple, not full list
                    results = index.query_range(x_range=(batch_ids[0], batch_ids[-1]))
                    query_results.append(len(results))
            except Exception as e:
                errors.append(e)

        # Create writer and multiple readers
        writer = threading.Thread(target=add_coordinates, args=(50,))
        readers = [threading.Thread(target=query_coordinates) for _ in range(3)]

        # Start all threads
        writer.start()
        for r in readers:
            r.start()

        # Wait for completion
        writer.join()
        for r in readers:
            r.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # All coordinates should be added
        assert len(index.coords) == 50

        # Query results should increase over time (or stay same)
        # Some queries might see partial results
        assert len(query_results) > 0

    def test_concurrent_add_and_remove(self, mock_issue_id):
        """Test concurrent adds and removes."""
        index = MemoryIndex()
        errors = []

        # Pre-populate with some coordinates
        for i in range(0, 50):
            coord = VectorCoordinate(x=mock_issue_id(i), y=2, z=2)
            metadata = {"timestamp": "2025-01-06T12:00:00Z", "agent_id": "setup"}
            index.add(coord, metadata)

        def add_coordinates(start_idx: int, count: int):
            try:
                for i in range(count):
                    coord = VectorCoordinate(x=mock_issue_id(start_idx + i), y=3, z=1)
                    metadata = {"timestamp": "2025-01-06T13:00:00Z", "agent_id": "adder"}
                    index.add(coord, metadata)
            except Exception as e:
                errors.append(e)

        def remove_coordinates(start_idx: int, count: int):
            try:
                for i in range(count):
                    coord = VectorCoordinate(x=mock_issue_id(start_idx + i), y=2, z=2)
                    index.remove(coord)
            except Exception as e:
                errors.append(e)

        # Create add and remove threads
        adder = threading.Thread(target=add_coordinates, args=(50, 25))
        remover = threading.Thread(target=remove_coordinates, args=(0, 25))

        # Start both
        adder.start()
        remover.start()

        # Wait for completion
        adder.join()
        remover.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Should have 50 remaining: 25 from original (25-49) + 25 new
        assert len(index.coords) == 50

    def test_concurrent_content_index_updates(self, mock_issue_id):
        """Test concurrent updates to content index."""
        index = MemoryIndex()
        errors = []

        def add_with_content(start_idx: int, count: int, word: str):
            try:
                for i in range(count):
                    coord = VectorCoordinate(x=mock_issue_id(start_idx + i), y=2, z=3)
                    metadata = {"timestamp": "2025-01-06T12:00:00Z", "agent_id": f"agent-{word}"}
                    content = f"This is a test with {word} keyword"
                    index.add(coord, metadata, content=content)
            except Exception as e:
                errors.append(e)

        # Create threads with different keywords
        threads = []
        keywords = ["database", "network", "storage", "compute"]
        for i, keyword in enumerate(keywords):
            t = threading.Thread(target=add_with_content, args=(i * 10, 10, keyword))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Check content index built correctly
        for keyword in keywords:
            coords = index.query_content([keyword])
            assert len(coords) == 10

        # Check common words
        test_coords = index.query_content(["test"])
        assert len(test_coords) == 40  # All have "test"

    def test_concurrent_partial_order_queries(self, mock_issue_id, mock_dag_order):
        """Test concurrent partial order queries while adding."""
        index = MemoryIndex()
        errors = []
        query_counts = []

        # Pre-populate
        for i in range(0, 20):
            for y in [1, 2, 3]:
                coord = VectorCoordinate(x=mock_issue_id(i), y=y, z=1)
                metadata = {"timestamp": "2025-01-06T12:00:00Z", "agent_id": "setup"}
                index.add(coord, metadata)

        def query_before_point(issue_id: str, y_thresh: int, iterations: int):
            try:
                for _ in range(iterations):
                    results = index.query_partial_order(
                        issue_id, y_thresh, dag_order=mock_dag_order
                    )
                    query_counts.append(len(results))
            except Exception as e:
                errors.append(e)

        # Create multiple query threads
        threads = []
        for _i in range(4):
            t = threading.Thread(target=query_before_point, args=(mock_issue_id(10), 3, 25))
            threads.append(t)
            t.start()

        # Wait for all
        for t in threads:
            t.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # All queries should return consistent results
        assert len(query_counts) == 100
        # All should be the same since we're not modifying during queries
        assert all(c == query_counts[0] for c in query_counts)

    def test_race_condition_add_same_coordinate(self, mock_issue_id):
        """Test race condition when adding same coordinate from multiple threads."""
        index = MemoryIndex()
        errors = []

        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)

        def add_same_coordinate(agent_id: str):
            try:
                metadata = {"timestamp": "2025-01-06T12:00:00Z", "agent_id": agent_id}
                index.add(coord, metadata)
            except Exception as e:
                errors.append(e)

        # Create 10 threads trying to add same coordinate
        threads = []
        for i in range(10):
            t = threading.Thread(target=add_same_coordinate, args=(f"agent-{i}",))
            threads.append(t)
            t.start()

        # Wait for all
        for t in threads:
            t.join()

        # No errors should occur (last write wins)
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Coordinate should exist once
        assert coord.to_tuple() in index.coords

        # One of the agent IDs should be in metadata
        assert "agent_id" in index.metadata[coord.to_tuple()]

    def test_concurrent_layer_index_consistency(self, mock_issue_id):
        """Test layer index remains consistent during concurrent operations."""
        index = MemoryIndex()
        errors = []

        def add_to_layer(z: int, start_idx: int, count: int):
            try:
                for i in range(count):
                    coord = VectorCoordinate(x=mock_issue_id(start_idx + i), y=2, z=z)
                    metadata = {"timestamp": "2025-01-06T12:00:00Z", "agent_id": f"layer-{z}"}
                    index.add(coord, metadata)
            except Exception as e:
                errors.append(e)

        # Add to all layers concurrently
        threads = []
        for z in [1, 2, 3, 4]:
            t = threading.Thread(target=add_to_layer, args=(z, 0, 25))
            threads.append(t)
            t.start()

        # Wait for all
        for t in threads:
            t.join()

        # Check no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify layer index consistency
        for z in [1, 2, 3, 4]:
            layer_coords = index.layer_index[z]
            # Each layer should have 25 coordinates
            assert len(layer_coords) == 25
            # All should be at the correct z level
            for coord_tuple in layer_coords:
                assert coord_tuple[2] == z
