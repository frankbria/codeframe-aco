# ACO Feature Breakdown - Phase 1 MVP

**Created**: 2025-11-06
**Source**: PRD in docs/codeframe-aco-spec.md
**Status**: Tracked in Beads

## Overview

This document lists the 10 core features extracted from the ACO PRD, organized by implementation priority and dependencies. All features are tracked as Beads issues with proper dependency relationships.

## Feature List

### Foundation Layer (Priority 0 - Build First)

#### 1. Vector Memory Manager
**Beads ID**: `codeframe-aco-t49`
**Priority**: P0 (Critical)
**Dependencies**: None
**Status**: ✅ Ready to specify

**Description**: Core coordinate-based storage system (x, y, z) that enables:
- 3D coordinate storage and retrieval
- Layer immutability (z=1 architecture layer)
- Git synchronization for persistence
- Context retrieval for agents
- Precise context management without window pollution

**Why First**: Foundation for all other components. No dependencies. Well-defined in PRD Appendix A.

---

#### 2. Beads Integration Layer
**Beads ID**: `codeframe-aco-xon`
**Priority**: P0 (Critical)
**Dependencies**: None
**Status**: ✅ Ready to specify

**Description**: Interface to Beads issue tracker for DAG management:
- Issue CRUD operations via bd CLI
- Dependency graph queries
- Issue state synchronization
- JSON parsing of bd output
- Integration with Git workflow

**Why Second**: Enables DAG-driven development. Can be built in parallel with Vector Memory Manager.

---

### Core System Layer (Priority 1 - Build on Foundation)

#### 3. DAG Orchestrator
**Beads ID**: `codeframe-aco-p1a`
**Priority**: P1 (High)
**Dependencies**: Blocked by codeframe-aco-t49, codeframe-aco-xon
**Status**: ⏸️ Waiting for foundation

**Description**: Issue selection, dependency management, deadlock detection:
- Select next issue(s) to process via bd ready
- Detect and handle dependency deadlocks
- Manage DAG mutations during execution
- Track overall project progress
- Implement gravity function for scope control

**Blocks**: Human Interaction Router, Resource Management, Observability

---

#### 4. Cycle Processor
**Beads ID**: `codeframe-aco-2sd`
**Priority**: P1 (High)
**Dependencies**: Blocked by codeframe-aco-t49, codeframe-aco-xon
**Status**: ⏸️ Waiting for foundation

**Description**: Executes development cycle stages for each issue:
- Execute each stage: Architect → Test → Implement → Review → Merge
- Manage tool integration for each stage
- Handle stage failures and retries
- Triage feedback (revise/spawn/continue)
- Enforce unified development cycle

**Blocks**: Human Interaction Router, External Tool Integration, Quality Gates, Resource Management, Observability

---

#### 5. Rollback Controller
**Beads ID**: `codeframe-aco-18s`
**Priority**: P1 (High)
**Dependencies**: Blocked by codeframe-aco-t49, codeframe-aco-xon
**Status**: ⏸️ Waiting for foundation

**Description**: Error handling with vector-based rollback:
- Identify error impact radius from dependency graph
- Calculate rollback point using partial ordering on (x,y) vectors
- Orchestrate rollback execution via Git
- Preserve forward progress where possible
- Resume from safe state

**Blocks**: None (can be used independently)

---

### Integration Layer (Priority 2 - Connect External Tools)

#### 6. Human Interaction Router
**Beads ID**: `codeframe-aco-cp7`
**Priority**: P2 (Medium)
**Dependencies**: Blocked by codeframe-aco-p1a, codeframe-aco-2sd
**Status**: ⏸️ Waiting for core system

**Description**: SMS/Email/Docs escalation system:
- Channel selection based on urgency/impact
- SMS: Immediate blocking issues (critical path)
- Email: Important but can continue with assumptions
- Docs: FYI, decisions logged for review
- Integration with SendGrid/SMS services

**Blocks**: None (enables autonomous operation)

---

#### 7. External Tool Integration
**Beads ID**: `codeframe-aco-du2`
**Priority**: P2 (Medium)
**Dependencies**: Blocked by codeframe-aco-2sd
**Status**: ⏸️ Waiting for cycle processor

**Description**: Claude Code, Spec-kit, GitHub integration:
- Claude Code: Primary implementation agent
- Spec-kit: Architecture stage tool
- GitHub: Version control and CI/CD
- Traycer.ai: Review stage verification (future)
- CodeRabbit: PR review (future)
- Zapier: Webhook orchestration (future)

