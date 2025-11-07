# Quickstart Guide: Vector Memory Manager

**Feature**: Vector Memory Manager
**Branch**: 001-vector-memory
**Date**: 2025-01-06
**Audience**: Developers and AI agents using the Vector Memory Manager

## What is Vector Memory?

The Vector Memory Manager is a coordinate-based storage system that lets you store and retrieve decisions using 3D coordinates `(x, y, z)`:

- **x**: Issue number in the DAG (which issue)
- **y**: Development cycle stage (which stage: architect, test, implement, review, merge)
- **z**: Memory layer (which layer: Architecture, Interfaces, Implementation, Ephemeral)

**Key Feature**: The Architecture layer (z=1) is **immutable** - once you store a decision there, it can never be changed. This ensures consistency across the entire development lifecycle.

## Quick Start (5 Minutes)

### 1. Initialize the Manager

```python
from pathlib import Path
from vector_memory import VectorMemoryManager, VectorCoordinate

# Initialize with your repository path and agent ID
manager = VectorMemoryManager(
    repo_path=Path("/path/to/your/repo"),
    agent_id="claude-code-01"
)
```

### 2. Store a Decision

```python
# Define a coordinate (issue 5, architect stage, architecture layer)
coord = VectorCoordinate(x=5, y=2, z=1)

# Store a decision
decision = manager.store(
    coord=coord,
    content="Use PostgreSQL for persistence layer",
    issue_context={
        "issue_id": "codeframe-aco-t49",
        "issue_title": "Vector Memory Manager"
    }
)

print(f"Stored decision at {coord}")
```

### 3. Retrieve a Decision

```python
# Get the decision back
decision = manager.get(coord)

if decision:
    print(f"Found: {decision.content}")
    print(f"Stored by: {decision.agent_id}")
    print(f"At: {decision.timestamp}")
else:
    print("No decision at this coordinate")
```

### 4. Sync to Git

```python
# Commit all decisions to Git
manager.sync(message="Store architecture decisions for issue 5")
```

## Coordinate System Guide

### X-Axis: Issue Numbers

- Range: 1 to 1000 (MVP limit)
- Maps to Beads issue IDs
- Example: Issue `codeframe-aco-t49` might be x=1

### Y-Axis: Development Cycle Stages

| Y Value | Stage Name | When to Use |
|---------|-----------|-------------|
| 1 | Architect | During specification and design |
| 2 | Test | Writing tests before implementation |
| 3 | Implement | During actual code writing |
| 4 | Review | During code review and feedback |
| 5 | Merge | After merge, final notes |

### Z-Axis: Memory Layers

| Z Value | Layer Name | Mutable? | When to Use |
|---------|-----------|----------|-------------|
| 1 | Architecture | ❌ No | Foundational decisions (DB choice, API style, patterns) |
| 2 | Interfaces | ✅ Yes | API contracts, data schemas |
| 3 | Implementation | ✅ Yes | Code details, algorithms, optimizations |
| 4 | Ephemeral | ✅ Yes | Temporary notes, WIP, scratchpad |

**Important**: Layer 1 (Architecture) is **immutable** - you cannot modify or delete decisions once stored.

## Common Use Cases

### Use Case 1: Store Architectural Decision

```python
# At the start of issue 10, during architecture phase
coord = VectorCoordinate(x=10, y=2, z=1)
manager.store(coord, "Use REST API with JSON for all endpoints")

# This decision is now permanent and cannot be changed
```

### Use Case 2: Query Architecture Decisions

```python
# Get all architecture decisions for issues 1-20
arch_decisions = manager.query_range(
    x_range=(1, 20),
    z_range=(1, 1)  # Only z=1 (architecture layer)
)

for decision in arch_decisions:
    print(f"Issue {decision.coordinate.x}: {decision.content}")
```

### Use Case 3: Find Decisions for Rollback

```python
# Error occurred at issue 15, implement stage
# Find all decisions before this point
decisions_before = manager.query_partial_order(
    x_threshold=15,
    y_threshold=3  # Before implement stage
)

print(f"Found {len(decisions_before)} decisions to keep")
# Use this list to identify what to rollback to
```

### Use Case 4: Search for Specific Topics

```python
# Find all decisions about databases
db_decisions = manager.search_content(["database", "PostgreSQL", "SQL"])

for decision in db_decisions:
    print(f"[{decision.coordinate}] {decision.content}")
```

### Use Case 5: Update Implementation Details

```python
# Implementation details can be updated (z=3 is mutable)
coord = VectorCoordinate(x=10, y=3, z=3)

# First version
manager.store(coord, "Use simple linear search")
manager.sync()

# Later, optimize
manager.store(coord, "Use binary search for better performance")
manager.sync()

# Both versions preserved in Git history
```

## Common Patterns

### Pattern: Start of New Issue

```python
# When starting work on issue #42
issue_num = 42

# Store architectural decisions early
arch_coord = VectorCoordinate(x=issue_num, y=2, z=1)
manager.store(arch_coord, "Follow REST API patterns from issue #5")

# Store test decisions
test_coord = VectorCoordinate(x=issue_num, y=2, z=2)
manager.store(test_coord, "Test all endpoints with integration tests")

# Sync before implementation
manager.sync()
```

### Pattern: Context Retrieval for New Agent

```python
# Agent starting on issue #50 needs context
# Get all architecture decisions from previous issues
context = manager.query_range(
    x_range=(1, 49),  # All previous issues
    z_range=(1, 1)    # Only architecture
)

# Build context string for agent
context_text = "\n".join([
    f"Issue {d.coordinate.x}: {d.content}"
    for d in context
])
```

