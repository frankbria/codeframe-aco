# API Contract: Vector Memory Manager

**Feature**: Vector Memory Manager
**Branch**: 001-vector-memory
**Date**: 2025-01-06
**Status**: Complete
**Version**: 1.0.0

## Overview

This document defines the public API contract for the Vector Memory Manager. All functions, parameters, return values, and error conditions are specified to enable implementation and testing.

## Core API

### VectorMemoryManager

Main interface for interacting with the vector memory system.

#### Constructor

```python
class VectorMemoryManager:
    def __init__(self, repo_path: Path, agent_id: str):
        """
        Initialize vector memory manager.

        Args:
            repo_path: Path to Git repository root
            agent_id: Unique identifier for this agent

        Raises:
            StorageError: If repo_path doesn't exist or isn't a Git repository
            ValueError: If agent_id is empty

        Post-conditions:
            - .vector-memory/ directory created if it doesn't exist
            - In-memory index loaded from existing files
            - Ready to store/retrieve decisions
        """
```

**Example**:
```python
manager = VectorMemoryManager(
    repo_path=Path("/path/to/codeframe-aco"),
    agent_id="claude-code-01"
)
```

---

### Storage Operations

#### store()

Store a decision at a specific coordinate.

```python
def store(
    self,
    coord: VectorCoordinate,
    content: str,
    issue_context: Optional[Dict[str, str]] = None
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

    Pre-conditions:
        - coord.x in [1, 1000]
        - coord.y in {1, 2, 3, 4, 5}
        - coord.z in {1, 2, 3, 4}
        - content is non-empty and <= 100KB
        - If z=1, coordinate must not already exist

    Post-conditions:
        - Decision written to .vector-memory/x-{x}/y-{y}-z-{z}.json
        - Index updated with new coordinate
        - Decision retrievable via get()
        - NOT automatically committed to Git (call sync() separately)
    """
```

**Example**:
```python
coord = VectorCoordinate(x=5, y=2, z=1)
decision = manager.store(
    coord=coord,
    content="Use PostgreSQL for persistence layer",
    issue_context={
        "issue_id": "codeframe-aco-t49",
        "issue_title": "Vector Memory Manager"
    }
)
assert decision.coordinate == coord
assert decision.agent_id == "claude-code-01"
```

---

#### get()

Retrieve a decision from a specific coordinate.

```python
def get(self, coord: VectorCoordinate) -> Optional[StoredDecision]:
    """
    Retrieve a decision from the specified coordinate.

    Args:
        coord: 3D coordinate to retrieve from

    Returns:
        StoredDecision if exists, None if coordinate is empty

    Raises:
        CoordinateValidationError: If coordinate values are invalid
        StorageError: If file read fails

    Pre-conditions:
        - coord is a valid VectorCoordinate

    Post-conditions:
        - None (read-only operation)
    """
```

**Example**:
```python
coord = VectorCoordinate(x=5, y=2, z=1)
decision = manager.get(coord)
if decision:
    print(f"Found: {decision.content}")
else:
    print("No decision at this coordinate")
```

---

#### exists()

Check if a decision exists at a coordinate without reading it.

```python
def exists(self, coord: VectorCoordinate) -> bool:
    """
    Check if a decision exists at the specified coordinate.

    Args:
        coord: 3D coordinate to check

    Returns:
        True if decision exists, False otherwise

    Raises:
        CoordinateValidationError: If coordinate values are invalid

    Pre-conditions:
        - coord is a valid VectorCoordinate

    Post-conditions:
        - None (read-only operation)
    """
```

**Example**:
```python
coord = VectorCoordinate(x=5, y=2, z=1)
if manager.exists(coord):
    print("Decision already stored here")
```

---

### Query Operations

#### query_range()

Query decisions within coordinate ranges.