**Blocks**: None (enables cycle processor capabilities)

---

#### 8. Quality Gates System
**Beads ID**: `codeframe-aco-a85`
**Priority**: P2 (Medium)
**Dependencies**: Blocked by codeframe-aco-2sd
**Status**: ⏸️ Waiting for cycle processor

**Description**: Stage transition validation:
- Architecture: Success criteria, constraints, timeline
- Tests: Coverage > 80%, meaningful assertions
- Implementation: Tests pass, performance criteria met
- Review: No critical issues, acceptable technical debt
- Enforce constitutional quality standards

**Blocks**: None (validates cycle processor transitions)

---

### Quality & Observability Layer (Priority 3 - Polish & Monitor)

#### 9. Resource Management System
**Beads ID**: `codeframe-aco-9bv`
**Priority**: P3 (Low)
**Dependencies**: Blocked by codeframe-aco-p1a, codeframe-aco-2sd
**Status**: ⏸️ Waiting for core system

**Description**: Cost tracking, budgets, limits:
- API cost budget per hour/project
- Maximum parallel agents
- Context window limits per issue
- Retry budgets per stage
- Cost accumulation tracking
- Budget enforcement

**Blocks**: None (monitors resource usage)

---

#### 10. Observability & Metrics
**Beads ID**: `codeframe-aco-s1n`
**Priority**: P3 (Low)
**Dependencies**: Blocked by codeframe-aco-t49, codeframe-aco-p1a, codeframe-aco-2sd
**Status**: ⏸️ Waiting for core system

**Description**: Audit trail, performance tracking:
- Complete audit trail in Git history
- Vector coordinates for all decisions
- Cost tracking per issue and stage
- Performance metrics per development cycle stage
- Agent reasoning logs with context
- Success metrics tracking (autonomy rate, cost efficiency, time efficiency)

**Blocks**: None (observes system behavior)

---

## Implementation Order

Based on dependencies, the recommended implementation order is:

1. **Phase 1 - Foundation** (No blockers, can run in parallel):
   - `codeframe-aco-t49`: Vector Memory Manager
   - `codeframe-aco-xon`: Beads Integration Layer

2. **Phase 2 - Core System** (After Phase 1 complete):
   - `codeframe-aco-p1a`: DAG Orchestrator
   - `codeframe-aco-2sd`: Cycle Processor
   - `codeframe-aco-18s`: Rollback Controller

3. **Phase 3 - Integration** (After Phase 2 complete):
   - `codeframe-aco-cp7`: Human Interaction Router
   - `codeframe-aco-du2`: External Tool Integration
   - `codeframe-aco-a85`: Quality Gates System

4. **Phase 4 - Quality & Observability** (After Phase 2/3 complete):
   - `codeframe-aco-9bv`: Resource Management System
   - `codeframe-aco-s1n`: Observability & Metrics

## Next Steps

### Current Ready Work
```bash
bd ready
```
Shows 2 issues ready to specify:
1. `codeframe-aco-t49`: Vector Memory Manager ⭐ **START HERE**
2. `codeframe-aco-xon`: Beads Integration Layer

### To Specify a Feature
```bash
/speckit.specify <feature description from this document>
```

Example:
```bash
/speckit.specify Vector Memory Manager - Core coordinate-based storage system that provides 3D coordinate storage and retrieval, layer immutability, Git synchronization, and context retrieval for agents
```

### To View Dependencies
```bash
bd dep tree <issue-id>
```

Example:
```bash
bd dep tree codeframe-aco-p1a
```

## Beads Commands Reference

```bash
# View all features
bd list

# View ready work (no blockers)
bd ready

# View specific issue
bd show codeframe-aco-t49

# View dependency tree
bd dep tree codeframe-aco-p1a

# Update issue status
bd update codeframe-aco-t49 --status in_progress
```

## Constitutional Alignment

All features align with the ACO Constitution principles:

- ✅ **Vector Memory Architecture**: Feature #1 implements this directly
- ✅ **DAG-Driven Development**: Feature #2 & #3 enable this
- ✅ **Unified Development Cycle**: Feature #4 enforces this
- ✅ **Test-First Development**: Feature #8 validates this
- ✅ **Autonomous Operation**: Feature #6 enables controlled escalation
- ✅ **Scope Control**: Feature #3 implements gravity function
- ✅ **Observability**: Feature #10 provides audit trail

---

**Next Action**: Start with `/speckit.specify` for Vector Memory Manager (codeframe-aco-t49)
