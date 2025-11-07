# Autonomous Code Orchestrator (ACO) - Product Requirements Document

## 1. Executive Summary

The Autonomous Code Orchestrator (ACO) is an AI-powered software development system that autonomously manages the complete lifecycle of code projects from specification to deployment. By combining a dependency-aware issue tracking system (Beads) with a state machine orchestrator and a novel 3D vector memory system, ACO enables continuous, autonomous development with minimal human intervention.

The system treats software development as a graph traversal problem where issues form nodes in a directed acyclic graph (DAG), each processed through a consistent development cycle. The key innovation is the separation of "what to build" (DAG traversal) from "how to build it" (cycle processing), combined with a coordinate-based memory system that ensures context coherence across multiple AI agents.

## 2. Problem Statement

Current AI-assisted development tools require constant human orchestration, suffer from context window degradation, and lack coordination between multiple agents. Developers spend significant time:
- Managing AI context and prompts
- Coordinating between different AI tools
- Resolving conflicts between AI-generated code
- Manually tracking project state and dependencies
- Recovering from errors that cascade through the codebase

ACO solves these problems by providing autonomous orchestration, precise context management, and systematic error recovery.

## 3. Architecture Overview

### 3.1 Core Architecture

The system consists of three primary layers:

1. **DAG Layer (Beads)**: Manages issue dependencies and project structure
2. **State Machine Layer**: Processes each issue through a consistent development cycle
3. **Orchestrator Layer**: Traverses the DAG and coordinates execution

### 3.2 The Development Cycle

Every issue follows the same cycle:
```
Pick Issue → Architect → Write Tests → Implement → Test → 
Review → Respond to Feedback → [Revise/Spawn New Issue/Merge]
```

### 3.3 The 3D Vector Memory System

Every piece of information in the project has coordinates (x, y, z):
- **x**: Position in the DAG (which issue)
- **y**: Position in the development cycle (which state)
- **z**: Memory layer (1=Architecture, 2=Interfaces, 3=Implementation, 4=Ephemeral)

This enables:
- Precise context retrieval for any agent
- Efficient rollback to any previous state
- Cross-agent knowledge sharing without corruption

## 4. Component Specifications

### 4.1 External Components

| Component | Purpose | Integration Point |
|-----------|---------|------------------|
| Beads | Issue tracking with Git integration | DAG management |
| Claude Code | Primary implementation agent | Cycle processor |
| Traycer.ai | Independent planning and verification | Review stage |
| CodeRabbit | PR review and bug detection | Review stage |
| Spec-kit | Specification and architecture development | Architecture stage |
| GitHub | Version control and CI/CD | All stages |
| Zapier | Webhook orchestration | Event routing |
| SendGrid/SMS | Human communication | Escalation system |

### 4.2 Core System Components

#### 4.2.1 DAG Orchestrator
```python
class DAGOrchestrator:
    """
    Responsibilities:
    - Select next issue(s) to process
    - Detect and handle dependency deadlocks
    - Manage DAG mutations during execution
    - Track overall project progress
    """
```

#### 4.2.2 Cycle Processor
```python
class CycleProcessor:
    """
    Responsibilities:
    - Execute each stage of the development cycle
    - Manage tool integration for each stage
    - Handle stage failures and retries
    - Triage feedback (revise/spawn/continue)
    """
```

#### 4.2.3 Vector Memory Manager
```python
class VectorMemoryManager:
    """
    Responsibilities:
    - Store information at coordinates
    - Retrieve context for agents
    - Maintain immutability of architecture layer
    - Synchronize with Git for persistence
    """
```

#### 4.2.4 Rollback Controller
```python
class RollbackController:
    """
    Responsibilities:
    - Identify error impact radius
    - Calculate rollback point using partial ordering
    - Orchestrate rollback execution
    - Preserve forward progress where possible
    """
```

#### 4.2.5 Human Interaction Router
```python
class HumanInteractionRouter:
    """
    Channel selection based on urgency/impact:
    - SMS: Immediate blocking issues
    - Email: Important but can continue with assumptions
    - Docs: FYI, decisions logged for review
    """
```