```python
def query_range(
    self,
    x_range: Optional[Tuple[int, int]] = None,
    y_range: Optional[Tuple[int, int]] = None,
    z_range: Optional[Tuple[int, int]] = None
) -> List[StoredDecision]:
    """
    Query decisions within specified coordinate ranges.

    Args:
        x_range: (min, max) inclusive range for x, or None for all
        y_range: (min, max) inclusive range for y, or None for all
        z_range: (min, max) inclusive range for z, or None for all

    Returns:
        List of StoredDecision objects matching the ranges

    Raises:
        QueryError: If ranges are invalid (min > max)

    Pre-conditions:
        - If range specified, min <= max

    Post-conditions:
        - None (read-only operation)
        - Results sorted by (x, y, z) lexicographically
    """
```

**Example**:
```python
# Get all architecture decisions (z=1) for issues 1-10
decisions = manager.query_range(
    x_range=(1, 10),
    z_range=(1, 1)
)

# Get all decisions from architect stage (y=2)
decisions = manager.query_range(y_range=(2, 2))
```

---

#### query_partial_order()

Query decisions before a specific (x, y) threshold.

```python
def query_partial_order(
    self,
    x_threshold: int,
    y_threshold: int,
    z_filter: Optional[int] = None
) -> List[StoredDecision]:
    """
    Query decisions where (x,y) < (x_threshold, y_threshold).

    This returns all decisions that occurred "before" the threshold
    in the DAG × cycle space, useful for rollback operations.

    Args:
        x_threshold: Issue number threshold
        y_threshold: Cycle stage threshold
        z_filter: Optional layer filter (only return decisions at this z)

    Returns:
        List of StoredDecision objects where (x,y) < threshold

    Raises:
        CoordinateValidationError: If thresholds are invalid

    Pre-conditions:
        - x_threshold in [1, 1001] (can be 1001 to include x=1000)
        - y_threshold in [1, 6] (can be 6 to include y=5)
        - If z_filter specified, must be in {1, 2, 3, 4}

    Post-conditions:
        - None (read-only operation)
        - Results sorted by (x, y, z) lexicographically
        - Incomparable coordinates (e.g., (3,4) vs (5,2)) both included if < threshold
    """
```

**Example**:
```python
# Find all decisions before error at (7, 4)
# Useful for rollback: revert to state before this coordinate
decisions_before = manager.query_partial_order(
    x_threshold=7,
    y_threshold=4,
    z_filter=1  # Only architecture decisions
)

# All decisions are guaranteed to have (x,y) < (7,4)
for d in decisions_before:
    assert d.coordinate.x < 7 or (d.coordinate.x == 7 and d.coordinate.y < 4)
```

---

#### search_content()

Search decisions by content.

```python
def search_content(
    self,
    search_terms: List[str],
    match_all: bool = False
) -> List[StoredDecision]:
    """
    Search decisions by content keywords.

    Args:
        search_terms: List of keywords to search for
        match_all: If True, require all terms; if False, require any term

    Returns:
        List of StoredDecision objects matching search criteria

    Raises:
        QueryError: If search_terms is empty

    Pre-conditions:
        - search_terms is non-empty list
        - Each term is non-empty string

    Post-conditions:
        - None (read-only operation)
        - Results sorted by relevance (number of matching terms)
    """
```

**Example**:
```python
# Find all decisions about databases
decisions = manager.search_content(["database", "PostgreSQL"])

# Find decisions that mention both authentication AND security
decisions = manager.search_content(
    ["authentication", "security"],
    match_all=True
)
```

---

### Persistence Operations

#### sync()

Synchronize in-memory state to Git.

```python
def sync(self, message: Optional[str] = None) -> None:
    """
    Commit all pending changes to Git.

    Args:
        message: Optional custom commit message

    Raises:
        StorageError: If Git operations fail

    Pre-conditions:
        - Git repository is initialized
        - Working directory is clean (no uncommitted changes outside .vector-memory/)

    Post-conditions:
        - All files in .vector-memory/ committed to Git
        - Commit message includes coordinate ranges and decision count
        - All in-memory decisions marked as "clean" (synced)
    """
```