### Pattern: Checkpoint and Recovery

```python
# Before risky operation, record checkpoint
checkpoint_coord = VectorCoordinate(x=current_issue, y=current_stage, z=4)
manager.store(checkpoint_coord, f"Checkpoint before {operation_name}")
manager.sync()

# After operation, if something went wrong:
# Use query_partial_order to find decisions before checkpoint
# Rollback Git to that state
```

## Best Practices

### DO:

✅ **Store architecture decisions at z=1 early** - Lock in patterns before implementation
✅ **Use meaningful content** - Future agents will read these decisions
✅ **Sync after logical units of work** - After completing an issue or stage
✅ **Query context before starting work** - Avoid reinventing wheels
✅ **Use z=4 (Ephemeral) for temporary notes** - Clean up later

### DON'T:

❌ **Don't store code in decisions** - Store *decisions about* code, not code itself
❌ **Don't try to modify z=1** - It's immutable, will raise `ImmutableLayerError`
❌ **Don't sync after every single store** - Batch your work for performance
❌ **Don't store secrets** - Decisions are in Git, visible to all
❌ **Don't use huge content** - Keep decisions concise (< 1KB recommended)

## Error Handling

### Common Errors and Solutions

#### ImmutableLayerError

```python
try:
    coord = VectorCoordinate(x=5, y=2, z=1)
    manager.store(coord, "Modified decision")  # Fails if coord exists
except ImmutableLayerError:
    # Solution: Store at a different coordinate
    new_coord = VectorCoordinate(x=10, y=2, z=1)
    manager.store(new_coord, "New decision superseding old one")
```

#### CoordinateValidationError

```python
try:
    coord = VectorCoordinate(x=2000, y=2, z=1)  # x > 1000
except CoordinateValidationError as e:
    print(f"Invalid coordinate: {e}")
    # Solution: Use valid ranges (x: 1-1000, y: 1-5, z: 1-4)
```

#### StorageError

```python
try:
    manager.sync()
except StorageError as e:
    print(f"Git operation failed: {e}")
    # Solution: Check Git status, resolve conflicts, retry
```

## Integration with Beads

### Mapping Issue IDs to X-Coordinates

```python
# Beads issue: codeframe-aco-t49
# Maps to x-coordinate (you decide mapping)

# Simple approach: Use a mapping file
issue_to_x = {
    "codeframe-aco-t49": 1,
    "codeframe-aco-xon": 2,
    # ...
}

x = issue_to_x["codeframe-aco-t49"]
coord = VectorCoordinate(x=x, y=2, z=1)
```

## Performance Tips

### Tip 1: Batch Store Operations

```python
# Good: Store multiple, then sync once
for i in range(10):
    coord = VectorCoordinate(x=i, y=2, z=1)
    manager.store(coord, f"Decision {i}")
manager.sync()  # Single Git commit

# Avoid: Sync after each store
for i in range(10):
    coord = VectorCoordinate(x=i, y=2, z=1)
    manager.store(coord, f"Decision {i}")
    manager.sync()  # 10 Git commits (slower)
```

### Tip 2: Use Exact Lookups When Possible

```python
# Fast: O(1) exact lookup
decision = manager.get(VectorCoordinate(x=5, y=2, z=1))

# Slower: O(n) range query
decisions = manager.query_range(x_range=(5, 5), y_range=(2, 2), z_range=(1, 1))
```

### Tip 3: Filter Early with Z-Layer

```python
# Good: Filter to specific layer
arch = manager.query_range(x_range=(1, 100), z_range=(1, 1))  # Only z=1

# Avoid: Get all, filter later
all_decisions = manager.query_range(x_range=(1, 100))
arch = [d for d in all_decisions if d.coordinate.z == 1]  # Inefficient
```

## Troubleshooting

### Problem: "No such file or directory"

**Solution**: Make sure you've initialized the manager and called `load_from_git()`:
```python
manager = VectorMemoryManager(repo_path=Path.cwd(), agent_id="agent-01")
manager.load_from_git()  # Load existing decisions
```

### Problem: "Cannot modify immutable layer"

**Solution**: You're trying to modify z=1. Store at a new coordinate instead:
```python
# Don't modify old decision
# Create new decision that supersedes it
new_coord = VectorCoordinate(x=next_issue, y=2, z=1)
manager.store(new_coord, "Updated approach: ...")
```

### Problem: "Git repository not found"

**Solution**: Make sure you're in a Git repository:
```bash
git init  # If not already initialized
```

### Problem: Slow queries

**Solution**: Check your query ranges and consider:
- Using exact lookups instead of ranges
- Filtering by z-layer to reduce result set
- Rebuilding index if corrupted: `manager.load_from_git()`

## Next Steps

1. **Read the API Contract**: See `contracts/memory-api.md` for complete API reference
2. **Read the Data Model**: See `data-model.md` for entity definitions
3. **Run Tests**: See test examples in `tests/` directory (coming in Phase 2)
4. **Integrate with Your Code**: Import `VectorMemoryManager` and start using it

## Getting Help

- **API Reference**: See `contracts/memory-api.md`
- **Technical Details**: See `research.md` and `data-model.md`
- **Implementation**: See source code in `src/vector_memory/`
- **Issues**: Track in Beads (issue: codeframe-aco-t49)

---

**Happy coding with Vector Memory!** 🎯
