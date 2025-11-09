# Prompt for Next AI Agent

## Context
You are continuing work on the **Beads Integration Layer** (feature 002-beads-integration), a Python interface to the Beads issue tracker for autonomous DAG management.

## Current State
- **Branch**: `002-beads-integration`
- **Progress**: 120/138 tasks complete (87%)
- **Status**: Phases 1-7 complete ✅, Phase 8 remaining 🔲
- **Last Commit**: `2eb34a9` - "feat(002): Complete Phase 6 & 7"

## Your Task
Complete **Phase 8: Polish & Production Readiness** (18 tasks: T121-T138)

This is the final phase to make the Beads Integration Layer production-ready.

## Quick Start

### 1. Read the Handoff Documentation
```bash
cat HANDOFF.md
```
This contains all context, architecture, and recent changes.

### 2. Check Current Status
```bash
# Verify you're on the right branch
git branch

# See what's ready to work on
bd ready

# Check Phase 8 issue
bd show codeframe-aco-huo
```

### 3. Review Task Breakdown
```bash
cat specs/002-beads-integration/tasks.md | grep -A 100 "Phase 8:"
```

## Phase 8 Task Groups

### Group 1: Factory Function Tests (T121-T124) - 2 hours
The `create_beads_client()` factory already exists in `src/beads/client.py`.

**Tasks**:
- Write unit tests for the factory function
- Test db_path parameter (currently unused)
- Test timeout parameter (currently works)
- Test sandbox parameter (currently works)
- Add db_path auto-discovery logic (find .beads/ in parent directories)

**Files to modify**:
- tests/unit/test_client.py (add TestCreateBeadsClientFactory class)
- src/beads/client.py (enhance auto-discovery if needed)

### Group 2: Test Coverage & Validation (T125-T130) - 3 hours
Ensure code quality and performance.

**Tasks**:
- Run full test suite: `pytest tests/ -v --cov=src/beads --cov-report=html`
- Verify 80%+ coverage for beads package (exclude vector_memory)
- Add missing unit tests for any uncovered code paths
- Run performance benchmarks (optional - can defer)
- Run concurrency tests (optional - can defer)

**Files to check**:
- All test files in tests/unit/ and tests/integration/
- Coverage report: htmlcov/index.html

### Group 3: Documentation (T131-T134) - 2 hours
Update user-facing documentation.

**Tasks**:
- Update README.md with examples from specs/002-beads-integration/quickstart.md
- Add/verify docstrings on all public methods
- Create CONTRIBUTING.md with setup instructions
- Test all example scripts work: examples/*.py

**Files to modify**:
- README.md (add usage examples, installation, quickstart)
- CONTRIBUTING.md (create new - dev setup, testing, contributing)
- Verify docstrings in src/beads/*.py

### Group 4: Production Readiness (T135-T138) - 2 hours
Add tooling and release preparation.

**Tasks**:
- Add mypy type checking: create mypy.ini or pyproject.toml config
- Add black/ruff formatting: create config, run formatter
- Create .github/workflows/ci.yml for GitHub Actions
- Tag release v0.1.0

**Files to create/modify**:
- mypy.ini or add [tool.mypy] to pyproject.toml
- .github/workflows/ci.yml (pytest, coverage, mypy, black)
- Update pyproject.toml with project metadata
- CHANGELOG.md (create with v0.1.0 release notes)

## Commands to Use

### Testing
```bash
# Activate venv
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/beads --cov-report=term --cov-report=html

# Run specific test file
pytest tests/unit/test_client.py -v

# Run tests excluding slow integration tests
pytest tests/unit/ -v
```

### Formatting & Type Checking
```bash
# Format code with black
black src/ tests/

# Check types with mypy
mypy src/beads/

# Lint with ruff
ruff check src/ tests/
```

### Examples
```bash
# Test examples work
cd /tmp/test-beads && bd init --prefix test
python examples/select_task.py
python examples/discover_gaps.py simulate
python examples/manage_dag.py
```

### Git & Beads
```bash
# Update Phase 8 status
bd update codeframe-aco-huo --status in_progress

# When complete
bd close codeframe-aco-huo

# Commit work
git add .
git commit -m "feat(002): Complete Phase 8 - Polish & Production Readiness"

# Tag release
git tag -a v0.1.0 -m "Release v0.1.0: Beads Integration Layer MVP"
```

## Success Criteria

You're done when:
- ✅ All 138 tasks marked [X] in specs/002-beads-integration/tasks.md
- ✅ Test coverage ≥ 80% for src/beads/ package
- ✅ All tests passing (unit + integration)
- ✅ README.md has clear usage examples
- ✅ CONTRIBUTING.md exists with setup instructions
- ✅ CI/CD workflow created and passing
- ✅ v0.1.0 tagged
- ✅ Phase 8 issue (codeframe-aco-huo) closed in beads
- ✅ Main issue (codeframe-aco-xon) closed in beads

## Key Files to Know

**Implementation**:
- src/beads/client.py - Main BeadsClient class (419 lines)
- src/beads/models.py - Dataclasses (251 lines)
- src/beads/exceptions.py - Custom exceptions
- src/beads/__init__.py - Public API exports

**Tests**:
- tests/unit/test_client.py - Client unit tests
- tests/unit/test_models.py - Model tests (580 lines)
- tests/integration/test_issue_crud.py - CRUD tests
- tests/integration/test_dependencies.py - Dependency tests

**Documentation**:
- specs/002-beads-integration/tasks.md - Task breakdown
- specs/002-beads-integration/quickstart.md - Usage examples
- HANDOFF.md - Detailed context (read this!)

**Examples**:
- examples/select_task.py - Work selection
- examples/track_progress.py - Status updates
- examples/plan_work.py - Context retrieval
- examples/discover_gaps.py - Gap discovery (Phase 6)
- examples/manage_dag.py - DAG manipulation (Phase 7)

## Important Notes

1. **Coverage Reporting**: Exclude vector_memory package - it's not part of this feature
   ```bash
   pytest --cov=src/beads --cov-report=html
   ```

2. **Integration Test Timeouts**: Some integration tests timeout. This is a known issue with bd CLI performance. Don't spend time fixing this for MVP.

3. **Factory Function**: Already implemented and working. Just needs tests and auto-discovery enhancement.

4. **Docstrings**: Most public methods already have good docstrings. Just verify completeness.

5. **Performance Benchmarks**: Can defer T127-T130 if time is short. Mark as optional in commit.

## Estimated Time

- **Minimum MVP**: 4-6 hours (skip performance benchmarks)
- **Full Complete**: 8-10 hours (include all benchmarks)

## When You're Done

1. Update tasks.md to mark all Phase 8 tasks as [X]
2. Close Phase 8 issue: `bd close codeframe-aco-huo`
3. Close main issue: `bd close codeframe-aco-xon`
4. Commit everything with comprehensive message
5. Tag release: `git tag -a v0.1.0 -m "Release v0.1.0: Beads Integration Layer MVP"`
6. Create final summary of what was accomplished

## Questions?

Read HANDOFF.md for detailed context. It has:
- Full architecture overview
- All recent changes
- Technical implementation notes
- Known issues and workarounds
- Development environment setup
- Testing strategies

Good luck! You're on the final stretch. 🎯
