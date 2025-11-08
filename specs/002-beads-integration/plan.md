# Implementation Plan: Beads Integration Layer

**Branch**: `002-beads-integration` | **Date**: 2025-11-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-beads-integration/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature implements a Python interface to the Beads issue tracker CLI (`bd` commands), enabling programmatic DAG management for autonomous orchestration. The interface provides CRUD operations for issues, dependency graph queries, status synchronization, and JSON parsing of all `bd` command outputs. This is a foundational component that enables DAG-driven development by wrapping the Beads CLI with a clean Python API.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: subprocess (stdlib), json (stdlib), dataclasses (stdlib), typing (stdlib)  
**Storage**: Beads native storage (`.beads/` directory with Git sync)  
**Testing**: pytest with fixtures for test `.beads/` databases  
**Target Platform**: Linux/macOS (WSL2 compatible)  
**Project Type**: Single library project  
**Performance Goals**: < 100ms overhead per CLI call, < 500ms for 100-issue DAG queries  
**Constraints**: Must not interfere with Beads' Git sync (5s debounce), thread-safe for future parallelism  
**Scale/Scope**: Handle DAGs up to 1000 issues without performance degradation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md` principles:

- [x] **Vector Memory Architecture**: Design supports coordinate-based storage (x=DAG, y=cycle, z=layer)
  - ✅ Issue IDs map directly to x-coordinate in vector memory system
  - ✅ Interface enables querying by issue ID (x-coordinate)
  - ✅ No violation of memory architecture principles
  
- [x] **DAG-Driven Development**: All work tracked in Beads with explicit dependencies
  - ✅ This IS the Beads integration - enables DAG-driven development for entire system
  - ✅ Provides dependency management functions (add, remove, query)
  - ✅ Respects Beads' native DAG structure without modification
  
- [x] **Unified Development Cycle**: Plan follows Architect → Test → Implement → Review → Merge
  - ✅ Plan will follow standard cycle (Phase 0: Research, Phase 1: Design/Contracts, Phase 2: Tasks)
  - ✅ Tests will be written before implementation (TDD approach)
  - ✅ No stage skipping
  
- [x] **Test-First Development**: Tests planned before implementation (80% coverage minimum)
  - ✅ pytest-based test suite planned with fixtures for test databases
  - ✅ Unit tests for all CLI wrapper functions
  - ✅ Integration tests against real `.beads/` database
  - ✅ Target: >80% coverage with meaningful assertions
  
- [x] **Autonomous Operation**: Escalation points identified (SMS/Email/Docs classification)
  - ✅ Error handling strategy: graceful exceptions with context
  - ✅ No human intervention required for normal operations
  - ✅ Malformed JSON or CLI errors → Python exceptions (agent handles)
  - ⚠️ Git sync conflicts → Log warning, let Beads handle (Docs-level issue)
  
- [x] **Scope Control**: Feature scope justified against gravity function, complexity budget
  - ✅ Foundation layer feature (P0 priority) - no gravity penalty
  - ✅ Minimal complexity: thin wrapper over existing CLI
  - ✅ No feature creep: strictly CRUD + dependency operations
  - ✅ Deliberately excludes: web UI, caching layer, query optimization
  
- [x] **Observability**: Audit trail, cost tracking, performance metrics planned
  - ✅ All operations logged via Python logging module
  - ✅ Performance metrics: CLI call duration tracking
  - ✅ Audit trail: Git history of `.beads/issues.jsonl` (Beads native)
  - ✅ Cost tracking: N/A (local operations, no API calls)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── beads/
│   ├── __init__.py          # Public API exports
│   ├── client.py            # BeadsClient main interface
│   ├── models.py            # Issue, Dependency, Status, Type, Priority dataclasses
│   ├── exceptions.py        # Custom exception types
│   └── utils.py             # JSON parsing helpers, CLI execution utilities

tests/
├── conftest.py              # pytest fixtures (test .beads/ database setup)
├── unit/
│   ├── test_client.py       # BeadsClient unit tests (mocked subprocess)
│   ├── test_models.py       # Dataclass validation tests
│   └── test_utils.py        # Utility function tests
└── integration/
    ├── test_issue_crud.py   # Create, read, update, delete operations
    ├── test_dependencies.py # Dependency management operations
    └── test_queries.py      # Ready issues, filtering, tree queries
```

**Structure Decision**: Single library project structure chosen because:
- Feature is a standalone Python library/module
- No frontend, backend, or multi-project separation needed
- Beads integration is self-contained within `src/beads/` package
- Clear separation between library code (`src/`) and tests (`tests/`)
- pytest fixtures enable integration testing against real `.beads/` databases

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations | All constitutional principles satisfied |

---

## Post-Design Constitution Review

**Phase 1 Complete**: Research, data model, contracts, and quickstart guide have been generated.

**Re-evaluation of Constitutional Compliance**:

✅ **All principles remain satisfied after design phase:**

1. **Vector Memory Architecture**: 
   - Design maintains clean mapping: Issue.id → x-coordinate
   - No changes to memory architecture principles
   - Interface respects vector-based retrieval patterns

2. **DAG-Driven Development**:
   - API fully supports DAG operations (ready, dependencies, cycles)
   - Design preserves Beads' DAG integrity (no bypassing)
   - Dependency validation prevents graph corruption

3. **Unified Development Cycle**:
   - Planning followed correct sequence: Research → Design → (Tasks next)
   - Phase 0 research resolved all unknowns
   - Phase 1 contracts define clear interfaces for TDD

4. **Test-First Development**:
   - Contract specifications enable test writing before implementation
   - Test structure defined in project layout
   - Fixtures planned for isolated test databases

5. **Autonomous Operation**:
   - Error handling strategy complete (custom exception hierarchy)
   - No human intervention points added
   - All edge cases have programmatic responses

6. **Scope Control**:
   - Design stayed within MVP scope
   - No feature creep introduced during planning
   - Complexity remains minimal (thin CLI wrapper)

7. **Observability**:
   - Logging strategy included in research decisions
   - Performance tracking approach documented
   - Audit trail preserved via Beads' native Git sync

**Conclusion**: ✅ **Ready to proceed to Phase 2 (Task Generation)**

No constitutional violations, no scope creep, all design artifacts complete.