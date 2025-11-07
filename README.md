# Autonomous Code Orchestrator (ACO)

An AI-powered software development system that autonomously manages the complete lifecycle of code projects from specification to deployment.

## Overview

ACO combines a dependency-aware issue tracking system ([Beads](https://github.com/steveyegge/beads)) with a state machine orchestrator and a novel 3D vector memory system to enable continuous, autonomous development with minimal human intervention.

The system treats software development as a graph traversal problem where issues form nodes in a directed acyclic graph (DAG), each processed through a consistent development cycle.

## Key Innovations

### 🎯 3D Vector Memory System

Every piece of information has coordinates (x, y, z):
- **x**: Position in the DAG (which issue)
- **y**: Position in development cycle (which state)
- **z**: Memory layer (1=Architecture, 2=Interfaces, 3=Implementation, 4=Ephemeral)

This enables:
- Precise context retrieval for any agent
- Efficient rollback to any previous state
- Cross-agent knowledge sharing without corruption

### 🔄 Unified Development Cycle

Every issue follows the same cycle:
```
Pick Issue → Architect → Write Tests → Implement → Test →
Review → Respond to Feedback → [Revise/Spawn New Issue/Merge]
```

### 📊 DAG-Driven Development

All work tracked as issues in Beads with explicit dependencies:
- **blocks** - Task B must complete before task A
- **related** - Soft connection, doesn't block progress
- **parent-child** - Epic/subtask hierarchical relationship
- **discovered-from** - Auto-created when discovering related work

## Architecture

### Three Primary Layers

1. **DAG Layer (Beads)** - Manages issue dependencies and project structure
2. **State Machine Layer** - Processes each issue through development cycle
3. **Orchestrator Layer** - Traverses DAG and coordinates execution

### External Components

| Component | Purpose | Integration Point |
|-----------|---------|------------------|
| Beads | Issue tracking with Git integration | DAG management |
| Claude Code | Primary implementation agent | Cycle processor |
| Spec-kit | Specification and architecture development | Architecture stage |
| GitHub | Version control and CI/CD | All stages |

## Getting Started

### Prerequisites

1. **Install Beads**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/steveyegge/beads/main/install.sh | bash
   ```

2. **Initialize Beads in your project**:
   ```bash
   bd init
   ```

3. **Review the Constitution**:
   All work must comply with `.specify/memory/constitution.md` principles.

### Quick Start

1. **Check ready work**:
   ```bash
   bd ready
   ```

2. **Create a new issue**:
   ```bash
   bd create "Issue title" -t feature -p 1
   ```

3. **Claim and work on issue**:
   ```bash
   bd update <issue-id> --status in_progress
   # Do your work following the development cycle
   bd close <issue-id> --reason "Completed"
   ```

4. **Use Spec-kit for planning**:
   ```bash
   /speckit.specify    # Create feature spec
   /speckit.plan       # Generate implementation plan
   /speckit.tasks      # Generate actionable tasks
   /speckit.implement  # Execute implementation
   ```

## Core Principles

This project operates under seven constitutional principles:

1. **Vector Memory Architecture** - All information addressable via 3D coordinates
2. **DAG-Driven Development** - All work tracked in Beads with explicit dependencies
3. **Unified Development Cycle** - Consistent cycle for all issues
4. **Test-First Development** - 80% minimum coverage, TDD required
5. **Autonomous Operation** - Minimal human intervention with controlled escalation
6. **Scope Control via Gravity** - Progressive value thresholds prevent infinite expansion
7. **Observability and Auditability** - Complete audit trail with vector coordinates

See [.specify/memory/constitution.md](.specify/memory/constitution.md) for full details.

## Quality Standards

- **Test Coverage**: Minimum 80% required
- **Security**: Zero vulnerabilities in auth code
- **Performance**: < 10% regression without justification
- **Code Quality**: < 5% duplication

## Development Workflow

### For AI Agents

See [AGENTS.md](AGENTS.md) for comprehensive AI agent guidelines, including:
- Beads workflow patterns
- Issue lifecycle management
- Dependency management
- Integration with other tools

### For Claude Code

See [CLAUDE.md](CLAUDE.md) for Claude Code-specific guidance, including:
- Project architecture overview
- Essential Beads commands
- Spec-kit integration
- Development workflow

## MVP Test Cases

### Phase 1 MVP Targets

1. **Static Website**: < 2 hours, $5 cost, Lighthouse > 90
2. **TODO App with Auth**: < 8 hours, $20 cost, 80% coverage
3. **API + Frontend**: < 24 hours, $50 cost, all endpoints functional

## Project Structure

```
.
├── .beads/                    # Beads issue tracking database
│   └── issues.jsonl          # Git-synced issue state
├── .specify/                  # Spec-kit configuration
│   ├── memory/
│   │   └── constitution.md   # Project governance
│   └── templates/            # Planning templates
├── docs/                      # Project documentation
│   └── codeframe-aco-spec.md # Product requirements
├── specs/                     # Feature specifications (by branch)
│   └── ###-feature-name/
│       ├── spec.md
│       ├── plan.md
│       ├── tasks.md
│       └── contracts/
├── AGENTS.md                  # AI agent guidelines
├── CLAUDE.md                  # Claude Code guidance
└── README.md                  # This file
```

## Error Handling

When errors occur:
1. Tag error with vector coordinates (x, y, z)
2. Calculate impact radius from dependency graph
3. Find rollback point using partial ordering
4. Rollback while preserving unaffected work
5. Resume from safe state

## Human Intervention Classification

- **SMS (Block and wait)**: Critical path blocked, irreversible decisions
- **Email (Queue for review)**: Important but can continue with assumptions
- **Docs (Log and continue)**: FYI only, decisions documented for review

## Contributing

This project uses a strict constitutional governance model. All contributions must:
- Comply with constitutional principles
- Include tests with 80%+ coverage
- Follow the unified development cycle
- Be tracked as Beads issues with proper dependencies

## Documentation

- [Product Requirements](docs/codeframe-aco-spec.md) - Complete PRD
- [Constitution](.specify/memory/constitution.md) - Governance principles
- [AI Agent Guidelines](AGENTS.md) - For AI assistants
- [Claude Code Guidance](CLAUDE.md) - For Claude Code agents

## License

[License information to be added]

## Status

**Phase**: MVP Development (Phase 1)
- Single agent execution
- Linear dependencies
- Local deployment
- Fixed project scope
- Manual checkpoint reviews

## Contact

[Contact information to be added]
