# Data Model: Vector Memory Manager

**Feature**: Vector Memory Manager
**Branch**: 001-vector-memory
**Date**: 2025-01-06
**Status**: Complete

## Overview

This document defines the core entities, their attributes, relationships, and validation rules for the Vector Memory Manager system.

## Core Entities

### 1. VectorCoordinate

Represents a position in 3D space used to address stored information.

**Attributes**:
- `x` (integer): Issue number in the DAG (range: 1-1000 for MVP)
- `y` (integer): Development cycle stage (1=architect, 2=test, 3=implement, 4=review, 5=merge)
- `z` (integer): Memory layer (1=Architecture, 2=Interfaces, 3=Implementation, 4=Ephemeral)

**Validation Rules**:
- `x` must be >= 1 and <= 1000
- `y` must be in {1, 2, 3, 4, 5}
- `z` must be in {1, 2, 3, 4}
- All values must be integers

**Operations**:
- `to_tuple()`: Returns `(x, y, z)` tuple
- `to_path()`: Converts to file system path `.vector-memory/x-{x}/y-{y}-z-{z}.json`
- `from_path(path)`: Parses coordinate from file path
- `__eq__`, `__hash__`: Enable use as dictionary keys
- `__lt__`: Enables sorting (lexicographic on (x,y,z))

**Example**:
```python
coord = VectorCoordinate(x=5, y=2, z=1)  # Issue 5, architect stage, architecture layer
assert coord.to_path() == Path(".vector-memory/x-005/y-2-z-1.json")
assert coord.to_tuple() == (5, 2, 1)
```

---

### 2. StoredDecision

Information stored at a specific coordinate, including content and metadata.

**Attributes**:
- `coordinate` (VectorCoordinate): Where this decision is stored
- `content` (string): The actual decision text (UTF-8)
- `timestamp` (datetime): When the decision was stored (ISO 8601)
- `agent_id` (string): Identifier of the agent that stored this decision
- `issue_context` (dict): Additional context about the issue (optional)
  - `issue_id`: Beads issue ID (e.g., "codeframe-aco-t49")
  - `issue_title`: Human-readable title
  - `cycle_stage_name`: Human-readable stage name (e.g., "architect")

**Validation Rules**:
- `content` must not be empty string
- `content` length <= 100KB (prevents massive decisions)
- `timestamp` must be valid ISO 8601 datetime
- `agent_id` must not be empty string
- `coordinate` must be a valid VectorCoordinate

**Operations**:
- `to_json()`: Serialize to JSON dict
- `from_json(data)`: Deserialize from JSON dict
- `to_file(path)`: Write to JSON file with pretty-printing
- `from_file(path)`: Read from JSON file

**JSON Structure**:
```json
{
  "coordinate": {
    "x": 5,
    "y": 2,
    "z": 1
  },
  "content": "Use PostgreSQL for persistence layer",
  "timestamp": "2025-01-06T15:30:00Z",
  "agent_id": "claude-code-01",
  "issue_context": {
    "issue_id": "codeframe-aco-t49",
    "issue_title": "Vector Memory Manager",
    "cycle_stage_name": "architect"
  }
}
```

---

### 3. MemoryLayer

Represents one of the four memory layers with different mutability characteristics.

**Attributes**:
- `z` (integer): Layer number (1-4)
- `name` (string): Layer name
- `is_immutable` (boolean): Whether layer can be modified after storage

**Layer Definitions**:

| Z | Name | Immutable | Purpose |
|---|------|-----------|---------|
| 1 | Architecture | ✅ Yes | Foundational decisions that must never change |
| 2 | Interfaces | ❌ No | API contracts, data schemas (can evolve) |
| 3 | Implementation | ❌ No | Code details, algorithms (frequently change) |
| 4 | Ephemeral | ❌ No | Temporary notes, work-in-progress (transient) |

**Validation Rules**:
- Layer 1 (Architecture): Once stored at a coordinate, cannot be modified or deleted
- Layers 2-4: Can be overwritten (with versioning via Git)
- All layers: Cannot delete decisions, only overwrite

**Operations**:
- `get_layer(z)`: Returns MemoryLayer object for given z value
- `validate_write(coord, existing)`: Checks if write is allowed
- `validate_delete(coord)`: Checks if delete is allowed (always False)