## 5. Functional Requirements

### 5.1 Project Initialization
- System accepts a project description
- Spec-kit generates initial architecture and specifications
- Initial DAG created with bootstrap issues
- Project memory initialized at layer 1 (architecture)

### 5.2 Issue Processing
- System selects issues with satisfied dependencies
- Each issue processed through standard cycle
- Context built from 3D vector memory
- Results stored back to memory with coordinates

### 5.3 Dynamic DAG Evolution
- New issues created when gaps discovered
- Dependencies automatically tracked
- DAG complexity limited by "gravity" function
- Later issues require higher value to be accepted

### 5.4 Quality Gates
Each stage transition requires quality criteria:
- Architecture: Has success criteria, constraints, timeline
- Tests: Coverage > 80%, all assertions meaningful
- Implementation: Passes tests, meets performance criteria
- Review: No critical issues, acceptable technical debt

### 5.5 Error Handling
- Errors tagged with vector coordinates
- Impact radius calculated from dependencies
- Rollback to last safe state via partial ordering
- Cascading changes identified and reverted

### 5.6 Resource Management
- API cost budget per hour/project
- Maximum parallel agents
- Context window limits per issue
- Retry budgets per stage

### 5.7 Human Intervention Classification
Issues requiring human input are classified by urgency and impact:
- **SMS (Block and wait)**: Critical path blocked, irreversible decisions
- **Email (Queue for review)**: Important but can continue with assumptions
- **Docs (Log and continue)**: FYI only, decisions documented for later review

## 6. Non-Functional Requirements

### 6.1 Performance
- MVP project completion < 24 hours
- Response to human intervention < 5 minutes
- State recovery after crash < 1 minute

### 6.2 Reliability
- System recoverable from any crash point
- All state persisted to Git
- Atomic operations for critical changes

### 6.3 Cost
- Static website < $5
- TODO app < $20
- Full API + Frontend < $50

### 6.4 Quality
- Minimum 80% test coverage
- Zero security vulnerabilities in auth code
- Performance regression < 10%
- Code duplication < 5%

### 6.5 Observability
- Complete audit trail in Git history
- Vector coordinates for all decisions
- Cost accumulation tracking
- Performance metrics per stage

## 7. MVP Test Cases

### 7.1 Test Case 1: Static Website
**Purpose**: Validate basic orchestration
- **Complexity**: 5-10 DAG nodes
- **Success Criteria**:
  - Completion < 2 hours
  - Zero human interventions
  - Cost < $5
  - Lighthouse score > 90

### 7.2 Test Case 2: TODO App with Authentication
**Purpose**: Validate stateful development and security handling
- **Complexity**: 20-30 DAG nodes
- **Success Criteria**:
  - Completion < 8 hours
  - < 3 human interventions
  - Cost < $20
  - Test coverage > 80%
  - Authentication functional
  - No security vulnerabilities

### 7.3 Test Case 3: API Framework with Frontend
**Purpose**: Validate complex orchestration and integration
- **Complexity**: 50-100 DAG nodes
- **Success Criteria**:
  - Completion < 24 hours
  - < 5 human interventions
  - Cost < $50
  - All endpoints functional
  - Frontend-backend integrated
  - API documented
  - Successfully deployed

## 8. Implementation Phases

### Phase 1: MVP (Month 1-2)
- Single agent execution (no parallelism)
- Linear dependencies only
- Local deployment only
- Fixed project scope
- Manual checkpoint reviews

### Phase 2: Enhanced Orchestration (Month 3-4)
- Parallel agent execution
- Complex DAG dependencies
- Staging environment deployment
- Dynamic scope with gravity limits
- Automated checkpoint decisions

### Phase 3: Production Ready (Month 5-6)
- Production deployment pipeline
- Cross-project learning
- Cost optimization
- Performance optimization
- Multi-project orchestration

## 9. Success Metrics

