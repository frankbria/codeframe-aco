# Research: Vector Memory Manager

**Feature**: Vector Memory Manager
**Branch**: 001-vector-memory
**Date**: 2025-01-06
**Status**: Complete

## Overview

This document captures technology decisions, architectural patterns, and best practices research for implementing the Vector Memory Manager component.

## Research Areas

### 1. Storage Format Decision

**Question**: How should we store vector memory data for optimal performance, durability, and human readability?

**Alternatives Considered**:

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **JSON files** (per coordinate) | Human-readable, Git-friendly, no dependencies, simple | File system overhead for many files | ✅ **CHOSEN** |
| SQLite database | Query performance, ACID transactions | Binary format (not Git-friendly), adds dependency | Rejected |
| Binary protocol buffers | Compact, fast deserialization | Not human-readable, tooling required | Rejected |
| Single JSON file | Simple, atomic writes | Large file size, merge conflicts | Rejected |

**Decision**: **JSON files organized by coordinates**

**Rationale**:
- **Human-readable**: Developers and AI agents can inspect decisions directly
- **Git-friendly**: Text diffs work, merge conflicts are manageable
- **No dependencies**: Pure Python stdlib (json module)
- **Coordinate-based organization**: `.vector-memory/x-{issue}/y-{stage}/z-{layer}.json`
- **Performance acceptable**: For MVP scale (1000 issues, 10K decisions), file I/O is sufficient

**File Organization**:
```
.vector-memory/
├── x-001/
│   ├── y-2-z-1.json  # Issue 1, architect stage, architecture layer
│   └── y-3-z-3.json  # Issue 1, implement stage, implementation layer
├── x-002/
│   ├── y-2-z-1.json
│   └── y-4-z-2.json
└── index.json        # Fast lookup index (optional optimization)
```

---

### 2. Concurrency Strategy

**Question**: How should we handle concurrent access from multiple AI agents without data corruption?

**Alternatives Considered**:

| Strategy | Pros | Cons | Decision |
|----------|------|------|----------|
| **File locking** (fcntl/lockfile) | Simple, OS-supported | Platform differences, deadlock risk | ✅ **CHOSEN** for writes |
| **Lock-free reads** | High performance | Requires careful design | ✅ **CHOSEN** for reads |
| **Database transactions** | ACID guarantees | Requires SQLite dependency | Rejected |
| **Single writer process** | No conflicts | Limits parallelism | Rejected for MVP |

**Decision**: **Lock-free reads + File locking for writes**

**Rationale**:
- **Reads are lock-free**: Immutable data (especially z=1) can be read without locks
- **Writes use file locks**: Python's `filelock` library for cross-platform file locking
- **Optimistic concurrency**: Check-before-write pattern for non-z=1 layers
- **Performance**: Reads (majority of operations) are not blocked

**Implementation Pattern**:
```python
# Read (lock-free)
def get_decision(coord):
    path = coord.to_path()
    with open(path) as f:
        return json.load(f)

# Write (with lock)
def store_decision(coord, decision):
    if coord.z == 1 and coord.exists():
        raise ImmutableLayerError()

    lock_path = coord.to_lock_path()
    with FileLock(lock_path):
        # Atomic write pattern
        temp_path = coord.to_temp_path()
        with open(temp_path, 'w') as f:
            json.dump(decision, f)
        os.rename(temp_path, coord.to_path())
```

---

### 3. Git Integration Pattern

**Question**: How should we persist vector memory to Git for durability and collaboration?

**Alternatives Considered**:

| Pattern | Pros | Cons | Decision |
|---------|------|------|----------|
| **Auto-commit on write** | Always in sync | Too many commits, performance hit | Rejected |
| **Manual sync command** | User control, batched | Requires explicit call | ✅ **CHOSEN** |
| **Periodic background sync** | Automatic, batched | Complexity, timing issues | Rejected for MVP |
| **Git hooks** | Automatic on git operations | Hard to debug, platform-specific | Rejected |

