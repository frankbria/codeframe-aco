# Implementation Tasks: Beads Integration Layer

**Feature**: 002-beads-integration
**Branch**: `002-beads-integration`
**Created**: 2025-11-07
**Status**: Ready for Implementation

---

## Overview

This document contains dependency-ordered, executable tasks for implementing the Beads Integration Layer. Each task follows TDD principles (Tests → Implementation) and is organized by user story for independent implementation and testing.

**Total Tasks**: 45
**Phases**: 7 (Setup + Foundational + 5 User Stories)
**Test-First**: Yes (80% coverage minimum per constitution)

---

## Task Format Legend

```
- [ ] [TaskID] [P] [Story] Description with file path

TaskID: Sequential number (T001, T002, ...)
[P]: Parallelizable (can run concurrently with other [P] tasks)
[Story]: User story label ([US1], [US2], etc.)
```

---

## Phase 1: Project Setup

**Goal**: Initialize project structure and dependencies

- [X] T001 Create src/beads/ directory structure per plan.md
- [X] T002 Create tests/ directory structure (unit/, integration/) per plan.md
- [X] T003 Create src/beads/__init__.py with package exports
- [X] T004 Create pyproject.toml or setup.py with Python 3.11+ requirement
- [X] T005 Create pytest.ini with test configuration and coverage settings (80% minimum)
- [X] T006 Create .gitignore with Python-specific patterns (__pycache__, *.pyc, .pytest_cache, .coverage)
- [X] T007 Create README.md with project overview and installation instructions
- [X] T008 Verify bd CLI is installed and accessible via `which bd` command

---

## Phase 2: Foundational Layer (Blocking Prerequisites)

**Goal**: Core infrastructure that all user stories depend on

### Enumerations (Required by all stories)

- [X] T009 [P] Write tests for IssueStatus enum in tests/unit/test_models.py
- [X] T010 [P] Write tests for IssueType enum in tests/unit/test_models.py
- [X] T011 [P] Write tests for DependencyType enum in tests/unit/test_models.py
- [X] T012 Implement IssueStatus enum in src/beads/models.py
- [X] T013 Implement IssueType enum in src/beads/models.py
- [X] T014 Implement DependencyType enum in src/beads/models.py
- [X] T015 Run tests for enums and verify 100% pass rate

### Exception Hierarchy (Required by all stories)

- [X] T016 [P] Write tests for BeadsError exception in tests/unit/test_exceptions.py
- [X] T017 [P] Write tests for BeadsCommandError exception in tests/unit/test_exceptions.py
- [X] T018 [P] Write tests for BeadsJSONParseError exception in tests/unit/test_exceptions.py
- [X] T019 [P] Write tests for BeadsIssueNotFoundError exception in tests/unit/test_exceptions.py
- [X] T020 [P] Write tests for BeadsDependencyCycleError exception in tests/unit/test_exceptions.py
- [X] T021 Implement exception hierarchy in src/beads/exceptions.py
- [X] T022 Run tests for exceptions and verify 100% pass rate

### Core Utilities (Required by all stories)

- [X] T023 Write tests for _run_bd_command helper in tests/unit/test_utils.py (subprocess mocking)
- [X] T024 Write tests for JSON parsing utilities in tests/unit/test_utils.py
- [X] T025 Implement _run_bd_command with subprocess execution in src/beads/utils.py
- [X] T026 Implement JSON parsing utilities with error handling in src/beads/utils.py
- [X] T027 Add logging and performance tracking to _run_bd_command in src/beads/utils.py
- [X] T028 Run tests for utilities and verify 100% pass rate

### Test Fixtures (Required for integration tests)

- [X] T029 Create pytest fixture for isolated .beads/ database in tests/conftest.py
- [X] T030 Create pytest fixture for BeadsClient with sandbox mode in tests/conftest.py
- [X] T031 Create pytest fixture for test issues with various states in tests/conftest.py
- [X] T032 Verify fixtures work by running simple integration test in tests/integration/test_fixtures.py

---

## Phase 3: User Story 1 - Query Ready Issues (P1) ⭐ MVP