### 9.1 Primary Metrics
- **Autonomy Rate**: % of projects completed without human intervention
- **Cost Efficiency**: $ per function point delivered
- **Time Efficiency**: Hours from spec to deployment
- **Quality Score**: Composite of coverage, performance, security

### 9.2 Secondary Metrics
- DAG growth factor per project
- Context retrieval accuracy
- Rollback frequency and success rate
- Human intervention classification distribution

## 10. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Infinite DAG growth | Project never completes | Gravity function + complexity budget |
| Context corruption | Agents work at cross purposes | 3D vector memory system |
| Cascading errors | Entire project rolled back | Partial ordering + blast radius calculation |
| API cost overrun | Budget exceeded | Hard limits + cost accumulation tracking |
| Quality degradation | Broken code shipped | Quality ratchet + mandatory gates |

## 11. Dependencies

### 11.1 Technical Dependencies
- GitHub API access
- Claude API access
- Git command line tools
- Python/Node.js runtime
- PostgreSQL/SQLite for state

### 11.2 Service Dependencies
- Beads issue tracker
- Various AI service subscriptions
- SMS/Email service accounts

## 12. Future Enhancements (V2+)

- Pattern learning from errors
- Cross-project memory transfer
- Sophisticated parallelization strategies
- Multi-language support
- Custom quality gates per project type
- Real-time collaboration with human developers
- Automatic performance optimization
- Security vulnerability patching

## 13. Appendix: Key Innovations

### A. The 3D Vector Memory System
The coordinate-based memory system enables precise context management without window pollution. Each decision exists at specific coordinates (x, y, z), retrievable by any agent:
- **x-coordinate**: Position in the DAG (issue identifier)
- **y-coordinate**: Position in development cycle (state)
- **z-coordinate**: Memory layer (1=Architecture, 2=Interfaces, 3=Implementation, 4=Ephemeral)

This allows any agent to query exactly the context it needs, such as "give me the database schema" by requesting (x=2, y=3, z=1) where issue 2 defined the database at the architecture stage.

### B. Vector-Based Rollback
Using partial ordering on (x,y) vectors enables intelligent rollback that preserves maximum forward progress while reverting errors. When an error occurs at vector (x₁, y₁):
1. Calculate the blast radius based on dependencies
2. Find the latest commit where vector (x, y) < (x₁, y₁) in partial order
3. Rollback to that commit while preserving unaffected work
4. Resume execution from the safe state

### C. DAG Evolution with Order-Maintenance Structure
The DAG is mutable during execution, requiring an order-maintenance data structure to ensure every node remains comparable for rollback purposes. We implement this using a self-balancing tree structure (Treap or B-tree based list) that:

1. **Maintains topological ordering** as nodes are inserted
2. **Supports O(log n) insertion** between arbitrary nodes
3. **Provides O(log n) comparison** between any two nodes
4. **Handles relabeling** when the ordering space becomes dense

When issues are spawned:
- **Blocking issues**: Inserted immediately before parent in the order
- **Following issues**: Inserted immediately after parent
- **Parallel issues**: Inserted in a range near the parent

This ensures partial ordering for vector-based rollback remains valid throughout execution, regardless of DAG complexity or growth patterns.

### D. Unified Development Cycle
Every issue, regardless of complexity, follows the same cycle. This simplifies orchestration and enables predictable quality gates. The three exit points from the cycle (revise, spawn, merge) handle all possible outcomes:
- **Revise**: Backtrack in the cycle when feedback requires changes
- **Spawn**: Create new issues when gaps are discovered
- **Merge**: Complete the issue and update the DAG

### E. Gravity-Based Scope Control
To prevent infinite scope expansion, the system implements a "gravity" function that makes it progressively harder to add new issues as the project ages and approaches completion:

```python
gravity = (days_since_start / 30) + (percent_complete / 50)
acceptance_threshold = issue_value / (issue_type_weight * gravity)
```

This ensures projects converge toward completion rather than expanding indefinitely.

---

**Document Version**: 1.0  
**Date**: November 2024  
**Status**: Final Draft  
**Author**: Frank Fiegel  
**Next Steps**: Begin Phase 1 MVP implementation with static website test case