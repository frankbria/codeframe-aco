# Tasks: Vector Memory Manager

**Input**: Design documents from `/specs/001-vector-memory/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/memory-api.md

**Tests**: Per constitution Principle IV (Test-First Development), tests are REQUIRED with 80% minimum coverage. Tests MUST be written and approved before implementation begins (Red-Green-Refactor cycle).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a single library project (Python package):
- Source: `src/vector_memory/`
- Tests: `tests/unit/`, `tests/integration/`, `tests/property/`
- Configuration: Repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create directory structure: src/vector_memory/, tests/unit/, tests/integration/, tests/property/
- [ ] T002 Initialize Python package with setup.py or pyproject.toml
- [ ] T003 [P] Configure pytest in pytest.ini or pyproject.toml
- [ ] T004 [P] Add dependencies: filelock, hypothesis to requirements.txt or pyproject.toml
- [ ] T005 [P] Configure linting (ruff/pylint) and formatting (black) in pyproject.toml
- [ ] T006 [P] Create .gitignore with .vector-memory/*.lock and __pycache__ entries
- [ ] T007 Create src/vector_memory/__init__.py with package exports
- [ ] T008 Create .vector-memory/ directory in repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Create custom exception classes in src/vector_memory/exceptions.py
- [ ] T010 Implement VectorCoordinate dataclass in src/vector_memory/coordinate.py
- [ ] T011 Add coordinate validation in VectorCoordinate.__post_init__()
- [ ] T012 Implement VectorCoordinate.to_tuple() in src/vector_memory/coordinate.py
- [ ] T013 Implement VectorCoordinate.to_path() in src/vector_memory/coordinate.py
- [ ] T014 Implement VectorCoordinate.from_path() in src/vector_memory/coordinate.py
- [ ] T015 Create StoredDecision dataclass in src/vector_memory/storage.py
- [ ] T016 Implement StoredDecision.to_json() in src/vector_memory/storage.py
- [ ] T017 Implement StoredDecision.from_json() in src/vector_memory/storage.py
- [ ] T018 Create MemoryLayer class with immutability rules in src/vector_memory/storage.py
- [ ] T019 Create MemoryIndex class in src/vector_memory/validation.py
- [ ] T020 Implement MemoryIndex.add() in src/vector_memory/validation.py
- [ ] T021 Implement MemoryIndex.query_exact() in src/vector_memory/validation.py
- [ ] T022 Create VectorMemoryManager class skeleton in src/vector_memory/manager.py
- [ ] T023 Implement VectorMemoryManager.__init__() with repo_path and agent_id validation

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Store Decision at Coordinate (Priority: P1) 🎯 MVP

**Goal**: Enable AI agents to store decisions at 3D coordinates with proper validation

**Independent Test**: Store a decision at coordinates (5, 2, 1) and successfully retrieve it using those same coordinates

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T024 [P] [US1] Unit test for VectorCoordinate validation in tests/unit/test_coordinate.py
- [ ] T025 [P] [US1] Unit test for StoredDecision serialization in tests/unit/test_storage.py
- [ ] T026 [P] [US1] Property-based test for coordinate roundtrip in tests/property/test_coordinate_properties.py
- [ ] T027 [P] [US1] Integration test for store and retrieve in tests/integration/test_end_to_end.py

### Implementation for User Story 1

- [ ] T028 [US1] Implement VectorMemoryManager.store() basic logic in src/vector_memory/manager.py
- [ ] T029 [US1] Add coordinate validation in store() method
- [ ] T030 [US1] Add content validation (non-empty, max 100KB) in store() method
- [ ] T031 [US1] Implement file write with atomic rename pattern in store() method
- [ ] T032 [US1] Add index update in store() method
- [ ] T033 [US1] Implement VectorMemoryManager.get() in src/vector_memory/manager.py
- [ ] T034 [US1] Implement VectorMemoryManager.exists() in src/vector_memory/manager.py
- [ ] T035 [US1] Add error handling for CoordinateValidationError in manager.py
- [ ] T036 [US1] Add error handling for StorageError in manager.py

**Checkpoint**: At this point, User Story 1 should be fully functional - can store and retrieve decisions

---

## Phase 4: User Story 2 - Retrieve Context for Agent (Priority: P1) 🎯 MVP

**Goal**: Enable AI agents to query specific subsets of decisions efficiently

**Independent Test**: Store multiple decisions across different coordinates and query for specific subsets (e.g., all z=1 architecture layer decisions for issues 1-7)

### Tests for User Story 2

- [ ] T037 [P] [US2] Unit test for query_range with various ranges in tests/unit/test_query.py
- [ ] T038 [P] [US2] Unit test for search_content with multiple terms in tests/unit/test_query.py
- [ ] T039 [P] [US2] Integration test for complex query scenarios in tests/integration/test_end_to_end.py

### Implementation for User Story 2

- [ ] T040 [US2] Create query.py module in src/vector_memory/query.py
- [ ] T041 [P] [US2] Implement MemoryIndex.query_range() in src/vector_memory/validation.py
- [ ] T042 [P] [US2] Build content index in MemoryIndex.add() for search functionality
- [ ] T043 [US2] Implement VectorMemoryManager.query_range() in src/vector_memory/manager.py
- [ ] T044 [US2] Add range validation (min <= max) in query_range()
- [ ] T045 [US2] Implement VectorMemoryManager.search_content() in src/vector_memory/manager.py
- [ ] T046 [US2] Add match_all logic in search_content() method
- [ ] T047 [US2] Implement result sorting by relevance in search_content()
- [ ] T048 [US2] Add error handling for QueryError in manager.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - can store, retrieve, and query decisions

---

## Phase 5: User Story 3 - Enforce Architecture Layer Immutability (Priority: P1) 🎯 MVP

**Goal**: Prevent any modifications to architecture layer (z=1) decisions to maintain consistency

**Independent Test**: Store an architecture decision at z=1 and attempt to modify or delete it - both operations should fail

### Tests for User Story 3

- [ ] T049 [P] [US3] Unit test for immutability enforcement in tests/unit/test_manager.py
- [ ] T050 [P] [US3] Unit test for ImmutableLayerError scenarios in tests/unit/test_manager.py
- [ ] T051 [P] [US3] Integration test for immutability across operations in tests/integration/test_end_to_end.py

### Implementation for User Story 3

- [ ] T052 [US3] Implement MemoryLayer.validate_write() in src/vector_memory/storage.py
- [ ] T053 [US3] Add immutability check in VectorMemoryManager.store() before write
- [ ] T054 [US3] Add exists() check for z=1 coordinates in store() method
- [ ] T055 [US3] Raise ImmutableLayerError when attempting to modify z=1
- [ ] T056 [US3] Add clear error messages for immutability violations

**Checkpoint**: All three core capabilities working - store, query, and immutability enforcement

---

## Phase 6: User Story 4 - Synchronize with Git (Priority: P2)

**Goal**: Persist all vector memory data to Git for durability and team collaboration

**Independent Test**: Store decisions, terminate the process, restart, and verify all decisions are still retrievable with correct coordinates

### Tests for User Story 4

- [ ] T057 [P] [US4] Unit test for Git commit message format in tests/unit/test_persistence.py
- [ ] T058 [P] [US4] Integration test for sync and load cycle in tests/integration/test_git_sync.py
- [ ] T059 [P] [US4] Integration test for recovery after crash in tests/integration/test_git_sync.py

### Implementation for User Story 4

- [ ] T060 [US4] Create persistence.py module in src/vector_memory/persistence.py
- [ ] T061 [P] [US4] Implement git add wrapper in persistence.py
- [ ] T062 [P] [US4] Implement git commit wrapper with message formatting in persistence.py
- [ ] T063 [US4] Implement VectorMemoryManager.sync() in src/vector_memory/manager.py
- [ ] T064 [US4] Add dirty flag tracking for pending changes in manager.py
- [ ] T065 [US4] Batch all .vector-memory/ changes into single commit in sync()
- [ ] T066 [US4] Implement VectorMemoryManager.load_from_git() in src/vector_memory/manager.py
- [ ] T067 [US4] Implement MemoryIndex.rebuild() for loading from file system
- [ ] T068 [US4] Add file system scanning in load_from_git()
- [ ] T069 [US4] Add JSON file parsing and validation in load_from_git()
- [ ] T070 [US4] Add error handling for Git operations in persistence.py
- [ ] T071 [US4] Update __init__() to call load_from_git() on initialization

**Checkpoint**: Vector memory now persists across sessions and can be shared via Git

---

## Phase 7: User Story 5 - Query by Partial Ordering (Priority: P2)

**Goal**: Enable rollback functionality by finding all decisions that occurred "before" a specific point using partial ordering

**Independent Test**: Store decisions at various (x, y) coordinates and query for all decisions where (x, y) < (5, 3) using partial ordering rules

### Tests for User Story 5

- [X] T072 [P] [US5] Unit test for PartialOrder.less_than() in tests/unit/test_query.py
- [X] T073 [P] [US5] Unit test for PartialOrder.comparable() in tests/unit/test_query.py
- [X] T074 [P] [US5] Property-based test for partial order properties in tests/property/test_partial_order_properties.py
- [X] T075 [P] [US5] Integration test for rollback scenario in tests/integration/test_end_to_end.py

### Implementation for User Story 5

- [X] T076 [US5] Create PartialOrder utility class in src/vector_memory/query.py
- [X] T077 [P] [US5] Implement PartialOrder.less_than() using lexicographic comparison
- [X] T078 [P] [US5] Implement PartialOrder.comparable() in src/vector_memory/query.py
- [X] T079 [US5] Implement PartialOrder.find_before() in src/vector_memory/query.py
- [X] T080 [US5] Implement MemoryIndex.query_partial_order() in src/vector_memory/validation.py
- [X] T081 [US5] Implement VectorMemoryManager.query_partial_order() in src/vector_memory/manager.py
- [X] T082 [US5] Add optional z_filter parameter to query_partial_order()
- [X] T083 [US5] Add coordinate validation for thresholds in query_partial_order()
- [X] T084 [US5] Sort results lexicographically in query_partial_order()

**Checkpoint**: All user stories complete - full vector memory functionality available

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T085 [P] Add comprehensive docstrings to all public API methods in src/vector_memory/manager.py
- [X] T086 [P] Add type hints to all functions and methods across all modules
- [X] T087 [P] Create __all__ exports in src/vector_memory/__init__.py
- [X] T088 [P] Add unit tests for edge cases in tests/unit/test_coordinate.py
- [X] T089 [P] Add unit tests for concurrency scenarios in tests/unit/test_validation.py
- [X] T090 [P] Add integration test for concurrent access in tests/integration/test_concurrent_access.py
- [X] T091 [P] Implement file locking for write operations using filelock library
- [X] T092 [P] Add atomic write pattern (temp file + rename) in store() method
- [X] T093 [P] Add logging throughout manager.py for observability
- [X] T094 [P] Performance optimization: lazy load decisions (load metadata only in index)
- [X] T095 [P] Add performance benchmarks in tests/performance/ directory
- [X] T096 [P] Validate against quickstart.md examples
- [X] T097 Code cleanup: Remove debug prints, unused imports
- [X] T098 [P] Run pylint/ruff and fix all issues
- [X] T099 [P] Run black formatter on all Python files
- [X] T100 Verify all success criteria from spec.md are met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (Store) is foundational for all other stories
  - US2 (Query) depends on US1 (need data to query)
  - US3 (Immutability) depends on US1 (enforces store behavior)
  - US4 (Git) depends on US1 (needs store to sync)
  - US5 (Partial Order) depends on US1 and US2 (query variant)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (Store)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (Query)**: Depends on US1 for basic storage functionality
- **User Story 3 (Immutability)**: Depends on US1 for store() method to modify
- **User Story 4 (Git Sync)**: Depends on US1 for persistence of stored decisions
- **User Story 5 (Partial Order)**: Depends on US1 and US2 for query infrastructure

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Core functionality before edge cases
- Error handling after happy path
- Validation before business logic

### Parallel Opportunities

**Within Setup (Phase 1)**:
- T003, T004, T005, T006 can all run in parallel

**Within Foundational (Phase 2)**:
- After T009 (exceptions), all dataclass implementations can proceed in parallel
- T010-T014 (VectorCoordinate) can run while T015-T018 (StoredDecision, MemoryLayer) run

**Within User Story 1**:
- T024, T025, T026, T027 (all tests) can run in parallel
- After tests pass, implementation tasks must be sequential

**Within User Story 2**:
- T037, T038, T039 (all tests) can run in parallel
- T041, T042 (index methods) can run in parallel

**Within User Story 3**:
- T049, T050, T051 (all tests) can run in parallel

**Within User Story 4**:
- T057, T058, T059 (all tests) can run in parallel
- T061, T062 (Git wrappers) can run in parallel

**Within User Story 5**:
- T072, T073, T074, T075 (all tests) can run in parallel
- T077, T078 (PartialOrder methods) can run in parallel

**Within Polish (Phase 8)**:
- Most polish tasks (T085-T100) can run in parallel as they touch different files

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
# Task T024: Unit test for VectorCoordinate validation in tests/unit/test_coordinate.py
# Task T025: Unit test for StoredDecision serialization in tests/unit/test_storage.py
# Task T026: Property-based test for coordinate roundtrip in tests/property/test_coordinate_properties.py
# Task T027: Integration test for store and retrieve in tests/integration/test_end_to_end.py

# After tests fail, implement serially:
# T028 → T029 → T030 → T031 → T032 → T033 → T034 → T035 → T036
```

