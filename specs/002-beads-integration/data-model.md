# Data Model: Beads Integration Layer

**Feature**: 002-beads-integration
**Date**: 2025-11-07

## Overview

This document defines all data entities, their fields, relationships, and validation rules for the Beads Integration Layer. These models map directly to Beads JSON output and provide type-safe interfaces for Python code.

---

## Core Entities

### 1. Issue

Represents a single unit of work in the Beads DAG.

**Fields**:
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| id | str | Yes | Non-empty, valid Beads ID format | Unique issue identifier (e.g., "codeframe-aco-xon") |
| title | str | Yes | Non-empty, max 500 chars | Human-readable issue title |
| description | str | Yes | - | Detailed issue description (can be empty string) |
| status | IssueStatus | Yes | Valid enum value | Current workflow state |
| priority | int | Yes | 0-4 | Priority level (0=critical, 4=backlog) |
| issue_type | IssueType | Yes | Valid enum value | Category of work |
| created_at | datetime | Yes | Valid ISO8601/RFC3339 | When issue was created |
| updated_at | datetime | Yes | Valid ISO8601/RFC3339 | When issue was last modified |
| content_hash | str | Yes | Non-empty | SHA256 hash of issue content (Beads internal) |
| source_repo | str | Yes | Valid path | Repository path where issue was created |
| assignee | str | No | - | Username of assigned person |
| labels | List[str] | No | - | List of label strings |

**State Transitions**:
```
open → in_progress → closed
  ↓         ↓
blocked → in_progress → closed
```

**Business Rules**:
- Issue ID is immutable after creation
- status cannot transition from closed back to open (use reopen operation)
- priority can change at any time
- created_at is immutable, updated_at changes on any modification

**Relationships**:
- Has zero or more Dependencies (as blocked issue)
- Has zero or more Dependencies (as blocker issue)
- Has zero or more Comments (future)
- Belongs to one Repository

**Python Representation**:
```python
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
    labels: Optional[List[str]] = None

    def __post_init__(self):
        # Validation
        if not self.id:
            raise ValueError("Issue ID cannot be empty")
        if not (0 <= self.priority <= 4):
            raise ValueError("Priority must be 0-4")
        if not self.title:
            raise ValueError("Title cannot be empty")
```

---

### 2. IssueStatus (Enum)

Valid states for an issue in the development workflow.

**Values**:
| Value | Description | Transitions To |
|-------|-------------|----------------|
| open | Issue created but work not started | in_progress, blocked, closed |
| in_progress | Work actively happening | closed, blocked |
| blocked | Cannot proceed due to dependencies | in_progress, closed |
| closed | Work completed or cancelled | (terminal state) |

**Python Representation**:
```python
class IssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    CLOSED = "closed"
```

---

### 3. IssueType (Enum)

Categories of work tracked in Beads.

**Values**:
| Value | Description | Priority Guidance |
|-------|-------------|------------------|
| bug | Defect requiring fix | Usually P0-P2 |
| feature | New functionality | Usually P1-P3 |
| task | General work item | Usually P2-P3 |
| epic | Large multi-issue effort | Usually P1-P2 |
| chore | Maintenance work | Usually P3-P4 |

**Python Representation**:
```python
class IssueType(str, Enum):
    BUG = "bug"
    FEATURE = "feature"
    TASK = "task"
    EPIC = "epic"
    CHORE = "chore"
```

---

### 4. Dependency

Represents a relationship between two issues in the DAG.

**Fields**:
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| blocked_id | str | Yes | Valid issue ID | Issue that is blocked |
| blocker_id | str | Yes | Valid issue ID | Issue that blocks |
| dependency_type | DependencyType | Yes | Valid enum value | Nature of relationship |

**Business Rules**:
- blocked_id and blocker_id must be different (no self-dependencies)
- Adding a dependency that creates a cycle MUST be rejected
- Removing a non-existent dependency is idempotent (no error)
- Dependencies persist even if issues are closed

**Relationships**:
- References two Issues (blocked and blocker)

**Python Representation**:
```python
@dataclass
class Dependency:
    blocked_id: str
    blocker_id: str
    dependency_type: DependencyType

    def __post_init__(self):
        if self.blocked_id == self.blocker_id:
            raise ValueError("Issue cannot depend on itself")
```

---

### 5. DependencyType (Enum)

Types of relationships between issues.

**Values**:
| Value | Description | Semantics |
|-------|-------------|-----------|
| blocks | Hard dependency | blocker MUST complete before blocked can be closed |
| related | Soft association | No blocking, just informational link |
| parent-child | Hierarchical | Epic/subtask relationship |
| discovered-from | Provenance | blocked was discovered while working on blocker |

**Python Representation**:
```python
class DependencyType(str, Enum):
    BLOCKS = "blocks"
    RELATED = "related"
    PARENT_CHILD = "parent-child"
    DISCOVERED_FROM = "discovered-from"
```