**Immutability Enforcement**:
```python
class MemoryLayer:
    ARCHITECTURE = MemoryLayer(z=1, name="Architecture", is_immutable=True)
    INTERFACES = MemoryLayer(z=2, name="Interfaces", is_immutable=False)
    IMPLEMENTATION = MemoryLayer(z=3, name="Implementation", is_immutable=False)
    EPHEMERAL = MemoryLayer(z=4, name="Ephemeral", is_immutable=False)

    def validate_write(self, coord, existing_decision):
        if self.is_immutable and existing_decision is not None:
            raise ImmutableLayerError(
                f"Cannot modify decision at {coord} in {self.name} layer"
            )
```

---

### 4. PartialOrder

Mathematical ordering relationship on (x,y) coordinate pairs.

**Purpose**: Enable intelligent rollback by identifying decisions that occurred "before" a specific point in the DAG × cycle space.

**Definition**: `(x, y) < (x₁, y₁)` if and only if:
- `x < x₁` (earlier issue), OR
- `x == x₁ AND y < y₁` (same issue, earlier stage)

**Attributes**: None (utility class with static methods)

**Operations**:
- `less_than(coord1, coord2)`: Returns True if coord1 < coord2
- `less_equal(coord1, coord2)`: Returns True if coord1 <= coord2
- `comparable(coord1, coord2)`: Returns True if coordinates are comparable
- `find_before(coords, threshold)`: Filters list to coordinates before threshold

**Properties**:
- **Reflexive**: `(x,y) <= (x,y)` is always True
- **Antisymmetric**: If `(x,y) <= (x₁,y₁)` and `(x₁,y₁) <= (x,y)`, then `(x,y) == (x₁,y₁)`
- **Transitive**: If `(x,y) < (x₁,y₁)` and `(x₁,y₁) < (x₂,y₂)`, then `(x,y) < (x₂,y₂)`
- **Not Total**: Some coordinate pairs are incomparable (e.g., (3,4) and (5,2))

**Examples**:
```python
# Comparable coordinates
assert PartialOrder.less_than((1, 2), (3, 4))  # True: x1 < x2
assert PartialOrder.less_than((5, 2), (5, 3))  # True: same x, y1 < y2
assert PartialOrder.less_than((5, 3), (5, 2))  # False

# Incomparable coordinates
assert PartialOrder.comparable((3, 4), (5, 2))  # False: neither < nor >
assert PartialOrder.less_than((3, 4), (5, 2))   # False
assert PartialOrder.less_than((5, 2), (3, 4))   # False
```

**Rollback Use Case**:
```python
# Find all decisions before error at (7, 4)
error_coord = (7, 4)
all_coords = [(1,2), (3,2), (3,4), (5,2), (5,3), (7,2), (7,4)]
before_error = PartialOrder.find_before(all_coords, error_coord)
# Result: [(1,2), (3,2), (3,4), (5,2), (5,3), (7,2)]
# Note: (7,4) not included, and incomparable coordinates like (3,4) and (5,2) both included
```

---

## Entity Relationships

### Composition

- **VectorMemoryManager** contains many **StoredDecision** objects
- **StoredDecision** contains one **VectorCoordinate**
- **VectorCoordinate** maps to one **MemoryLayer** (via z value)

### Aggregation

- **MemoryIndex** aggregates **VectorCoordinate** objects for fast lookup
- **PartialOrder** operates on collections of **(x,y)** tuples

### Dependency Graph

```
VectorMemoryManager
├── uses → VectorCoordinate (addressing)
├── uses → StoredDecision (storage)
├── uses → MemoryLayer (validation)
├── uses → PartialOrder (queries)
└── uses → MemoryIndex (performance)
```

---

## State Transitions

### StoredDecision Lifecycle

```
1. [Created] → Decision object instantiated
2. [Validated] → Coordinate and content validated
3. [Stored] → Written to file system + Git
4. [Indexed] → Added to in-memory index
5. [Retrievable] → Available for queries

# For non-immutable layers only:
6. [Updated] → Content modified (new version in Git)
7. [Superseded] → Older version still in Git history
```

### MemoryLayer State

```
Layer 1 (Architecture):
  [Empty] → [Stored] → [Immutable Forever]

Layers 2-4:
  [Empty] → [Stored] → [Updatable] ⟲ (can loop back to Stored)
```

---

## Validation Rules Summary

### At Storage Time

1. **Coordinate Validation**:
   - x in range [1, 1000]
   - y in {1, 2, 3, 4, 5}
   - z in {1, 2, 3, 4}

2. **Content Validation**:
   - Non-empty string
   - Length <= 100KB
   - Valid UTF-8 encoding

3. **Immutability Validation**:
   - If z=1 and coordinate exists → REJECT
   - If z≠1 and coordinate exists → ALLOW (overwrite)