**Goal**: Enable autonomous agents to query unblocked work for selection

**Independent Test**: Create test issues with dependencies, query via Python, verify only unblocked issues returned

**Depends On**: Phase 2 (Foundational Layer)

### Data Models

- [ ] T033 [US1] Write tests for Issue dataclass validation in tests/unit/test_models.py
- [ ] T034 [US1] Write tests for Issue.from_json() parsing in tests/unit/test_models.py
- [ ] T035 [US1] Implement Issue dataclass with validation in src/beads/models.py
- [ ] T036 [US1] Implement Issue.from_json() with datetime parsing in src/beads/models.py
- [ ] T037 [US1] Run tests for Issue model and verify 100% pass rate

### Client Methods (Tests First)

- [ ] T038 [US1] Write unit tests for BeadsClient.get_ready_issues() in tests/unit/test_client.py (mocked subprocess)
- [ ] T039 [US1] Write integration tests for get_ready_issues() in tests/integration/test_queries.py (real bd CLI)
- [ ] T040 [US1] Test scenario: 3 issues where issue A has no deps, B blocks C → returns A and B
- [ ] T041 [US1] Test scenario: All issues blocked → returns empty list
- [ ] T042 [US1] Test scenario: Issue transitions from blocked to ready → appears in results

### Implementation

- [ ] T043 [US1] Implement BeadsClient.get_ready_issues() in src/beads/client.py
- [ ] T044 [US1] Handle limit, priority, issue_type filters in get_ready_issues()
- [ ] T045 [US1] Add error handling for malformed JSON and CLI errors
- [ ] T046 [US1] Run all US1 tests and verify 100% pass rate

### Integration & Validation

- [ ] T047 [US1] Run integration tests against real .beads/ database
- [ ] T048 [US1] Verify performance: Query 100-issue DAG completes in < 500ms (SC-007)
- [ ] T049 [US1] Update src/beads/__init__.py to export Issue, IssueStatus, IssueType, BeadsClient
- [ ] T050 [US1] Create example script demonstrating work selection in examples/select_task.py

**US1 Complete**: ✅ Agents can query ready issues and select next work item

---

## Phase 4: User Story 2 - Update Issue Status (P2)

**Goal**: Enable cycle processors to track work progress through status updates

**Independent Test**: Create issue, update status via Python, verify persistence in Beads

**Depends On**: US1 (Issue model and BeadsClient foundation)

### Client Methods (Tests First)

- [ ] T051 [P] [US2] Write unit tests for update_issue_status() in tests/unit/test_client.py
- [ ] T052 [P] [US2] Write unit tests for update_issue_priority() in tests/unit/test_client.py
- [ ] T053 [P] [US2] Write unit tests for close_issue() in tests/unit/test_client.py
- [ ] T054 [US2] Write integration tests for status updates in tests/integration/test_issue_crud.py
- [ ] T055 [US2] Test scenario: Open → in_progress → appears in bd list --status in_progress
- [ ] T056 [US2] Test scenario: In_progress → closed → no longer in bd ready
- [ ] T057 [US2] Test scenario: Multiple updates in sequence → current status reflects latest

### Implementation

- [ ] T058 [US2] Implement update_issue_status() in src/beads/client.py
- [ ] T059 [US2] Implement update_issue_priority() in src/beads/client.py
- [ ] T060 [US2] Implement close_issue() in src/beads/client.py
- [ ] T061 [US2] Add validation for priority range (0-4) with ValueError
- [ ] T062 [US2] Handle BeadsIssueNotFoundError for non-existent issues
- [ ] T063 [US2] Run all US2 tests and verify 100% pass rate

### Integration & Validation

- [ ] T064 [US2] Run integration tests for status lifecycle (open → in_progress → closed)
- [ ] T065 [US2] Verify operations complete in < 100ms per call (SC-001)
- [ ] T066 [US2] Create example script demonstrating status updates in examples/track_progress.py

**US2 Complete**: ✅ Agents can track work progress through development cycle

---

## Phase 5: User Story 3 - Retrieve Issue Details (P3)

**Goal**: Enable orchestrators to retrieve full issue context for planning

