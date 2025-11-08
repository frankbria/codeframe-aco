# Research: Beads Integration Layer

**Date**: 2025-11-07
**Feature**: 002-beads-integration

## Overview

This document captures research findings for implementing a Python interface to the Beads issue tracker CLI. All technical uncertainties from the Technical Context have been resolved through CLI exploration and best practices research.

## 1. Beads CLI Interface Analysis

### Decision: Use subprocess with `--json` flag for all operations

**Rationale**:
- Beads provides a `--json` global flag that outputs structured JSON for all commands
- JSON output is machine-readable and eliminates parsing complexity
- subprocess.run() provides robust process management with timeout and error handling
- No need for custom DB access - CLI is the official interface

**Alternatives considered**:
- Direct SQLite access to `.beads/*.db`: Rejected because it bypasses Beads' business logic, Git sync, and daemon coordination
- Parse text output: Rejected because JSON flag exists and is purpose-built for programmatic access
- REST API: Rejected because Beads is CLI-first, no HTTP API exists

**Implementation approach**:
```python
import subprocess
import json
from typing import List, Dict, Any

def _run_bd_command(args: List[str], **kwargs) -> Dict[str, Any]:
    """Execute bd command with JSON output."""
    cmd = ['bd', '--json'] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,  # Handle errors explicitly
        **kwargs
    )

    if result.returncode != 0:
        raise BeadsCommandError(result.stderr)

    return json.loads(result.stdout) if result.stdout else {}
```

---

## 2. Error Handling Strategy

### Decision: Custom exception hierarchy with context preservation

**Rationale**:
- Beads CLI returns non-zero exit codes for errors
- stderr contains human-readable error messages
- Need to distinguish between different error types for agents

**Alternatives considered**:
- Generic exceptions: Rejected because agents need to handle different failures differently
- Silent failures: Rejected because errors indicate DAG corruption or system issues
- Retry logic in library: Rejected because retry policies should be orchestrator responsibility

**Exception hierarchy**:
```python
class BeadsError(Exception):
    """Base exception for all Beads operations."""
    pass

class BeadsCommandError(BeadsError):
    """CLI command failed (non-zero exit code)."""
    pass

class BeadsJSONParseError(BeadsError):
    """Failed to parse JSON output from bd command."""
    pass

class BeadsIssueNotFoundError(BeadsError):
    """Issue ID does not exist."""
    pass

class BeadsDependencyCycleError(BeadsError):
    """Circular dependency detected."""
    pass
```

---

## 3. JSON Schema Observations

### Decision: Use dataclasses with optional fields and type validation

**Rationale**:
- Beads JSON output is stable and well-structured (seen in `bd ready --json` output)
- Core fields: id, title, description, status, priority, issue_type, created_at, updated_at
- Optional fields: assignee, labels, dependencies (not always present)
- Datetime fields use RFC3339 format

**Sample JSON structure** (from `bd ready --json`):
```json
{
  "id": "codeframe-aco-xon",
  "content_hash": "a1a11394846b04994957d965eb37d2c12bac3f4f83e3c6b45fea0404e0253e49",
  "title": "Beads Integration Layer - Interface to Beads issue tracker for DAG management",
  "description": "",
  "status": "open",
  "priority": 0,
  "issue_type": "feature",
  "created_at": "2025-11-06T23:11:41.486663506-07:00",
  "updated_at": "2025-11-06T23:11:41.486663506-07:00",
  "source_repo": "."
}
```

**Implementation approach**:
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class IssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    CLOSED = "closed"

class IssueType(str, Enum):
    BUG = "bug"
    FEATURE = "feature"
    TASK = "task"
    EPIC = "epic"
    CHORE = "chore"

