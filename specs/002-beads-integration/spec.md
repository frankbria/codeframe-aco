# Feature Specification: Beads Integration Layer

**Feature Branch**: `002-beads-integration`
**Created**: 2025-11-07
**Status**: Draft
**Input**: User description: "Beads Integration Layer - Interface to Beads issue tracker for DAG management with issue CRUD operations, dependency graph queries, issue state synchronization, JSON parsing of bd output, and Git workflow integration"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Ready Issues for Work Selection (Priority: P1)

As an autonomous agent, I need to query which issues are ready to work on (no blocking dependencies) so I can select the next task to process.

**Why this priority**: This is the most critical functionality - without the ability to identify unblocked work, the entire DAG-driven workflow cannot function. This is the entry point for all autonomous orchestration.

**Independent Test**: Can be fully tested by creating test issues with various dependency states, running `bd ready`, and verifying the Python interface correctly returns only unblocked issues. Delivers immediate value by enabling work selection.

**Acceptance Scenarios**:

1. **Given** a DAG with 3 issues where issue A has no dependencies, issue B blocks C, **When** agent queries ready issues, **Then** returns issues A and B only
2. **Given** all issues are blocked by dependencies, **When** agent queries ready issues, **Then** returns empty list
3. **Given** an issue transitions from blocked to ready (blocker completed), **When** agent queries ready issues, **Then** the newly unblocked issue appears in results

---

### User Story 2 - Update Issue Status During Development Cycle (Priority: P2)

As a cycle processor, I need to update issue status (open → in_progress → closed) as I move through development stages so the DAG reflects current work state.

**Why this priority**: Essential for tracking work progress and preventing duplicate work assignment. Required before parallel agent execution. Enables basic orchestration.

**Independent Test**: Can be tested by creating an issue, updating its status through Python interface, and verifying status changes persist in Beads database. Delivers value by enabling progress tracking.

**Acceptance Scenarios**:

1. **Given** an issue with status "open", **When** agent starts work and updates status to "in_progress", **Then** issue status persists and appears in `bd list --status in_progress`
2. **Given** an issue with status "in_progress", **When** agent completes work and closes issue, **Then** issue status changes to "closed" and no longer appears in `bd ready`
3. **Given** multiple status updates in sequence, **When** agent queries issue details, **Then** current status reflects latest update

---

### User Story 3 - Retrieve Issue Details with Dependencies (Priority: P3)

As an orchestrator, I need to retrieve full issue details including dependencies, priority, type, and description so I can make informed decisions about work planning.

**Why this priority**: Enhances work selection with richer context but not strictly required for basic functionality. Enables smarter orchestration and better planning.

**Independent Test**: Can be tested by creating issues with various metadata and dependencies, then querying via Python interface and verifying all fields are correctly returned. Delivers value by enabling context-aware decision making.

**Acceptance Scenarios**:

1. **Given** an issue with priority P0, type "feature", and description, **When** agent retrieves issue details, **Then** all fields are correctly returned
2. **Given** an issue with blocking dependencies, **When** agent retrieves issue details, **Then** dependency list includes all blocker IDs
3. **Given** an issue with metadata (created date, updated date, author), **When** agent retrieves issue details, **Then** metadata fields are correctly parsed from JSON

---

### User Story 4 - Create New Issues During Discovery (Priority: P4)

As a cycle processor, I need to create new issues when discovering gaps or related work so the DAG evolves during execution.

**Why this priority**: Enables dynamic DAG growth but can be deferred - initial MVP can work with pre-defined issues only. Required for full autonomous operation.

**Independent Test**: Can be tested by using Python interface to create new issue with specified fields, then verifying issue appears in `bd list` with correct attributes. Delivers value by enabling autonomous scope expansion.

**Acceptance Scenarios**:

1. **Given** agent discovers missing functionality, **When** creating new issue with title, type, priority, **Then** issue appears in Beads with correct attributes
2. **Given** agent creates issue related to current work, **When** creating with `discovered-from` dependency, **Then** dependency link is established in DAG
3. **Given** agent creates multiple related issues, **When** adding blocking dependencies between them, **Then** dependency graph correctly reflects relationships

---

### User Story 5 - Manage Issue Dependencies (Priority: P5)

As an orchestrator, I need to add and remove dependencies between issues so the DAG accurately reflects work relationships.

**Why this priority**: Important for complex multi-issue features but not required for linear workflows. Enables advanced DAG manipulation and refactoring.

**Independent Test**: Can be tested by creating issues and manipulating dependencies via Python interface, then verifying dependency graph changes. Delivers value by enabling DAG evolution.

**Acceptance Scenarios**:

1. **Given** two independent issues, **When** adding "blocks" dependency, **Then** blocked issue no longer appears in `bd ready`
2. **Given** an incorrect dependency, **When** removing dependency, **Then** previously blocked issue becomes ready
3. **Given** complex dependency changes, **When** querying dependency tree, **Then** tree structure reflects all relationship changes

---

### Edge Cases

- What happens when Beads CLI returns non-zero exit code (e.g., invalid issue ID)?
- How does system handle malformed JSON output from `bd` commands?
- What happens when Git sync fails during issue update?
- How does system handle race conditions when multiple agents update same issue?
- What happens when circular dependencies are detected in the DAG?
- How does system handle very large DAGs (1000+ issues)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST wrap all `bd` CLI commands with Python interface (subprocess execution)
- **FR-002**: System MUST parse JSON output from `bd` commands into Python data structures
- **FR-003**: System MUST provide function to query ready issues (`bd ready`)
- **FR-004**: System MUST provide function to update issue status (open/in_progress/closed)
- **FR-005**: System MUST provide function to retrieve full issue details by ID
- **FR-006**: System MUST provide function to create new issues with type, priority, description
- **FR-007**: System MUST provide function to add dependencies between issues
- **FR-008**: System MUST provide function to remove dependencies between issues
- **FR-009**: System MUST provide function to query dependency tree for an issue
- **FR-010**: System MUST handle `bd` command errors gracefully with informative exceptions
- **FR-011**: System MUST support all Beads dependency types (blocks, related, parent-child, discovered-from)
- **FR-012**: System MUST respect Git sync behavior (automatic export/import with debouncing)
- **FR-013**: System MUST detect circular dependencies via `bd dep cycles`
- **FR-014**: System MUST provide function to list issues with filtering (status, type, priority)

### Key Entities

- **Issue**: Represents a unit of work with ID, title, status, type, priority, description, dependencies, metadata (created/updated dates, author)
- **Dependency**: Relationship between two issues with type (blocks, related, parent-child, discovered-from)
- **BeadsClient**: Python interface wrapper for all `bd` CLI operations
- **IssueStatus**: Enumeration of valid states (open, in_progress, closed)
- **IssueType**: Enumeration of valid types (feature, bug, task, epic)
- **Priority**: Enumeration of priority levels (P0, P1, P2, P3, etc.)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All `bd` CLI operations successfully wrapped with Python functions with < 100ms overhead per call
- **SC-002**: System handles malformed JSON from `bd` commands without crashing (graceful error messages)
- **SC-003**: 100% of Beads operations required for DAG orchestration are accessible via Python interface
- **SC-004**: Integration tests pass for all CRUD operations (create, read, update, delete) on real `.beads/` database
- **SC-005**: System correctly handles all 4 dependency types without data loss
- **SC-006**: Circular dependency detection identifies all cycles in test DAGs
- **SC-007**: Performance test: Query ready issues from 100-issue DAG completes in < 500ms
- **SC-008**: Zero data corruption when running concurrent operations (tested with simulated race conditions)