**Decision**: **Manual synchronization with explicit `sync()` method**

**Rationale**:
- **Explicit control**: Agents call `memory.sync()` after logical units of work
- **Batched commits**: Multiple decisions committed together, reducing Git overhead
- **Atomic operations**: All changes in `.vector-memory/` committed atomically
- **Performance**: Avoids commit-per-write overhead
- **Recovery**: On startup, load from `.vector-memory/` if more recent than in-memory state

**API Pattern**:
```python
class VectorMemoryManager:
    def sync(self) -> None:
        """Synchronize in-memory state to Git."""
        # 1. Write all dirty decisions to files
        # 2. Git add .vector-memory/
        # 3. Git commit with metadata
        # 4. Mark all decisions as clean
        pass

    def load_from_git(self) -> None:
        """Load vector memory from Git on initialization."""
        # 1. Check if .vector-memory/ exists
        # 2. Load all JSON files
        # 3. Rebuild in-memory index
        pass
```

**Git Commit Message Format**:
```
vector-memory: sync {count} decisions

Coordinates: (x,y,z) ranges affected
Agent: {agent_id}
Timestamp: {iso8601}
```

---

### 4. Query Performance Optimization

**Question**: How can we achieve sub-100ms query performance for partial ordering and range queries?

**Alternatives Considered**:

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **In-memory index** | Fast lookups, simple | Memory overhead | ✅ **CHOSEN** |
| **File system scanning** | No memory overhead | Too slow for queries | Rejected |
| **SQLite index** | Query optimization built-in | Adds dependency, complexity | Rejected for MVP |
| **Cached queries** | Speeds up repeated queries | Stale cache issues | Maybe for V2 |

**Decision**: **In-memory index with lazy loading**

**Rationale**:
- **Fast lookups**: O(1) coordinate access, O(n) range scans (n = result size)
- **Memory efficient**: Only store coordinates + metadata in index, load full decisions on demand
- **Simple**: Python dict with tuple keys `(x, y, z) -> file_path`
- **Rebuilds quickly**: Loading 10K coordinate tuples takes < 1 second

**Index Structure**:
```python
class MemoryIndex:
    def __init__(self):
        self.coords = {}  # (x,y,z) -> file_path
        self.metadata = {}  # (x,y,z) -> {timestamp, agent_id}
        self.content_index = {}  # word -> set((x,y,z))

    def add(self, coord, metadata):
        self.coords[coord] = coord.to_path()
        self.metadata[coord] = metadata
        # Build content index for fast search

    def query_range(self, x_range, y_range, z_range):
        # Filter coords by ranges
        matching = [c for c in self.coords
                    if c[0] in x_range
                    and c[1] in y_range
                    and c[2] in z_range]
        return matching

    def query_partial_order(self, x1, y1):
        # Find all (x,y,z) where (x,y) < (x1,y1)
        return [c for c in self.coords
                if c[0] < x1 or (c[0] == x1 and c[1] < y1)]
```

---

### 5. Partial Ordering Implementation

**Question**: How should we implement partial ordering on (x,y) vectors for rollback support?

**Definition**: `(x, y) < (x₁, y₁)` if and only if `(x < x₁) OR (x = x₁ AND y < y₁)`

**Implementation Approach**: **Lexicographic comparison**

**Rationale**:
- **Simple**: Python tuple comparison already implements lexicographic ordering
- **Correct**: `(x, y) < (x₁, y₁)` matches mathematical definition
- **Efficient**: O(1) comparison using built-in tuple comparison