---

## Implementation Strategy

### MVP First (User Stories 1, 2, 3 Only)

**Target**: Core coordinate-based storage with queries and immutability

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Store & Retrieve)
4. Complete Phase 4: User Story 2 (Query)
5. Complete Phase 5: User Story 3 (Immutability)
6. **STOP and VALIDATE**: Test core functionality independently
7. Deploy/use for other ACO components

**MVP Scope**: 23 tasks (T001-T023) + 13 tasks (T024-T036) + 12 tasks (T037-T048) + 8 tasks (T049-T056) = **56 tasks**

### Incremental Delivery

1. **Foundation** (Phases 1-2): T001-T023 → File system storage works
2. **MVP Core** (Phases 3-5): T024-T056 → Store, query, immutability works → **Can integrate with DAG Orchestrator**
3. **Persistence** (Phase 6): T057-T071 → Git sync works → **Can survive restarts**
4. **Advanced Query** (Phase 7): T072-T084 → Rollback support works → **Can support error recovery**
5. **Production Ready** (Phase 8): T085-T100 → Performance, polish → **Ready for production use**

### Sequential Strategy (Single Developer)

1. Complete all tests for a user story first (Red phase)
2. Implement to make tests pass (Green phase)
3. Refactor and polish (Refactor phase)
4. Move to next priority user story
5. Order: US1 → US2 → US3 → US4 → US5 → Polish

### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup + Foundational together** (T001-T023)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (T024-T036) - Blocks everyone else
   - After US1 complete:
     - **Developer A**: User Story 3 (T049-T056) - Immutability
     - **Developer B**: User Story 2 (T037-T048) - Queries
   - After US1-3 complete:
     - **Developer A**: User Story 4 (T057-T071) - Git Sync
     - **Developer B**: User Story 5 (T072-T084) - Partial Order
3. **All developers**: Polish tasks in parallel (T085-T100)

---

## Notes

- **[P] tasks** = different files, no dependencies between them
- **[Story] label** = maps task to specific user story for traceability
- **Test-First**: All tests written before implementation (Red-Green-Refactor)
- **Independent Stories**: Each user story should be independently testable after completion
- **Commit Strategy**: Commit after each task or logical group of related tasks
- **Validation Points**: Stop at each checkpoint to validate story works independently
- **Performance**: Targets from spec.md (< 50ms store/retrieve, < 100ms queries)
- **Coverage**: Minimum 80% test coverage required per constitution
- **Dependencies**: hypothesis (property testing), filelock (concurrency), pytest (testing)

---

## Success Criteria Validation

After completing all tasks, verify these success criteria from spec.md:

- **SC-001**: Store/retrieve operations < 50ms (99th percentile) ✓ via T095 benchmarks
- **SC-002**: 100% accuracy in coordinate-based retrieval ✓ via integration tests
- **SC-003**: 100% immutability of z=1 layer ✓ via T049-T051 tests
- **SC-004**: Handles 10,000 stored decisions ✓ via T095 performance tests
- **SC-005**: Git sync < 5s for 1000 decisions ✓ via T058 integration test
- **SC-006**: Recovery < 10s ✓ via T059 integration test
- **SC-007**: Partial ordering queries < 100ms ✓ via T074 property test
- **SC-008**: Content search < 200ms ✓ via T038 unit test
- **SC-009**: Zero data loss during concurrency ✓ via T090 concurrency test
- **SC-010**: < 5 lookups for 95% of queries ✓ via efficient index design

---

**Total Tasks**: 100
**MVP Tasks**: 56 (Phases 1-5)
**Full Feature Tasks**: 84 (Phases 1-7)
**Polish Tasks**: 16 (Phase 8)

**Estimated Time**:
- MVP (T001-T056): 3-5 days for experienced Python developer
- Full Feature (T001-T084): 5-8 days
- Production Ready (T001-T100): 6-10 days

**Ready for**: `/speckit.implement` command to begin TDD implementation