**Example**:
```python
# Store several decisions
manager.store(VectorCoordinate(1, 2, 1), "Decision 1")
manager.store(VectorCoordinate(2, 2, 1), "Decision 2")

# Sync to Git
manager.sync(message="Store initial architecture decisions")
```

---

#### load_from_git()

Load vector memory state from Git.

```python
def load_from_git(self) -> int:
    """
    Load all decisions from .vector-memory/ directory.

    Returns:
        Number of decisions loaded

    Raises:
        StorageError: If files are corrupted or unreadable

    Pre-conditions:
        - .vector-memory/ directory exists (created by constructor if needed)

    Post-conditions:
        - In-memory index rebuilt from files
        - All decisions available via get() and query operations
        - Manager ready for new store() operations
    """
```

**Example**:
```python
# After git pull or system restart
count = manager.load_from_git()
print(f"Loaded {count} decisions from Git")
```

---

## Utility Classes

### VectorCoordinate

```python
@dataclass
class VectorCoordinate:
    x: int  # Issue number (1-1000)
    y: int  # Cycle stage (1-5)
    z: int  # Memory layer (1-4)

    def __post_init__(self):
        """Validate coordinate values."""
        if not (1 <= self.x <= 1000):
            raise CoordinateValidationError(f"x must be in [1, 1000], got {self.x}")
        if self.y not in {1, 2, 3, 4, 5}:
            raise CoordinateValidationError(f"y must be in [1, 2, 3, 4, 5], got {self.y}")
        if self.z not in {1, 2, 3, 4}:
            raise CoordinateValidationError(f"z must be in [1, 2, 3, 4], got {self.z}")

    def to_tuple(self) -> Tuple[int, int, int]:
        """Convert to tuple for use as dict key."""
        return (self.x, self.y, self.z)

    def to_path(self) -> Path:
        """Convert to file system path."""
        return Path(f".vector-memory/x-{self.x:03d}/y-{self.y}-z-{self.z}.json")

    @staticmethod
    def from_path(path: Path) -> "VectorCoordinate":
        """Parse coordinate from file path."""
        # Example: .vector-memory/x-005/y-2-z-1.json
        match = re.match(r"x-(\d+)/y-(\d+)-z-(\d+)\.json", str(path))
        if not match:
            raise ValueError(f"Invalid coordinate path: {path}")
        x, y, z = map(int, match.groups())
        return VectorCoordinate(x, y, z)
```

---

### StoredDecision

```python
@dataclass
class StoredDecision:
    coordinate: VectorCoordinate
    content: str
    timestamp: datetime
    agent_id: str
    issue_context: Optional[Dict[str, str]] = None

    def to_json(self) -> dict:
        """Serialize to JSON dict."""
        return {
            "coordinate": {
                "x": self.coordinate.x,
                "y": self.coordinate.y,
                "z": self.coordinate.z
            },
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "issue_context": self.issue_context
        }

    @staticmethod
    def from_json(data: dict) -> "StoredDecision":
        """Deserialize from JSON dict."""
        coord = VectorCoordinate(
            x=data["coordinate"]["x"],
            y=data["coordinate"]["y"],
            z=data["coordinate"]["z"]
        )
        return StoredDecision(
            coordinate=coord,
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            agent_id=data["agent_id"],
            issue_context=data.get("issue_context")
        )
```

---

## Error Hierarchy

```python
class VectorMemoryError(Exception):
    """Base exception for all vector memory errors."""
    pass

class CoordinateValidationError(VectorMemoryError):
    """Coordinate values out of range or invalid."""
    pass

class ImmutableLayerError(VectorMemoryError):
    """Attempt to modify immutable architecture layer (z=1)."""
    pass

class ConcurrencyError(VectorMemoryError):
    """Concurrent access conflict or lock timeout."""
    pass

class StorageError(VectorMemoryError):
    """File system or Git operation failed."""
    pass

class QueryError(VectorMemoryError):
    """Query parameters invalid or malformed."""
    pass
```

