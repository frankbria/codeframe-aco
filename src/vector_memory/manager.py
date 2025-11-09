"""VectorMemoryManager - Main API for the vector memory system."""

import logging
from datetime import UTC, datetime
from pathlib import Path

from vector_memory.coordinate import VectorCoordinate
from vector_memory.exceptions import (
    ConcurrencyError,
    CoordinateValidationError,
    ImmutableLayerError,
    QueryError,
    StorageError,
)
from vector_memory.persistence import GitPersistence
from vector_memory.storage import MemoryLayer, StoredDecision
from vector_memory.validation import MemoryIndex

# Configure module logger
logger = logging.getLogger(__name__)


class VectorMemoryManager:
    """
    Main interface for interacting with the vector memory system.

    Manages coordinate-based storage and retrieval of AI agent decisions.
    """

    def __init__(self, repo_path: Path, agent_id: str):
        """
        Initialize vector memory manager.

        Args:
            repo_path: Path to Git repository root
            agent_id: Unique identifier for this agent

        Raises:
            StorageError: If repo_path doesn't exist or isn't a Git repository
            ValueError: If agent_id is empty
        """
        # Validate inputs
        if not agent_id or not agent_id.strip():
            raise ValueError("agent_id must not be empty")

        if not repo_path.exists():
            raise StorageError(f"Repository path does not exist: {repo_path}")

        # Check if it's a git repository
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            raise StorageError(f"Not a Git repository: {repo_path}")

        # Initialize attributes
        self.repo_path = repo_path.resolve()
        self.agent_id = agent_id
        self.vector_memory_dir = self.repo_path / ".vector-memory"
        self.index = MemoryIndex()
        self.git = GitPersistence(self.repo_path)

        # Create .vector-memory directory if it doesn't exist
        self.vector_memory_dir.mkdir(exist_ok=True)

        # Load existing decisions from file system
        decision_count = self.load_from_git()
        logger.info(
            f"Initialized VectorMemoryManager for agent '{agent_id}' "
            f"at {repo_path} with {decision_count} existing decisions"
        )

    def store(
        self,
        coord: VectorCoordinate,
        content: str,
        issue_context: dict[str, str] | None = None,
    ) -> StoredDecision:
        """
        Store a decision at the specified coordinate.

        Args:
            coord: 3D coordinate (x, y, z) where to store the decision
            content: Decision text (max 100KB)
            issue_context: Optional context about the issue

        Returns:
            StoredDecision object with timestamp and metadata

        Raises:
            CoordinateValidationError: If coordinate values are invalid
            ImmutableLayerError: If trying to modify z=1 (architecture) layer
            StorageError: If file write fails
            ValueError: If content is empty or too large
            ConcurrencyError: If lock timeout occurs
        """
        import json
        import os
        import tempfile

        from filelock import FileLock, Timeout

        # Validate content
        if not content or not content.strip():
            raise ValueError("content must not be empty")

        if len(content.encode("utf-8")) > 100 * 1024:  # 100KB
            raise ValueError("content too large (max 100KB)")

        # Get layer info for validation
        layer = MemoryLayer.get_layer(coord.z)

        # Create decision object
        timestamp = datetime.now(UTC)
        decision = StoredDecision(
            coordinate=coord,
            content=content,
            timestamp=timestamp,
            agent_id=self.agent_id,
            issue_context=issue_context,
        )

        # Write to file system using atomic write pattern with file locking
        file_path = self.repo_path / coord.to_path()
        lock_path = file_path.parent / f"{file_path.name}.lock"

        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Acquire lock before writing (timeout after 5 seconds)
            with FileLock(lock_path, timeout=5):
                # CRITICAL: Check immutability AFTER acquiring lock to prevent race condition
                # Read on-disk state (not index) to catch concurrent writes
                existing_decision = None
                if file_path.exists():
                    existing_decision = StoredDecision.from_file(file_path)

                # Validate immutability rules based on actual on-disk state
                layer.validate_write(coord, existing_decision)

                # Atomic write: write to temp file, then rename
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=file_path.parent,
                    delete=False,
                    suffix=".tmp",
                ) as tmp_file:
                    json.dump(decision.to_json(), tmp_file, indent=2, ensure_ascii=False)
                    tmp_path = tmp_file.name

                # Atomic rename
                os.replace(tmp_path, str(file_path))

            # Update index (outside lock - index is in-memory)
            metadata = {
                "timestamp": timestamp.isoformat(),
                "agent_id": self.agent_id,
            }
            self.index.add(coord, metadata, content)

            logger.info(
                f"Stored decision at {coord.to_tuple()} "
                f"(layer={layer.name}, size={len(content)} bytes)"
            )
            return decision

        except Timeout as e:
            logger.error(f"Lock timeout storing decision at {coord.to_tuple()}")
            raise ConcurrencyError(
                f"Lock timeout while storing decision at {coord.to_tuple()}. "
                "Another process may be writing to this coordinate."
            ) from e
        except ImmutableLayerError:
            # Re-raise immutability errors directly (don't wrap in StorageError)
            raise
        except Exception as e:
            logger.error(f"Failed to store decision at {coord.to_tuple()}: {e}")
            raise StorageError(f"Failed to store decision at {coord.to_tuple()}: {e}") from e

    def get(self, coord: VectorCoordinate) -> StoredDecision | None:
        """
        Retrieve a decision from the specified coordinate.

        Args:
            coord: 3D coordinate to retrieve from

        Returns:
            StoredDecision if exists, None if coordinate is empty

        Raises:
            CoordinateValidationError: If coordinate values are invalid
            StorageError: If file read fails
        """
        # Check if coordinate exists in index
        file_path = self.index.query_exact(coord)

        if file_path is None:
            return None

        # Read from file system
        try:
            full_path = self.repo_path / file_path
            if not full_path.exists():
                return None

            decision = StoredDecision.from_file(full_path)
            return decision

        except Exception as e:
            raise StorageError(f"Failed to retrieve decision at {coord.to_tuple()}: {e}") from e

    def exists(self, coord: VectorCoordinate) -> bool:
        """
        Check if a decision exists at the specified coordinate.

        Args:
            coord: 3D coordinate to check

        Returns:
            True if decision exists, False otherwise

        Raises:
            CoordinateValidationError: If coordinate values are invalid
        """
        file_path = self.index.query_exact(coord)
        if file_path is None:
            return False

        # Verify file actually exists on disk
        full_path = self.repo_path / file_path
        return full_path.exists()

    def query_range(
        self,
        x_range: tuple[str, str] | None = None,
        y_range: tuple[int, int] | None = None,
        z_range: tuple[int, int] | None = None,
        dag_order: dict[str, int] | None = None,
    ) -> list[StoredDecision]:
        """
        Query decisions within specified coordinate ranges.

        Args:
            x_range: (min, max) inclusive range for x (issue IDs), or None for all
            y_range: (min, max) inclusive range for y, or None for all
            z_range: (min, max) inclusive range for z, or None for all
            dag_order: Optional DAG topological ordering (maps issue_id → position).
                      When provided, x-coordinates are compared using DAG positions
                      instead of lexicographic string ordering. This enables correct
                      ordering for non-padded Beads IDs.

        Returns:
            List of StoredDecision objects matching the ranges

        Raises:
            QueryError: If ranges are invalid (min > max)
        """
        # Validate ranges (for x_range, validation is lexicographic string comparison)
        if x_range is not None:
            x_min, x_max = x_range
            # String comparison for issue IDs - validation is less strict
            # since we don't know the DAG ordering here

        if y_range is not None:
            y_min, y_max = y_range
            if y_min > y_max:
                raise QueryError(f"Invalid y_range: min ({y_min}) > max ({y_max})")

        if z_range is not None:
            z_min, z_max = z_range
            if z_min > z_max:
                raise QueryError(f"Invalid z_range: min ({z_min}) > max ({z_max})")

        # Query index for matching coordinates
        coord_tuples = self.index.query_range(x_range, y_range, z_range, dag_order=dag_order)

        # Load decisions from file system
        results = []
        for coord_tuple in coord_tuples:
            coord = VectorCoordinate(x=coord_tuple[0], y=coord_tuple[1], z=coord_tuple[2])
            decision = self.get(coord)
            if decision is not None:
                results.append(decision)

        return results

    def query_partial_order(
        self,
        x_threshold: str,
        y_threshold: int,
        z_filter: int | None = None,
        dag_order: dict[str, int] | None = None,
    ) -> list[StoredDecision]:
        """
        Query decisions where (x,y) < (x_threshold, y_threshold).

        This returns all decisions that occurred "before" the threshold
        in the DAG × cycle space, useful for rollback operations.

        Args:
            x_threshold: Issue ID threshold
            y_threshold: Cycle stage threshold (1-6)
            z_filter: Optional layer filter (only return decisions at this z)
            dag_order: Optional DAG topological ordering (maps issue_id → position).
                      When provided, x-coordinates are compared using DAG positions
                      instead of lexicographic string ordering. This enables correct
                      partial ordering for non-padded Beads IDs.

        Returns:
            List of StoredDecision objects where (x,y) < threshold, sorted

        Raises:
            CoordinateValidationError: If thresholds are invalid
        """
        # T081: Add coordinate validation for thresholds
        # x_threshold is a string issue ID - no numeric validation needed
        if not (1 <= y_threshold <= 6):
            raise CoordinateValidationError(f"y_threshold must be in [1, 6], got {y_threshold}")
        if z_filter is not None and z_filter not in {1, 2, 3, 4}:
            raise CoordinateValidationError(f"z_filter must be in {{1, 2, 3, 4}}, got {z_filter}")

        # T081: Query index using partial order
        coord_tuples = self.index.query_partial_order(
            x_threshold=x_threshold,
            y_threshold=y_threshold,
            z_filter=z_filter,
            dag_order=dag_order,
        )

        # T082: Load decisions from coordinates
        results = []
        for coord_tuple in coord_tuples:
            coord = VectorCoordinate(x=coord_tuple[0], y=coord_tuple[1], z=coord_tuple[2])
            decision = self.get(coord)
            if decision is not None:
                results.append(decision)

        # T084: Results are already sorted lexicographically by index
        return results

    def search_content(
        self,
        search_terms: list[str],
        match_all: bool = False,
    ) -> list[StoredDecision]:
        """
        Search decisions by content keywords.

        Args:
            search_terms: List of keywords to search for
            match_all: If True, require all terms; if False, require any term

        Returns:
            List of StoredDecision objects matching search criteria

        Raises:
            QueryError: If search_terms is empty
        """
        if not search_terms:
            raise QueryError("search_terms must not be empty")

        # Query index for matching coordinates
        coord_tuples = self.index.query_content(search_terms, match_all)

        # Load decisions from file system
        results = []
        for coord_tuple in coord_tuples:
            coord = VectorCoordinate(x=coord_tuple[0], y=coord_tuple[1], z=coord_tuple[2])
            decision = self.get(coord)
            if decision is not None:
                results.append(decision)

        # Sort by relevance (number of matching terms in content)
        def relevance_score(decision: StoredDecision) -> int:
            content_lower = decision.content.lower()
            score = sum(1 for term in search_terms if term.lower() in content_lower)
            return score

        results.sort(key=relevance_score, reverse=True)

        return results

    def sync(self, message: str | None = None) -> None:
        """
        Commit all pending changes to Git.

        Args:
            message: Optional custom commit message

        Raises:
            StorageError: If Git operations fail
        """
        try:
            # Check if there are changes to commit
            if not self.git.has_changes():
                # Nothing to commit, return silently
                logger.debug("Sync called but no changes to commit")
                return

            logger.info("Starting Git sync of vector memory changes")
            # Add .vector-memory/ directory to staging
            self.git.add_vector_memory()

            # Count decisions for commit message
            decision_count = len(self.index.coords)

            # Create commit
            self.git.commit(message=message, decision_count=decision_count)
            logger.info(f"Git sync completed successfully ({decision_count} decisions)")

        except Exception as e:
            logger.error(f"Git sync failed: {e}")
            raise StorageError(f"Failed to sync to Git: {e}") from e

    def load_from_git(self) -> int:
        """
        Load all decisions from .vector-memory/ directory.

        Returns:
            Number of decisions loaded

        Raises:
            StorageError: If files are corrupted or unreadable
        """
        try:
            # Clear existing index
            self.index.coords.clear()
            self.index.metadata.clear()
            self.index.content_index.clear()
            for layer_list in self.index.layer_index.values():
                layer_list.clear()

            # Scan file system
            if not self.vector_memory_dir.exists():
                return 0

            count = 0
            for json_file in self.vector_memory_dir.rglob("*.json"):
                try:
                    # Parse coordinate from path
                    coord = VectorCoordinate.from_path(json_file)

                    # Load full decision to get content for indexing
                    decision = StoredDecision.from_file(json_file)

                    # Add to index with content
                    metadata = {
                        "timestamp": decision.timestamp.isoformat(),
                        "agent_id": decision.agent_id,
                    }
                    self.index.add(coord, metadata, decision.content)

                    count += 1
                except (ValueError, Exception):
                    # Skip invalid files
                    continue

            return count

        except Exception as e:
            raise StorageError(f"Failed to load from Git: {e}") from e
