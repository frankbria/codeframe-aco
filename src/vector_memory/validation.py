"""Index and validation utilities for vector memory."""

from pathlib import Path

from vector_memory.coordinate import VectorCoordinate


class MemoryIndex:
    """
    In-memory index for fast coordinate lookup.

    Attributes:
        coords: Maps coordinate tuples to file paths
        metadata: Maps coordinate tuples to metadata dicts
        content_index: Maps words to sets of coordinate tuples (for content search)
        layer_index: Maps layer z to lists of coordinate tuples (optimization)
    """

    def __init__(self) -> None:
        """Initialize empty index."""
        self.coords: dict[tuple[str, int, int], Path] = {}
        self.metadata: dict[tuple[str, int, int], dict] = {}
        self.content_index: dict[str, set[tuple[str, int, int]]] = {}
        self.layer_index: dict[int, list[tuple[str, int, int]]] = {1: [], 2: [], 3: [], 4: []}

    def add(self, coord: VectorCoordinate, metadata: dict, content: str = "") -> None:
        """
        Add coordinate to all indexes.

        Args:
            coord: Coordinate to add
            metadata: Metadata dictionary (timestamp, agent_id, etc.)
            content: Decision content for content indexing (optional)
        """
        coord_tuple = coord.to_tuple()

        # Add to primary index
        self.coords[coord_tuple] = coord.to_path()

        # Add to metadata index
        self.metadata[coord_tuple] = metadata

        # Add to layer index
        if coord_tuple not in self.layer_index[coord.z]:
            self.layer_index[coord.z].append(coord_tuple)

        # Build content index (simple word-based)
        if content:
            words = self._tokenize(content)
            for word in words:
                if word not in self.content_index:
                    self.content_index[word] = set()
                self.content_index[word].add(coord_tuple)

    def remove(self, coord: VectorCoordinate) -> None:
        """
        Remove coordinate from all indexes.

        Args:
            coord: Coordinate to remove
        """
        coord_tuple = coord.to_tuple()

        # Remove from primary index
        if coord_tuple in self.coords:
            del self.coords[coord_tuple]

        # Remove from metadata index
        if coord_tuple in self.metadata:
            del self.metadata[coord_tuple]

        # Remove from layer index
        if coord_tuple in self.layer_index[coord.z]:
            self.layer_index[coord.z].remove(coord_tuple)

        # Remove from content index (expensive, but rare operation)
        for word_set in self.content_index.values():
            word_set.discard(coord_tuple)

    def query_exact(self, coord: VectorCoordinate) -> Path | None:
        """
        O(1) lookup by exact coordinate.

        Args:
            coord: Coordinate to look up

        Returns:
            Path to file if exists, None otherwise
        """
        return self.coords.get(coord.to_tuple())

    def query_range(
        self,
        x_range: tuple[str, str] | None = None,
        y_range: tuple[int, int] | None = None,
        z_range: tuple[int, int] | None = None,
        dag_order: dict[str, int] | None = None,
    ) -> list[tuple[str, int, int]]:
        """
        O(n) scan with filtering by coordinate ranges.

        Args:
            x_range: (min, max) inclusive range for x (issue IDs), or None for all
            y_range: (min, max) inclusive range for y, or None for all
            z_range: (min, max) inclusive range for z, or None for all
            dag_order: Optional DAG ordering for x comparison (maps issue_id -> position)

        Returns:
            List of coordinate tuples matching the ranges
        """
        results = []

        for coord_tuple in self.coords:
            x, y, z = coord_tuple

            # Check x range
            if x_range is not None:
                x_min, x_max = x_range

                if dag_order is not None:
                    # Use DAG topological sort positions for comparison
                    x_pos = dag_order.get(x, float("inf"))
                    x_min_pos = dag_order.get(x_min, float("-inf"))
                    x_max_pos = dag_order.get(x_max, float("inf"))
                    if not (x_min_pos <= x_pos <= x_max_pos):
                        continue
                else:
                    # Fallback: lexicographic string comparison
                    if not (x_min <= x <= x_max):
                        continue

            # Check y range
            if y_range is not None:
                y_min, y_max = y_range
                if not (y_min <= y <= y_max):
                    continue

            # Check z range
            if z_range is not None:
                z_min, z_max = z_range
                if not (z_min <= z <= z_max):
                    continue

            results.append(coord_tuple)

        return sorted(results)

    def query_partial_order(
        self,
        x_threshold: str,
        y_threshold: int,
        z_filter: int | None = None,
        dag_order: dict[str, int] | None = None,
    ) -> list[tuple[str, int, int]]:
        """
        Find all coordinates where (x,y) < (x_threshold, y_threshold).

        Args:
            x_threshold: Issue ID threshold
            y_threshold: Cycle stage threshold
            z_filter: Optional layer filter (only return decisions at this z)
            dag_order: Optional DAG ordering for x comparison (maps issue_id -> position)

        Returns:
            List of coordinate tuples where (x,y) < threshold
        """
        results = []

        for coord_tuple in self.coords:
            x, y, z = coord_tuple

            # Check partial ordering: (x,y) < (x_threshold, y_threshold)
            # Means: x < x_threshold OR (x == x_threshold AND y < y_threshold)
            if dag_order is not None:
                # Use DAG topological sort positions
                x_pos = dag_order.get(x, float("inf"))
                x_threshold_pos = dag_order.get(x_threshold, float("inf"))
                x_less = x_pos < x_threshold_pos
                x_equal = x == x_threshold
            else:
                # Fallback: lexicographic string comparison
                x_less = x < x_threshold
                x_equal = x == x_threshold

            if x_less or (x_equal and y < y_threshold):
                # Apply z filter if specified
                if z_filter is None or z == z_filter:
                    results.append(coord_tuple)

        return sorted(results)

    def query_content(
        self, search_terms: list[str], match_all: bool = False
    ) -> set[tuple[str, int, int]]:
        """
        Search by content keywords.

        Args:
            search_terms: List of keywords to search for
            match_all: If True, require all terms; if False, require any term

        Returns:
            Set of coordinate tuples matching search criteria
        """
        if not search_terms:
            return set()

        # Normalize search terms
        normalized_terms = [term.lower() for term in search_terms]

        if match_all:
            # Intersection: coordinates must contain ALL terms
            result_sets = []
            for term in normalized_terms:
                term_coords = self.content_index.get(term, set())
                result_sets.append(term_coords)

            if not result_sets:
                return set()

            # Intersection of all sets
            result = result_sets[0]
            for coord_set in result_sets[1:]:
                result = result.intersection(coord_set)
            return result
        else:
            # Union: coordinates contain ANY term
            result = set()
            for term in normalized_terms:
                term_coords = self.content_index.get(term, set())
                result = result.union(term_coords)
            return result

    def rebuild(self, vector_memory_dir: Path) -> int:
        """
        Reconstruct index from file system.

        Args:
            vector_memory_dir: Root directory (.vector-memory/)

        Returns:
            Number of decisions loaded
        """
        import json

        # Clear existing index
        self.coords.clear()
        self.metadata.clear()
        self.content_index.clear()
        for layer_list in self.layer_index.values():
            layer_list.clear()

        # Scan file system
        if not vector_memory_dir.exists():
            return 0

        count = 0
        for json_file in vector_memory_dir.rglob("*.json"):
            try:
                # Parse coordinate from path
                coord = VectorCoordinate.from_path(json_file)

                # Load metadata (timestamp, agent_id) from file WITHOUT loading full content
                # This is the lazy loading optimization - we only load what we need for indexing
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Extract only metadata fields, not the full content
                metadata = {
                    "timestamp": data.get("timestamp", ""),
                    "agent_id": data.get("agent_id", ""),
                    "path": str(json_file),
                }

                # Add to index without content (lazy load content on demand when get() is called)
                self.add(coord, metadata, content="")  # No content = lazy load
                count += 1
            except (ValueError, Exception):
                # Skip invalid files
                continue

        return count

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """
        Simple tokenization for content indexing.

        Args:
            text: Text to tokenize

        Returns:
            List of lowercase words
        """
        # Simple word tokenization (split on non-alphanumeric)
        import re

        words = re.findall(r"\w+", text.lower())
        return words