**Independent Test**: Create issues with metadata, query via Python, verify all fields returned

**Depends On**: US1 (Issue model and BeadsClient foundation)

### Client Methods (Tests First)

- [ ] T067 [P] [US3] Write unit tests for get_issue() in tests/unit/test_client.py
- [ ] T068 [P] [US3] Write unit tests for list_issues() in tests/unit/test_client.py
- [ ] T069 [US3] Write integration tests for get_issue() in tests/integration/test_queries.py
- [ ] T070 [US3] Write integration tests for list_issues() filters in tests/integration/test_queries.py
- [ ] T071 [US3] Test scenario: Issue with priority P0, type "feature" → all fields correct
- [ ] T072 [US3] Test scenario: Issue with dependencies → dependency list includes blockers
- [ ] T073 [US3] Test scenario: Issue with metadata → dates and author correctly parsed

### Implementation

- [ ] T074 [US3] Implement get_issue() with BeadsIssueNotFoundError handling in src/beads/client.py
- [ ] T075 [US3] Implement list_issues() with status/priority/type filters in src/beads/client.py
- [ ] T076 [US3] Add limit parameter support to list_issues()
- [ ] T077 [US3] Run all US3 tests and verify 100% pass rate

### Integration & Validation

- [ ] T078 [US3] Run integration tests with various filter combinations
- [ ] T079 [US3] Verify CLI overhead < 100ms per call (SC-001)
- [ ] T080 [US3] Create example script demonstrating context-aware planning in examples/plan_work.py

**US3 Complete**: ✅ Orchestrators can retrieve full issue context for smart planning

---

## Phase 6: User Story 4 - Create New Issues (P4)

**Goal**: Enable cycle processors to create issues during gap discovery

**Independent Test**: Create issue via Python, verify appears in bd list with correct attributes

**Depends On**: US1 (Issue model and BeadsClient foundation)

### Client Methods (Tests First)

- [ ] T081 [US4] Write unit tests for create_issue() in tests/unit/test_client.py
- [ ] T082 [US4] Write integration tests for create_issue() in tests/integration/test_issue_crud.py
- [ ] T083 [US4] Test scenario: Create issue with title, type, priority → appears in Beads
- [ ] T084 [US4] Test scenario: Create with empty title → raises ValueError
- [ ] T085 [US4] Test scenario: Create with invalid priority → raises ValueError
- [ ] T086 [US4] Test scenario: Create with description and assignee → fields persisted

### Implementation

- [ ] T087 [US4] Implement create_issue() with title/type/priority validation in src/beads/client.py
- [ ] T088 [US4] Add support for optional description and assignee parameters
- [ ] T089 [US4] Parse and return newly created issue ID from bd output
- [ ] T090 [US4] Add validation: title non-empty, priority 0-4
- [ ] T091 [US4] Run all US4 tests and verify 100% pass rate

### Integration & Validation

- [ ] T092 [US4] Run integration tests verifying issue creation persists
- [ ] T093 [US4] Verify created issues appear in subsequent queries
- [ ] T094 [US4] Create example script demonstrating gap discovery workflow in examples/discover_gaps.py

**US4 Complete**: ✅ Agents can autonomously expand DAG by creating new issues

---

## Phase 7: User Story 5 - Manage Dependencies (P5)

**Goal**: Enable orchestrators to manipulate DAG structure dynamically

**Independent Test**: Create issues, add/remove dependencies via Python, verify graph changes

**Depends On**: US1 (Issue model), US4 (create_issue for test setup)

### Data Models

- [ ] T095 [P] [US5] Write tests for Dependency dataclass in tests/unit/test_models.py
- [ ] T096 [P] [US5] Write tests for DependencyTree dataclass in tests/unit/test_models.py
- [ ] T097 [US5] Implement Dependency dataclass with self-dependency validation in src/beads/models.py
- [ ] T098 [US5] Implement DependencyTree dataclass in src/beads/models.py
- [ ] T099 [US5] Run tests for dependency models and verify 100% pass rate

### Client Methods (Tests First)