---

## Usage Patterns

### Pattern 1: Store and Retrieve

```python
# Initialize manager
manager = VectorMemoryManager(
    repo_path=Path.cwd(),
    agent_id="claude-code-01"
)

# Store a decision
coord = VectorCoordinate(x=5, y=2, z=1)
manager.store(coord, "Use PostgreSQL for persistence")

# Retrieve it later
decision = manager.get(coord)
print(decision.content)  # "Use PostgreSQL for persistence"
```

### Pattern 2: Query and Filter

```python
# Get all architecture decisions for first 10 issues
arch_decisions = manager.query_range(
    x_range=(1, 10),
    z_range=(1, 1)
)

# Find decisions before a specific point (for rollback)
before_error = manager.query_partial_order(x_threshold=7, y_threshold=4)

# Search by content
db_decisions = manager.search_content(["database", "PostgreSQL"])
```

### Pattern 3: Git Synchronization

```python
# Work with decisions
manager.store(VectorCoordinate(1, 2, 1), "Decision 1")
manager.store(VectorCoordinate(2, 2, 1), "Decision 2")
manager.store(VectorCoordinate(3, 2, 1), "Decision 3")

# Sync to Git periodically
manager.sync()

# After restart or git pull
manager.load_from_git()
```

### Pattern 4: Immutability Enforcement

```python
# Store architecture decision
coord = VectorCoordinate(x=5, y=2, z=1)
manager.store(coord, "Original decision")

# Try to modify it (will fail)
try:
    manager.store(coord, "Modified decision")
except ImmutableLayerError as e:
    print(f"Cannot modify: {e}")

# Can modify other layers
coord2 = VectorCoordinate(x=5, y=2, z=3)
manager.store(coord2, "Implementation v1")
manager.store(coord2, "Implementation v2")  # OK, z=3 is mutable
```

---

## Performance Guarantees

| Operation | Time Complexity | Performance Target |
|-----------|----------------|-------------------|
| store() | O(1) | < 50ms (99th percentile) |
| get() | O(1) | < 50ms (99th percentile) |
| exists() | O(1) | < 10ms |
| query_range() | O(n) | < 100ms for n < 100 |
| query_partial_order() | O(m) | < 100ms for m < 1000 |
| search_content() | O(k) | < 200ms for k < 10000 |
| sync() | O(d) | < 5s for d < 1000 |
| load_from_git() | O(d) | < 10s for d < 10000 |

Where:
- n = result set size
- m = total coordinates in index
- k = total decisions in system
- d = number of decisions being synced/loaded

---

## Contract Version

**Version**: 1.0.0
**Status**: Stable
**Breaking Changes**: None (initial version)

**Changelog**:
- 2025-01-06: Initial API contract defined

---

## Testing Contract

All implementations MUST pass the following test scenarios:

1. **Basic Storage**: Store and retrieve at all (x,y,z) combinations
2. **Immutability**: Verify z=1 cannot be modified
3. **Concurrency**: Multiple agents storing to different coordinates simultaneously
4. **Queries**: Range, partial order, and content search correctness
5. **Git Sync**: Store → sync → restart → load → verify all decisions present
6. **Error Handling**: All specified exceptions raised for invalid inputs
7. **Performance**: All operations meet performance targets under load

---

## Future API Additions (V2+)

Potential additions for future versions (NOT in MVP):

- `delete()` - Soft delete for non-architecture layers
- `query_history()` - Retrieve version history for a coordinate
- `export()` - Export decisions to external format
- `import_()` - Import decisions from external format
- `optimize()` - Compact and optimize storage
- `statistics()` - Get memory usage statistics

These are NOT part of v1.0.0 contract and should not be implemented yet.

---

**Contract Complete**: Ready for implementation and testing.