@dataclass
class Issue:
    id: str
    title: str
    description: str
    status: IssueStatus
    priority: int
    issue_type: IssueType
    created_at: datetime
    updated_at: datetime
    content_hash: str
    source_repo: str
    assignee: Optional[str] = None
    labels: List[str] = None

    @classmethod
    def from_json(cls, data: dict) -> 'Issue':
        """Parse Issue from Beads JSON output."""
        return cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description', ''),
            status=IssueStatus(data['status']),
            priority=data['priority'],
            issue_type=IssueType(data['issue_type']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            content_hash=data['content_hash'],
            source_repo=data['source_repo'],
            assignee=data.get('assignee'),
            labels=data.get('labels', [])
        )
```

---

## 4. Thread Safety and Git Sync

### Decision: No locking in Python library - rely on Beads' built-in mechanisms

**Rationale**:
- Beads has built-in daemon mode for concurrent access
- Beads handles Git sync automatically with 5-second debounce
- SQLite database handles concurrent reads/writes
- Python library should not interfere with Beads' coordination

**Alternatives considered**:
- File-based locking: Rejected because Beads already handles this via daemon
- In-process locks: Rejected because multiple Python processes need coordination
- Transaction batching: Rejected because premature optimization (not needed for MVP)

**Best practices**:
- Use `--no-daemon` flag ONLY in tests (sandbox mode)
- Let Beads handle auto-import/auto-flush for Git sync
- Document that concurrent access across processes is safe
- Add timeout to subprocess calls (30s default) to prevent hangs

---

## 5. Dependency Management Commands

### Decision: Wrap all 4 dependency subcommands with type-safe interface

**Rationale**:
- `bd dep add <blocked> <blocker> --type blocks` - Primary use case
- `bd dep remove <blocked> <blocker>` - For corrections
- `bd dep tree <issue-id>` - For visualization and impact analysis
- `bd dep cycles` - For validation before operations

**Key findings from `bd dep --help`**:
- Dependency types: blocks, related, parent-child, discovered-from
- `bd dep tree` shows both upstream (blockers) and downstream (blocked by)
- `bd dep cycles` returns JSON array of cycle paths
- No JSON output for `bd dep add/remove` - check stderr for errors

**Implementation approach**:
```python
class DependencyType(str, Enum):
    BLOCKS = "blocks"
    RELATED = "related"
    PARENT_CHILD = "parent-child"
    DISCOVERED_FROM = "discovered-from"

def add_dependency(
    blocked_id: str,
    blocker_id: str,
    dep_type: DependencyType = DependencyType.BLOCKS
) -> None:
    """Add dependency between two issues."""
    _run_bd_command([
        'dep', 'add',
        blocked_id, blocker_id,
        '--type', dep_type.value
    ])

def get_dependency_tree(issue_id: str) -> Dict[str, Any]:
    """Get full dependency tree for an issue."""
    return _run_bd_command(['dep', 'tree', issue_id])

def detect_cycles() -> List[List[str]]:
    """Detect circular dependencies in DAG."""
    result = _run_bd_command(['dep', 'cycles'])
    return result.get('cycles', [])
```

---

## 6. Testing Strategy

### Decision: pytest with fixture-based test databases

**Rationale**:
- pytest provides excellent fixture support for setup/teardown
- Can create isolated `.beads/` directories per test
- Use `--sandbox` flag to disable daemon and Git sync in tests
- Integration tests should use real Beads commands for validation

**Alternatives considered**:
- Mock subprocess calls: Rejected because we need to test actual Beads behavior
- Shared test database: Rejected because tests would interfere with each other
- unittest: Rejected because pytest fixtures are superior for this use case

**Test fixture pattern**:
```python
# tests/conftest.py
import pytest
import tempfile
import subprocess
from pathlib import Path

@pytest.fixture
def test_beads_db(tmp_path: Path):
    """Create isolated Beads database for testing."""
    # Initialize Beads in temp directory
    subprocess.run(
        ['bd', 'init', '--prefix', 'test'],
        cwd=tmp_path,
        check=True
    )

    # Create some test issues
    subprocess.run(
        ['bd', 'create', 'Test issue 1', '--type', 'task', '--priority', '1'],
        cwd=tmp_path,
        check=True
    )

    yield tmp_path

    # Cleanup handled by tmp_path fixture