4. **Metadata Validation**:
   - agent_id non-empty
   - timestamp valid ISO 8601
   - issue_context well-formed (if present)

### At Query Time

1. **Coordinate Existence**: Coordinate must exist in index
2. **Range Validity**: x_min <= x_max, y_min <= y_max, z_min <= z_max
3. **Partial Order**: Threshold coordinate must be valid

---

## Index Structure

### MemoryIndex Entity

```python
class MemoryIndex:
    """In-memory index for fast coordinate lookup."""

    # Primary index: coordinate → file path
    coords: Dict[Tuple[int, int, int], Path]

    # Metadata index: coordinate → metadata
    metadata: Dict[Tuple[int, int, int], dict]

    # Content index: word → set of coordinates (for content search)
    content_index: Dict[str, Set[Tuple[int, int, int]]]

    # Layer index: z → list of coordinates (optimization)
    layer_index: Dict[int, List[Tuple[int, int, int]]]
```

**Operations**:
- `add(coord, metadata)`: Add coordinate to all indexes
- `remove(coord)`: Remove coordinate from all indexes (metadata only, file persists)
- `query_exact(coord)`: O(1) lookup by exact coordinate
- `query_range(x_range, y_range, z_range)`: O(n) scan with filtering
- `query_partial_order(x_threshold, y_threshold)`: O(n) scan with ordering check
- `query_content(search_terms)`: O(k) where k = matching documents
- `rebuild()`: Reconstruct index from file system (recovery)

---

## File System Layout

### Directory Structure

```
.vector-memory/
├── x-001/
│   ├── y-1-z-1.json
│   ├── y-2-z-1.json
│   ├── y-3-z-3.json
│   └── y-4-z-2.json
├── x-002/
│   ├── y-2-z-1.json
│   └── y-3-z-3.json
├── x-003/
│   └── y-2-z-1.json
├── index.json (optional, for faster startup)
└── metadata.json (version info, project settings)
```

### File Naming Convention

- **Directory**: `x-{issue_number:03d}` (zero-padded to 3 digits)
- **File**: `y-{stage}-z-{layer}.json`
- **Lock files**: `y-{stage}-z-{layer}.lock` (not committed to Git)

### Index File (Optional Optimization)

```json
{
  "version": "1.0",
  "last_updated": "2025-01-06T15:30:00Z",
  "decision_count": 42,
  "coordinates": [
    {"x": 1, "y": 2, "z": 1, "path": ".vector-memory/x-001/y-2-z-1.json"},
    {"x": 1, "y": 3, "z": 3, "path": ".vector-memory/x-001/y-3-z-3.json"}
  ]
}
```

---

## Concurrency Model

### Read Operations (Lock-Free)

- Multiple agents can read simultaneously
- No locks required for reads
- Immutable data guarantees consistency

### Write Operations (File-Locked)

- One writer per coordinate at a time
- File lock acquired before write
- Atomic write via temp file + rename
- Lock released after write completes

### Lock Acquisition Order (Deadlock Prevention)

1. Sort coordinates lexicographically: `(x, y, z)`
2. Acquire locks in sorted order
3. Never acquire locks in reverse order
4. Timeout after 5 seconds → retry

---

## Error Conditions

### Custom Exceptions

```python
class VectorMemoryError(Exception):
    """Base exception for all vector memory errors."""

class CoordinateValidationError(VectorMemoryError):
    """Coordinate values out of range or invalid."""

class ImmutableLayerError(VectorMemoryError):
    """Attempt to modify immutable architecture layer (z=1)."""

class ConcurrencyError(VectorMemoryError):
    """Concurrent access conflict or lock timeout."""

class StorageError(VectorMemoryError):
    """File system or Git operation failed."""

class QueryError(VectorMemoryError):
    """Query parameters invalid or malformed."""
```

---

## Performance Characteristics

### Space Complexity

- **Per Decision**: ~1KB (JSON file)
- **Index**: ~100 bytes per coordinate (in-memory)
- **Total for 10K decisions**: ~10MB files + 1MB index = 11MB

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Store decision | O(1) | Write file + update index |
| Retrieve decision | O(1) | Index lookup + file read |
| Range query | O(n) | n = result set size |
| Partial order query | O(n) | n = total coordinates |
| Content search | O(m) | m = matching decisions |
| Index rebuild | O(n) | n = total decisions |

---

## Conclusion

Data model complete. All entities defined with attributes, validation rules, and relationships. Ready for API contract definition and implementation.
