# Implementation Plan: Vector Memory Manager

**Branch**: `001-vector-memory` | **Date**: 2025-01-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-vector-memory/spec.md`

## Summary

The Vector Memory Manager is a coordinate-based storage system that enables AI agents to store and retrieve decisions using 3D coordinates (x=issue, y=cycle stage, z=memory layer). This system provides precise context management without window pollution, enforces architectural immutability (z=1 layer), persists to Git for durability, and supports partial ordering queries for intelligent rollback.

**Primary Requirements**:
- Store/retrieve information at 3D coordinates (x, y, z)
- Enforce immutability of architecture layer (z=1)
- Persist to Git in structured format
- Support coordinate-based queries and partial ordering
- Handle concurrent access without corruption

**Technical Approach**:
File-based storage with JSON serialization, Git-backed persistence, in-memory index for fast lookup, and lock-free concurrent access patterns.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- No external dependencies for core (stdlib only for MVP)
- Git CLI for persistence
- JSON for serialization

**Storage**: File system + Git (structured JSON files in `.vector-memory/` directory)
**Testing**: pytest with property-based testing (hypothesis) for coordinate validation
**Target Platform**: Cross-platform (Linux, macOS, Windows) - anywhere Git + Python runs
**Project Type**: Single library project (Python package)
**Performance Goals**:
- <50ms for 99% of store/retrieve operations
- <100ms for partial ordering queries (up to 100 issues)
- <5s for Git synchronization (up to 1000 decisions)

**Constraints**:
- Maximum 1000 issues per project (MVP limit)
- Maximum 10,000 stored decisions
- File system must support atomic writes
- Git repository must be initialized

**Scale/Scope**:
- Single project/repository scope
- Up to 10 concurrent agent processes
- Up to 1000 decisions per Git sync

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md` principles:

- [x] **Vector Memory Architecture**: Design implements THE coordinate-based storage system itself - this IS the vector memory architecture
- [x] **DAG-Driven Development**: All work tracked in Beads (issue codeframe-aco-t49), dependencies on Beads Integration Layer documented
- [x] **Unified Development Cycle**: Plan follows Architect (this phase) → Test (Phase 2) → Implement (Phase 2) → Review → Merge
- [x] **Test-First Development**: Tests will be written before implementation in Phase 2, targeting 80%+ coverage with property-based testing
- [x] **Autonomous Operation**: No human escalation needed for this foundational component (deterministic behavior)
- [x] **Scope Control**: Feature scope clearly bounded in spec "Out of Scope" section, no scope creep
- [x] **Observability**: Metadata tracking (timestamps, agent IDs) built into StoredDecision entity, Git provides audit trail

**Result**: ✅ ALL GATES PASSED - No constitutional violations

## Project Structure

### Documentation (this feature)

```text
specs/001-vector-memory/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (technology decisions, patterns)
├── data-model.md        # Phase 1 output (entity definitions)
├── quickstart.md        # Phase 1 output (usage guide)
├── contracts/           # Phase 1 output (API contracts)
│   └── memory-api.md   # Core API contract
├── checklists/
│   └── requirements.md  # Spec validation checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created yet)
```

### Source Code (repository root)

```text
src/
├── vector_memory/
│   ├── __init__.py           # Package exports
│   ├── coordinate.py         # VectorCoordinate class
│   ├── storage.py            # StoredDecision, MemoryLayer classes
│   ├── manager.py            # VectorMemoryManager (main API)
│   ├── query.py              # Query operations (range, partial order, content search)
│   ├── persistence.py        # Git synchronization
│   └── validation.py         # Coordinate validation, concurrency control

tests/
├── unit/
│   ├── test_coordinate.py
│   ├── test_storage.py
│   ├── test_manager.py
│   ├── test_query.py
│   ├── test_persistence.py
│   └── test_validation.py
├── integration/
│   ├── test_git_sync.py
│   ├── test_concurrent_access.py
│   └── test_end_to_end.py
└── property/
    ├── test_coordinate_properties.py  # Property-based tests with hypothesis
    └── test_partial_order_properties.py
```

**Structure Decision**: Single library project chosen because:
- Core infrastructure component (not user-facing application)
- No frontend/backend split needed
- Will be imported by other ACO components (DAG Orchestrator, Cycle Processor)
- Python package structure supports clean imports and testing