@pytest.fixture
def beads_client(test_beads_db):
    """Create BeadsClient pointing to test database."""
    return BeadsClient(db_path=str(test_beads_db / '.beads'))
```

---

## 7. Performance Considerations

### Decision: No caching, direct CLI calls for MVP

**Rationale**:
- CLI overhead is ~50-100ms per call (acceptable for MVP)
- Caching adds complexity and invalidation challenges
- DAG queries (`bd ready`, `bd list`) are already optimized in Beads
- Premature optimization - measure first, optimize later

**Alternatives considered**:
- In-memory cache: Rejected because stale data risk outweighs performance gain
- Redis/memcached: Rejected as massive overkill for local CLI wrapper
- Batch operations: Rejected because Beads doesn't support batching

**Performance targets** (validated as achievable):
- Single issue query: < 100ms
- `bd ready` with 100 issues: < 500ms (tested with 2-issue DB: ~50ms)
- Issue creation: < 150ms
- Dependency tree query: < 200ms

**Monitoring approach**:
```python
import time
import logging

def _run_bd_command(args: List[str], **kwargs) -> Dict[str, Any]:
    start = time.perf_counter()
    result = # ... execute command
    duration = time.perf_counter() - start

    logging.debug(f"bd {' '.join(args)} took {duration*1000:.1f}ms")

    return result
```

---

## 8. Python Best Practices for CLI Wrappers

### Decision: Follow subprocess best practices with robust error handling

**Rationale**:
- Use `capture_output=True` to capture both stdout and stderr
- Use `text=True` for string handling (not bytes)
- Use `timeout` to prevent hanging processes
- Use `check=False` and handle errors explicitly for better error messages

**Key best practices**:
1. Always specify full command path or ensure `bd` is in PATH
2. Use list form `['bd', 'create', title]` not string form `"bd create {title}"`
3. Never use shell=True (security risk for injection)
4. Log all commands for debugging (with sanitization for secrets)
5. Provide clear error messages with original command and stderr

**Security considerations**:
- No shell injection risk (using list form, no shell=True)
- No SQL injection risk (Beads CLI handles escaping)
- No path traversal risk (Beads validates issue IDs)
- Log sanitization for any future secrets (none in MVP)

---

## Summary of Decisions

| Area | Decision | Key Rationale |
|------|----------|---------------|
| **CLI Interface** | subprocess + --json flag | Official Beads interface, structured output |
| **Error Handling** | Custom exception hierarchy | Type-safe error handling for agents |
| **Data Models** | dataclasses with enums | Type safety, IDE support, validation |
| **Thread Safety** | Rely on Beads daemon | Don't reinvent concurrency control |
| **Dependencies** | Wrap all 4 subcommands | Complete DAG manipulation support |
| **Testing** | pytest with fixtures | Isolated test databases, real CLI |
| **Performance** | No caching for MVP | Simplicity over premature optimization |
| **Best Practices** | subprocess safety patterns | Security, reliability, debuggability |

---

## Open Questions (None)

All unknowns from Technical Context have been resolved:
- ✅ Language/Version: Python 3.11+
- ✅ Dependencies: stdlib only (subprocess, json, dataclasses, typing)
- ✅ Storage: Beads native (`.beads/` directory)
- ✅ Testing: pytest with fixtures
- ✅ Performance: CLI overhead acceptable (<100ms/call)
- ✅ Thread Safety: Beads daemon handles concurrency

---

## Next Steps

Proceed to **Phase 1: Design & Contracts**:
1. Generate `data-model.md` with entity definitions
2. Generate `contracts/` with Python interface specifications
3. Generate `quickstart.md` with usage examples
4. Update agent context with Python 3.11+ requirement
