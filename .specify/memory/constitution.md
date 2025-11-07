<!--
SYNC IMPACT REPORT
==================
Version Change: [new file] → 1.0.0 (MINOR - initial constitution)
Modified Principles: N/A (initial version)
Added Sections: All (Core Principles, Quality Standards, Development Workflow, Governance)
Removed Sections: N/A
Templates Requiring Updates:
  ✅ plan-template.md - Constitution Check section aligns with principles
  ✅ spec-template.md - User story prioritization aligns with autonomy principle
  ✅ tasks-template.md - Task organization supports dependency-aware execution
Follow-up TODOs: None
-->

# Autonomous Code Orchestrator (ACO) Constitution

## Core Principles

### I. Vector Memory Architecture (NON-NEGOTIABLE)

Every piece of information MUST be addressable via 3D coordinates (x, y, z):
- **x**: Position in the DAG (issue identifier)
- **y**: Position in development cycle (state: architect, test, implement, review, merge)
- **z**: Memory layer (1=Architecture, 2=Interfaces, 3=Implementation, 4=Ephemeral)

**Rationale**: Coordinate-based memory enables precise context retrieval, efficient rollback,
and cross-agent knowledge sharing without context pollution or corruption.

**Rules**:
- Architecture layer (z=1) is immutable once set
- All decisions MUST be tagged with vector coordinates
- Context retrieval MUST specify exact coordinates, not broad queries
- Rollback operations MUST use partial ordering on (x,y) vectors

### II. DAG-Driven Development (NON-NEGOTIABLE)

All work MUST be tracked as issues in the Beads dependency-aware issue tracker forming a
directed acyclic graph (DAG).

**Rationale**: DAG structure separates "what to build" from "how to build it", enabling
autonomous orchestration and systematic error recovery.

**Rules**:
- Every feature/bug/task MUST exist as a Beads issue
- Dependencies MUST be explicit using bd dependency types (blocks, related, parent-child, discovered-from)
- Issues MUST be selected via `bd ready` (unblocked work only)
- NO markdown TODO lists or external trackers permitted
- DAG mutations during execution MUST maintain partial ordering for rollback capability

### III. Unified Development Cycle

Every issue MUST follow the same cycle regardless of complexity:
```
Pick Issue → Architect → Write Tests → Implement → Test →
Review → Respond to Feedback → [Revise/Spawn New Issue/Merge]
```

**Rationale**: Consistent cycle enables predictable quality gates and simplifies orchestration.

**Rules**:
- All issues processed through identical stages
- Stage transitions require quality gate passage
- Three exit points only: Revise (backtrack), Spawn (create new issues), Merge (complete)
- NO skipping stages except tests when explicitly not required by spec

### IV. Test-First Development

Tests MUST be written and approved before implementation begins.

**Rationale**: TDD ensures requirements are clear, testable, and verifiable before code is written.

**Rules**:
- Tests written → User approved → Tests fail → Then implement (Red-Green-Refactor)
- Minimum 80% code coverage required
- All assertions MUST be meaningful (no placeholder tests)
- Tests MUST be independently executable

### V. Autonomous Operation with Controlled Escalation

The system MUST operate autonomously with minimal human intervention, escalating only when necessary.

**Rationale**: Reduces human orchestration burden while maintaining control over critical decisions.

**Rules**:
- Human intervention classified by urgency:
  - **SMS (Block)**: Critical path blocked, irreversible decisions
  - **Email (Queue)**: Important but can continue with assumptions
  - **Docs (Log)**: FYI only, decisions logged for review
- Agents MUST attempt autonomous resolution before escalating
- All decisions MUST be documented with rationale at vector coordinates
- Escalation MUST include full context (issue, cycle state, vector coordinates)

### VI. Scope Control via Gravity

New issues MUST pass progressively higher value thresholds as projects age.

**Rationale**: Prevents infinite scope expansion and ensures project convergence.

**Rules**:
- Gravity function: `gravity = (days_since_start / 30) + (percent_complete / 50)`
- Acceptance threshold: `issue_value / (issue_type_weight * gravity)`
- Later issues require higher business value justification
- Complexity budget MUST be enforced

### VII. Observability and Auditability

All state changes, decisions, and agent actions MUST be auditable.

**Rationale**: Enables debugging, rollback, learning, and trust in autonomous operations.

**Rules**:
- Complete audit trail in Git history
- Vector coordinates for all decisions
- Cost tracking per issue and stage
- Performance metrics per development cycle stage
- All agent reasoning MUST be logged with context

## Quality Standards

### Test Coverage
- Minimum 80% code coverage required for all implementations
- All test assertions MUST be meaningful and verify behavior
- Integration tests REQUIRED for: new library contracts, contract changes, inter-service communication, shared schemas

### Security
- Zero security vulnerabilities permitted in authentication/authorization code
- Security review REQUIRED before merge for auth-related changes
- All sensitive operations MUST be audited

### Performance
- Performance regression < 10% without explicit justification
- MVP completion targets:
  - Static website: < 2 hours, < $5
  - TODO app with auth: < 8 hours, < $20
  - API + Frontend: < 24 hours, < $50

### Code Quality
- Code duplication < 5%
- All code MUST pass linters and formatters
- Technical debt MUST be tracked as Beads issues

## Development Workflow

### Issue Lifecycle
1. **Creation**: Issue created in Beads with proper type, priority, dependencies
2. **Selection**: Agent picks from `bd ready` output (unblocked work)
3. **Claim**: Update status to `in_progress` before starting work
4. **Processing**: Follow unified development cycle
5. **Completion**: Close issue with reason, commit `.beads/issues.jsonl` with code changes
6. **Discovery**: New work discovered → create linked issue with `discovered-from` dependency

### Quality Gates
Each stage transition requires:
- **Architecture**: Success criteria defined, constraints documented, timeline estimated, stored at z=1
- **Tests**: Coverage > 80%, all assertions meaningful, tests fail initially
- **Implementation**: All tests pass, performance criteria met, no regressions
- **Review**: No critical issues, acceptable technical debt, security verified

### Error Handling
When errors occur:
1. Tag error with vector coordinates (x, y, z)
2. Calculate impact radius from dependency graph
3. Find rollback point using partial ordering: latest commit where (x, y) < (x₁, y₁)
4. Rollback while preserving unaffected work
5. Resume from safe state

### Git Integration
- All Beads state auto-syncs to `.beads/issues.jsonl`
- Commit issue state changes WITH code changes (atomic)
- NO force pushes to main/master
- All commits MUST include vector coordinates in message when relevant

## Governance

This constitution supersedes all other development practices and guidelines. All work performed in this repository MUST comply with these principles.

### Amendment Process
1. Proposed changes documented with rationale
2. Impact analysis on existing work and templates
3. Version increment per semantic versioning:
   - **MAJOR**: Backward incompatible principle changes
   - **MINOR**: New principles or materially expanded guidance
   - **PATCH**: Clarifications, wording fixes, non-semantic refinements
4. Sync impact report generated
5. Dependent templates updated before constitution merge
6. Migration plan for work-in-progress if breaking changes

### Compliance
- All PR reviews MUST verify constitutional compliance
- Agents MUST check constitution before major decisions
- Complexity MUST be justified against simplicity principle
- Deviations MUST be documented with explicit rationale and vector coordinates

### Runtime Guidance
- Use `CLAUDE.md` for agent-specific development guidance
- Use `AGENTS.md` for AI agent workflow details
- Constitution takes precedence when conflicts arise

**Version**: 1.0.0 | **Ratified**: 2025-01-06 | **Last Amended**: 2025-01-06