---

### 6. DependencyTree

Represents the full upstream and downstream dependency graph for an issue.

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| issue_id | str | Yes | Root issue for tree query |
| blockers | List[str] | Yes | Issues that block this issue (upstream) |
| blocked_by | List[str] | Yes | Issues blocked by this issue (downstream) |

**Business Rules**:
- Tree query returns transitive closure (all ancestors and descendants)
- Empty lists if no dependencies exist
- Includes all dependency types (not filtered)

**Python Representation**:
```python
@dataclass
class DependencyTree:
    issue_id: str
    blockers: List[str]  # Upstream: blocks this issue
    blocked_by: List[str]  # Downstream: blocked by this issue
```

---

### 7. DependencyCycle

Represents a detected circular dependency path in the DAG.

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cycle_path | List[str] | Yes | Issue IDs forming the cycle |

**Business Rules**:
- First and last element are the same (cycle closure)
- Example: ["A", "B", "C", "A"] means A→B→C→A
- Cycles MUST be resolved before work can proceed

**Python Representation**:
```python
@dataclass
class DependencyCycle:
    cycle_path: List[str]

    def __str__(self) -> str:
        return " → ".join(self.cycle_path)
```

---

## Entity Relationships Diagram

```
┌─────────────┐
│   Issue     │
│ (DAG Node)  │
└──────┬──────┘
       │
       │ 1:N (as blocked)
       ├──────────────────┐
       │                  │
       │ 1:N (as blocker) │
       │                  ↓
       │         ┌────────────────┐
       └────────→│  Dependency    │
                 │  (DAG Edge)    │
                 └────────────────┘
                         │
                         │ N:1
                         ↓
                 ┌────────────────┐
                 │ DependencyType │
                 │    (Enum)      │
                 └────────────────┘
```

**Notes**:
- Each Issue can have multiple dependencies (as blocked or blocker)
- Each Dependency connects exactly two Issues
- DependencyTree is a derived entity (query result, not stored)
- DependencyCycle is a validation result (query result, not stored)

---

## Validation Rules

### Issue Validation

1. **ID Format**: Must match Beads pattern (e.g., `prefix-hash` like "codeframe-aco-xon")
2. **Title Length**: Non-empty, max 500 characters
3. **Priority Range**: Integer 0-4 inclusive
4. **Status Enum**: Must be valid IssueStatus value
5. **Type Enum**: Must be valid IssueType value
6. **Dates**: Must be valid ISO8601/RFC3339 timestamps
7. **Content Hash**: Must be non-empty SHA256 hash (validated by Beads)

### Dependency Validation

1. **Issue Existence**: Both blocked_id and blocker_id must reference existing issues
2. **No Self-Dependencies**: blocked_id ≠ blocker_id
3. **Acyclic**: Adding dependency must not create cycles in DAG
4. **Type Validity**: Must be valid DependencyType value

---

## JSON Schema Examples

### Issue JSON (from `bd show --json`)
```json
{
  "id": "codeframe-aco-xon",
  "content_hash": "a1a11394846b04994957d965eb37d2c12bac3f4f83e3c6b45fea0404e0253e49",
  "title": "Beads Integration Layer",
  "description": "Interface to Beads issue tracker for DAG management",
  "status": "open",
  "priority": 0,
  "issue_type": "feature",
  "created_at": "2025-11-06T23:11:41.486663506-07:00",
  "updated_at": "2025-11-06T23:11:41.486663506-07:00",
  "source_repo": ".",
  "assignee": null,
  "labels": []
}
```

### Issue List JSON (from `bd ready --json`)
```json
[
  {
    "id": "codeframe-aco-t49",
    "title": "Vector Memory Manager",
    "status": "in_progress",
    "priority": 0,
    "issue_type": "feature",
    ...
  },
  {
    "id": "codeframe-aco-xon",
    "title": "Beads Integration Layer",
    "status": "open",
    "priority": 0,
    "issue_type": "feature",
    ...
  }
]
```

### Dependency Tree JSON (from `bd dep tree --json`)
```json
{
  "issue_id": "codeframe-aco-p1a",
  "blockers": ["codeframe-aco-t49", "codeframe-aco-xon"],
  "blocked_by": ["codeframe-aco-cp7", "codeframe-aco-du2"]
}
```

### Cycles JSON (from `bd dep cycles --json`)
```json
{
  "cycles": [
    ["issue-A", "issue-B", "issue-C", "issue-A"],
    ["issue-X", "issue-Y", "issue-X"]
  ]
}
```

---

## Future Extensions (Not in MVP)

The following entities are NOT part of Phase 1 MVP but documented for future reference:

- **Comment**: User annotations on issues
- **Attachment**: Files linked to issues
- **Milestone**: Grouping of issues by delivery date
- **Label**: Categorization metadata
- **WorkLog**: Time tracking per issue
- **Notification**: Alert/event system

These will be added in future phases when requirements emerge.