**Implementation**:
```python
class PartialOrder:
    @staticmethod
    def less_than(coord1: Tuple[int, int], coord2: Tuple[int, int]) -> bool:
        """Check if coord1 < coord2 in partial order."""
        x1, y1 = coord1
        x2, y2 = coord2
        return x1 < x2 or (x1 == x2 and y1 < y2)

    @staticmethod
    def comparable(coord1: Tuple[int, int], coord2: Tuple[int, int]) -> bool:
        """Check if coord1 and coord2 are comparable."""
        return (coord1 <= coord2) or (coord2 <= coord1)

    @staticmethod
    def find_before(coords: List[Tuple], threshold: Tuple[int, int]) -> List[Tuple]:
        """Find all coordinates before threshold in partial order."""
        return [c for c in coords if PartialOrder.less_than(c[:2], threshold)]
```

**Edge Cases Handled**:
- **Incomparable coordinates**: (3,4) and (5,2) are neither < nor > each other
- **Equal coordinates**: (5,3) == (5,3) is not < but is <=
- **Z-coordinate independence**: Partial ordering only applies to (x,y), z is independent

---

## Best Practices Applied

### Python Best Practices

1. **Type hints**: Use `typing` module for all public APIs
2. **Dataclasses**: Use `@dataclass` for VectorCoordinate and StoredDecision
3. **Path handling**: Use `pathlib.Path` for cross-platform file operations
4. **Context managers**: Use `with` statements for file operations
5. **Error handling**: Define custom exceptions (`ImmutableLayerError`, `CoordinateValidationError`)

### Testing Strategy

1. **Unit tests**: Test each module independently (pytest)
2. **Property-based tests**: Use `hypothesis` library for coordinate validation
3. **Integration tests**: Test Git synchronization and concurrent access
4. **Test coverage**: Target 80%+ line coverage, 100% for critical paths

**Example Property Test**:
```python
from hypothesis import given, strategies as st

@given(
    x=st.integers(min_value=1, max_value=1000),
    y=st.integers(min_value=1, max_value=5),
    z=st.integers(min_value=1, max_value=4)
)
def test_coordinate_roundtrip(x, y, z):
    coord = VectorCoordinate(x, y, z)
    path = coord.to_path()
    parsed = VectorCoordinate.from_path(path)
    assert parsed == coord
```

### Git Best Practices

1. **Atomic commits**: All `.vector-memory/` changes in single commit
2. **Descriptive messages**: Include coordinate ranges and decision counts
3. **Gitignore**: Add `.vector-memory/*.lock` (lock files should not be committed)
4. **Pre-commit hooks**: Validate JSON files before commit (optional)

---

## Open Questions (Resolved)

All questions were resolved during research. No blockers remain for Phase 1 design.

---

## Dependencies

- **Python 3.11+**: For type hints, dataclasses, pathlib
- **Git**: For version control and persistence
- **pytest**: For testing framework
- **hypothesis**: For property-based testing (dev dependency)
- **filelock**: For cross-platform file locking (to be added)

---

## Performance Estimates

Based on research findings and assumptions:

| Operation | Target | Estimated | Notes |
|-----------|--------|-----------|-------|
| Store decision | < 50ms | 10-30ms | File write + index update |
| Retrieve decision | < 50ms | 5-15ms | Index lookup + file read |
| Range query | < 100ms | 20-50ms | Index scan + file reads |
| Partial order query | < 100ms | 30-60ms | Index filter + file reads |
| Content search | < 200ms | 50-150ms | Content index lookup |
| Git sync | < 5s | 1-3s | Batch commit, 100-1000 decisions |
| Recovery (load from Git) | < 10s | 3-7s | Load + rebuild index |

All targets achievable with proposed design.

---

## Conclusion

Research complete. All technology decisions made. Ready to proceed to Phase 1 (Design & Contracts).

**Key Decisions Summary**:
1. ✅ JSON files organized by coordinates
2. ✅ Lock-free reads + file locking for writes
3. ✅ Manual Git synchronization
4. ✅ In-memory index with lazy loading
5. ✅ Lexicographic partial ordering

**No blockers**. Phase 1 can begin.