## Complexity Tracking

> **No constitutional violations - this section left empty**

## Phase 0: Research & Technology Decisions

**Status**: ✅ Complete
**Output**: research.md

### Research Tasks Completed

1. **Storage Format Decision**
2. **Concurrency Strategy**
3. **Git Integration Pattern**
4. **Query Performance Optimization**
5. **Partial Ordering Implementation**

See [research.md](research.md) for detailed findings and rationale.

## Phase 1: Design & Contracts

**Status**: ✅ Complete
**Prerequisites**: research.md complete
**Outputs**:
- data-model.md (entity definitions)
- contracts/memory-api.md (API contract)
- quickstart.md (usage guide)
- Agent context updated

### Design Decisions

1. **Entity Model**: Four core entities (VectorCoordinate, StoredDecision, MemoryLayer, PartialOrder)
2. **API Contract**: Functional API with explicit coordinate passing
3. **Git Structure**: `.vector-memory/` directory with coordinate-organized JSON files

See [data-model.md](data-model.md) and [contracts/memory-api.md](contracts/memory-api.md) for details.

### Constitution Re-Check (Post-Design)

- [x] **Vector Memory Architecture**: Design fully implements 3D coordinate system with all required operations
- [x] **DAG-Driven Development**: Integrated with Beads via x-coordinate (issue number)
- [x] **Test-First Development**: Test structure planned, property-based testing strategy defined
- [x] **Observability**: Metadata and Git history provide full audit trail

**Result**: ✅ ALL GATES STILL PASSING

## Phase 2: Task Generation

**Status**: ⏸️ Pending
**Next Command**: `/speckit.tasks`

This phase will generate tasks.md with dependency-ordered implementation tasks based on the design artifacts created in Phase 0 and Phase 1.

## Dependencies

### External Dependencies

- **Beads Integration Layer** (codeframe-aco-xon): Provides issue number (x-coordinate) mapping
- **Git**: Version control system for persistence
- **Python 3.11+**: Runtime environment

### Internal Dependencies (within this feature)

- coordinate.py → (no internal deps)
- storage.py → coordinate.py
- validation.py → coordinate.py
- query.py → storage.py, coordinate.py
- persistence.py → storage.py, coordinate.py
- manager.py → ALL above modules

## Success Criteria Validation

All success criteria from spec.md are achievable with this design:

- **SC-001** (< 50ms operations): In-memory index + file I/O achievable
- **SC-002** (100% accuracy): Deterministic coordinate-based lookup
- **SC-003** (100% immutability): Enforced by validation.py layer checks
- **SC-004** (10K decisions): File-based storage scales to this size
- **SC-005** (< 5s Git sync): Batch operations, incremental commits
- **SC-006** (< 10s recovery): Load from JSON files, rebuild index
- **SC-007** (< 100ms partial order): In-memory comparison, pre-computed ordering
- **SC-008** (< 200ms content search): Full-text index on decision content
- **SC-009** (Zero data loss): File locking + atomic writes
- **SC-010** (< 5 lookups): Efficient query API minimizes round trips

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| File system lock contention | Medium | Medium | Use lock-free reads, short write locks |
| Git merge conflicts | Low | High | Single-writer pattern, coordinate-based file names |
| Performance degradation at scale | Medium | Medium | Implement lazy loading, index optimization |
| Coordinate validation bugs | Medium | High | Property-based testing with hypothesis |

### Mitigation Strategies

1. **Concurrency**: Lock-free reads (immutable data), optimistic locking for writes
2. **Git Conflicts**: Coordinate-based file naming prevents conflicts, single-writer per coordinate
3. **Performance**: In-memory index, lazy loading, incremental Git operations
4. **Correctness**: Property-based testing, extensive unit tests, integration tests

## Next Steps

1. Run `/speckit.tasks` to generate implementation tasks
2. Implement following test-first development (TDD)
3. Start with coordinate.py and storage.py (foundation)
4. Build up to manager.py (integration)
5. Comprehensive testing at each layer

---

**Planning Complete**: ✅
**Ready for**: `/speckit.tasks` command to generate actionable implementation tasks