- [ ] T100 [P] [US5] Write unit tests for add_dependency() in tests/unit/test_client.py
- [ ] T101 [P] [US5] Write unit tests for remove_dependency() in tests/unit/test_client.py
- [ ] T102 [P] [US5] Write unit tests for get_dependency_tree() in tests/unit/test_client.py
- [ ] T103 [P] [US5] Write unit tests for detect_dependency_cycles() in tests/unit/test_client.py
- [ ] T104 [US5] Write integration tests for dependencies in tests/integration/test_dependencies.py
- [ ] T105 [US5] Test scenario: Add "blocks" dependency → blocked issue not in bd ready
- [ ] T106 [US5] Test scenario: Remove dependency → previously blocked issue becomes ready
- [ ] T107 [US5] Test scenario: Query dependency tree → structure reflects relationships
- [ ] T108 [US5] Test scenario: Add cycle-creating dependency → raises BeadsDependencyCycleError

### Implementation

- [ ] T109 [US5] Implement add_dependency() with all 4 dependency types in src/beads/client.py
- [ ] T110 [US5] Add validation: blocked_id ≠ blocker_id (no self-dependencies)
- [ ] T111 [US5] Implement remove_dependency() as idempotent operation in src/beads/client.py
- [ ] T112 [US5] Implement get_dependency_tree() with JSON parsing in src/beads/client.py
- [ ] T113 [US5] Implement detect_dependency_cycles() returning List[List[str]] in src/beads/client.py
- [ ] T114 [US5] Handle cycle detection: parse bd dep cycles JSON output
- [ ] T115 [US5] Run all US5 tests and verify 100% pass rate

### Integration & Validation

- [ ] T116 [US5] Run integration tests with complex dependency scenarios
- [ ] T117 [US5] Verify all 4 dependency types work correctly (SC-005)
- [ ] T118 [US5] Verify cycle detection identifies all cycles (SC-006)
- [ ] T119 [US5] Update src/beads/__init__.py to export Dependency, DependencyType, DependencyTree
- [ ] T120 [US5] Create example script demonstrating DAG manipulation in examples/manage_dag.py

**US5 Complete**: ✅ Orchestrators can dynamically manage DAG structure

---

## Phase 8: Polish & Cross-Cutting Concerns

**Goal**: Final integration, documentation, and production readiness

### Factory Function

- [ ] T121 Write tests for create_beads_client() factory in tests/unit/test_client.py
- [ ] T122 Implement create_beads_client() with db_path, timeout, sandbox params in src/beads/client.py
- [ ] T123 Add auto-discovery of .beads/ directory when db_path is None
- [ ] T124 Run tests for factory function and verify sandbox mode works

### Final Integration

- [ ] T125 Verify all exports in src/beads/__init__.py are correct and documented
- [ ] T126 Run full test suite and verify 80%+ coverage (constitution requirement)
- [ ] T127 Run performance benchmark: 100-issue DAG query < 500ms (SC-007)
- [ ] T128 Run concurrency test: Verify no data corruption with simulated race conditions (SC-008)
- [ ] T129 Test against real .beads/ database with 100+ issues (scale test)
- [ ] T130 Verify CLI overhead < 100ms per call for all operations (SC-001)

### Documentation

- [ ] T131 [P] Update README.md with usage examples from quickstart.md
- [ ] T132 [P] Add API documentation docstrings to all public methods
- [ ] T133 [P] Create CONTRIBUTING.md with development setup instructions
- [ ] T134 [P] Verify all example scripts in examples/ directory work correctly

### Production Readiness

- [ ] T135 Add type hints verification (mypy or similar)
- [ ] T136 Add code formatting check (black or ruff)
- [ ] T137 Create GitHub Actions workflow for CI (tests + coverage)
- [ ] T138 Tag release v0.1.0 for Beads Integration Layer MVP

---

## Dependencies & Execution Strategy

### User Story Dependency Graph

```
Phase 1: Setup
    ↓
Phase 2: Foundational (Enums, Exceptions, Utils, Fixtures)
    ↓
    ├─→ Phase 3: US1 (Query Ready) ⭐ MVP - INDEPENDENT
    ├─→ Phase 4: US2 (Update Status) - depends on US1
    ├─→ Phase 5: US3 (Get Details) - depends on US1
    ├─→ Phase 6: US4 (Create Issues) - depends on US1
    └─→ Phase 7: US5 (Dependencies) - depends on US1, US4

All phases converge to:
    ↓
Phase 8: Polish & Integration
```

