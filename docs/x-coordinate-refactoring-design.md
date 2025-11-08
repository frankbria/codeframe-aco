# X-Coordinate Refactoring Design

**Issue**: codeframe-aco-slf
**Status**: In Progress
**Goal**: Migrate VectorCoordinate.x from `int` to Beads issue ID `str`

## Design Decisions

### 1. Beads ID Format

**Pattern**: `{project-prefix}-{hash}`
- Example: `"codeframe-aco-t49"`, `"codeframe-aco-xon"`
- Regex: `^[\w-]+-[a-z0-9]{3}$`

**Validation**:
```python
def validate_beads_id(issue_id: str) -> None:
    """Validate Beads issue ID format."""
    if not re.match(r'^[\w-]+-[a-z0-9]{3}$', issue_id):
        raise CoordinateValidationError(
            f"Invalid Beads issue ID format: {issue_id}. "
            f"Expected format: 'project-prefix-xxx' (e.g., 'codeframe-aco-t49')"
        )
```

### 2. Partial Ordering with DAG

**Problem**: `PartialOrder.less_than()` currently uses numeric comparison `x1 < x2`.

**Solution**: Add optional DAG ordering parameter with sensible defaults.

```python
class PartialOrder:
    @staticmethod
    def less_than(
        coord1: tuple[str, int],
        coord2: tuple[str, int],
        dag_order: dict[str, int] | None = None
    ) -> bool:
        """
        Check if coord1 < coord2 in partial order.

        Args:
            coord1: (issue_id, cycle_stage)
            coord2: (issue_id, cycle_stage)
            dag_order: Maps issue_id → topological position
                      If None, uses lexicographic string ordering
        """
        x1, y1 = coord1
        x2, y2 = coord2

        # Determine x-ordering
        if dag_order is not None:
            # Use topological sort positions
            x1_pos = dag_order.get(x1, float('inf'))
            x2_pos = dag_order.get(x2, float('inf'))
            x_less = x1_pos < x2_pos
            x_equal = x1 == x2
        else:
            # Fallback: lexicographic string ordering
            x_less = x1 < x2
            x_equal = x1 == x2

        return x_less or (x_equal and y1 < y2)
```

**Why this approach**:
- Works without Beads integration (uses string ordering)
- Enables proper DAG ordering when available
- No tight coupling to BeadsClient
- Tests can pass with or without DAG data

### 3. File Path Migration

**Old format**: `.vector-memory/x-005/y-2-z-1.json`
**New format**: `.vector-memory/x-codeframe-aco-t49/y-2-z-1.json`

```python
def to_path(self) -> Path:
    """Convert to file system path."""
    return Path(f".vector-memory/x-{self.x}/y-{self.y}-z-{self.z}.json")
```

**Migration script**:
```python
def migrate_vector_memory(
    repo_path: Path,
    issue_mapping: dict[int, str]
) -> int:
    """
    Migrate from integer x-coordinates to Beads IDs.

    Args:
        repo_path: Repository root
        issue_mapping: {1: "codeframe-aco-t49", 2: "codeframe-aco-xon", ...}

    Returns:
        Number of files migrated
    """
    vm_dir = repo_path / ".vector-memory"
    if not vm_dir.exists():
        return 0

    migrated = 0
    for old_dir in vm_dir.glob("x-*"):
        # Parse integer from directory name
        match = re.match(r'x-(\d+)', old_dir.name)
        if not match:
            continue  # Already migrated or invalid

        x_int = int(match.group(1))
        issue_id = issue_mapping.get(x_int)

        if issue_id:
            new_dir = vm_dir / f"x-{issue_id}"
            old_dir.rename(new_dir)
            migrated += 1
            logger.info(f"Migrated {old_dir} → {new_dir}")

    return migrated
```

### 4. Test Fixture Strategy

**Create test helper**:
```python
# tests/conftest.py

MOCK_BEADS_IDS = [
    f"test-issue-{chr(97 + i // 26)}{chr(97 + i % 26)}{i % 10}"
    for i in range(1000)
]
# Generates: test-issue-aa0, test-issue-aa1, ..., test-issue-zz9

@pytest.fixture
def mock_issue_id():
    """Get mock Beads issue ID for tests."""
    def _get_id(index: int) -> str:
        if index < len(MOCK_BEADS_IDS):
            return MOCK_BEADS_IDS[index]
        raise ValueError(f"Index {index} out of range")
    return _get_id

@pytest.fixture
def mock_dag_order():
    """Get mock DAG ordering for tests."""
    return {issue_id: i for i, issue_id in enumerate(MOCK_BEADS_IDS)}
```

**Update tests**:
```python
# OLD
def test_store_decision():
    coord = VectorCoordinate(x=5, y=2, z=1)
    manager.store(coord, "content")

# NEW
def test_store_decision(mock_issue_id):
    coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
    manager.store(coord, "content")
```

### 5. Backwards Compatibility

**Decision**: NO backwards compatibility during development.

**Rationale**:
- This is pre-1.0, still in MVP phase
- No production users yet
- Clean migration is simpler than hybrid support
- Reduces technical debt

**Migration for existing dev work**:
- Create mapping file: `.vector-memory-migration.json`
- Run migration script once per repository
- Commit migrated data

## Implementation Plan

### Phase 1: Core Changes (1 day)
1. Update `VectorCoordinate.x` type annotation
2. Update validation logic
3. Update `to_path()` formatting
4. Update `from_path()` parsing
5. Update `PartialOrder.less_than()` signature

### Phase 2: Propagate Changes (1 day)
1. Update `VectorMemoryManager` - no changes needed (type-agnostic)
2. Update `MemoryIndex` - dict keys already support strings
3. Update `query.py` - add `dag_order` parameter to query methods
4. Update all type hints throughout codebase

### Phase 3: Test Updates (1.5 days)
1. Create mock Beads ID fixtures in conftest.py
2. Update all unit tests (69 tests)
3. Update all integration tests (62 tests)
4. Update property-based tests (9 tests)
5. Update performance tests (8 tests)

### Phase 4: Migration Tool (0.5 days)
1. Create migration script
2. Test on sample data
3. Add CLI: `python -m vector_memory.migrate`

**Total**: ~4 days

## Risks & Mitigations

### Risk 1: Tests break during migration
**Mitigation**: Update tests incrementally by module, run suite after each module

### Risk 2: DAG ordering not available during testing
**Mitigation**: Fallback to lexicographic ordering when `dag_order=None`

### Risk 3: File path compatibility issues
**Mitigation**: Thoroughly test `from_path()` regex with new format

## Success Criteria

- [ ] All 183 tests pass with new Beads ID-based coordinates
- [ ] `VectorCoordinate.x` accepts only valid Beads ID format
- [ ] Partial ordering works with and without DAG data
- [ ] File paths use new format: `.vector-memory/x-{issue_id}/`
- [ ] Migration script successfully converts test data
- [ ] No runtime errors in any component
- [ ] Performance remains within spec thresholds