### Critical Path (Minimum MVP)

For the absolute minimum viable product:

1. Phase 1: Setup (T001-T008)
2. Phase 2: Foundational (T009-T032)
3. Phase 3: US1 Only (T033-T050)

**Result**: Agents can query ready issues and select work (core orchestration capability)

### Parallel Execution Opportunities

**Within Phase 2 (Foundational)**:
- T009-T011 (Enum tests) can run in parallel
- T016-T020 (Exception tests) can run in parallel

**Within Phase 3 (US1)**:
- T038-T042 (Tests) can be written in parallel by different developers

**Within Phase 4 (US2)**:
- T051-T053 (Client method tests) can run in parallel

**Within Phase 5 (US3)**:
- T067-T068 (Client method tests) can run in parallel

**Within Phase 7 (US5)**:
- T095-T096 (Model tests) can run in parallel
- T100-T103 (Client method tests) can run in parallel

**Within Phase 8 (Polish)**:
- T131-T134 (Documentation) can run in parallel

### Independent User Story Implementation

After Phase 2 completion, these can be implemented independently (different branches/developers):

- **US1** (T033-T050): Core query functionality
- **US2** (T051-T066): Status updates (depends on US1 for Issue model only)
- **US3** (T067-T080): Detail retrieval (depends on US1 for Issue model only)
- **US4** (T081-T094): Issue creation (depends on US1 for Issue model only)
- **US5** (T095-T120): Dependency management (depends on US1 and US4 for test setup)

---

## Implementation Strategy

### Test-Driven Development (TDD)

Per constitution requirement, ALL implementation follows Red-Green-Refactor:

1. **Red**: Write failing tests for functionality
2. **Green**: Implement minimal code to pass tests
3. **Refactor**: Improve code quality while keeping tests green

### Coverage Requirements

- Minimum 80% code coverage (constitutional requirement)
- All public API methods must have unit tests
- All user scenarios must have integration tests
- Edge cases must be explicitly tested

### Quality Gates

Before marking any phase complete:

✅ All tests pass
✅ Coverage > 80%
✅ No linter errors
✅ Performance criteria met
✅ Integration tests pass with real `.beads/` database

---

## Task Execution Checklist

When implementing each task:

1. ☐ Read task description and file path carefully
2. ☐ If test task: Write test following contract specification
3. ☐ If implementation task: Implement to pass tests (Red → Green)
4. ☐ Run specific test file to verify task completion
5. ☐ Check coverage for the modified file
6. ☐ Mark task complete: `- [x]` in tasks.md
7. ☐ Commit with message: `feat(US#): <task description>`

---

## Success Criteria Mapping

| Success Criterion | Related Tasks | Verification |
|------------------|---------------|--------------|
| SC-001: < 100ms overhead per call | T130, T065, T079 | Performance benchmark |
| SC-002: Handle malformed JSON | T024, T026, T045 | Error handling tests |
| SC-003: 100% operations accessible | T043-T120 | API completeness check |
| SC-004: Integration tests pass | T047, T064, T078, T092, T116 | Integration test suite |
| SC-005: All 4 dependency types | T109, T117 | Dependency type tests |
| SC-006: Cycle detection | T113, T118 | Cycle detection tests |
| SC-007: 100-issue query < 500ms | T048, T127 | Scale performance test |
| SC-008: No data corruption | T128 | Concurrency test |

---

## Notes

- **MVP Scope**: Phase 1 + Phase 2 + Phase 3 (US1) = 50 tasks
- **Full Feature**: All 138 tasks
- **Estimated Effort**: 2-3 days for MVP, 5-7 days for full feature
- **Constitutional Compliance**: ✅ All principles satisfied (TDD, 80% coverage, DAG-driven)

**Next Step**: Begin with T001 (Project Setup) or use `/speckit.implement` to start implementation workflow.
