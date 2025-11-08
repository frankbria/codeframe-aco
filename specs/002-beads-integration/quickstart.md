# Quickstart Guide: Beads Integration Layer

**Feature**: 002-beads-integration
**Date**: 2025-11-07
**Audience**: Developers implementing or using the Beads Python interface

## Overview

This guide provides quick examples of how to use the Beads Integration Layer to interact with the Beads issue tracker programmatically from Python code.

## Prerequisites

- Python 3.11+
- Beads CLI installed and in PATH (`which bd` should work)
- Existing Beads repository with `.beads/` directory

## Installation

```bash
# Install from source (during development)
cd /path/to/codeframe-aco
pip install -e .

# Import in your code
from beads import create_beads_client, IssueStatus, IssueType, DependencyType
```

## Basic Usage

### 1. Create a Client

```python
from beads import create_beads_client

# Auto-discover .beads/ directory (typical usage)
client = create_beads_client()

# Or specify explicit database path
client = create_beads_client(db_path="/path/to/project/.beads")
```

### 2. Query Ready Issues

```python
# Get all ready issues (no blocking dependencies)
ready_issues = client.get_ready_issues()

for issue in ready_issues:
    print(f"{issue.id}: {issue.title} (P{issue.priority})")

# Filter by priority
critical_ready = client.get_ready_issues(priority=0)

# Limit results
next_3_tasks = client.get_ready_issues(limit=3)
```

### 3. Get Issue Details

```python
# Get specific issue by ID
issue = client.get_issue("codeframe-aco-xon")

print(f"Title: {issue.title}")
print(f"Status: {issue.status}")
print(f"Type: {issue.issue_type}")
print(f"Priority: {issue.priority}")
print(f"Created: {issue.created_at}")
print(f"Description: {issue.description}")
```

### 4. Create New Issue

```python
from beads import IssueType

# Create a new feature
new_issue_id = client.create_issue(
    title="Implement caching layer",
    issue_type=IssueType.FEATURE,
    priority=2,
    description="Add Redis caching to improve performance"
)

print(f"Created issue: {new_issue_id}")

# Create a bug report
bug_id = client.create_issue(
    title="Fix authentication timeout",
    issue_type=IssueType.BUG,
    priority=0,
    description="Users are getting logged out after 5 minutes"
)
```

### 5. Update Issue Status

```python
from beads import IssueStatus

# Start work on an issue
client.update_issue_status("codeframe-aco-xon", IssueStatus.IN_PROGRESS)

# Complete an issue
client.update_issue_status("codeframe-aco-xon", IssueStatus.CLOSED)

# Or use convenience method
client.close_issue("codeframe-aco-xon")
```

### 6. Manage Dependencies

```python
from beads import DependencyType

# Add a blocking dependency
client.add_dependency(
    blocked_id="codeframe-aco-p1a",  # DAG Orchestrator
    blocker_id="codeframe-aco-xon",  # Beads Integration (this feature)
    dep_type=DependencyType.BLOCKS
)

# Add a related link (non-blocking)
client.add_dependency(
    blocked_id="codeframe-aco-du2",
    blocker_id="codeframe-aco-xon",
    dep_type=DependencyType.RELATED
)

# Remove a dependency
client.remove_dependency(
    blocked_id="codeframe-aco-p1a",
    blocker_id="codeframe-aco-xon"
)
```

### 7. Query Dependency Tree

```python
# Get full dependency tree for an issue
tree = client.get_dependency_tree("codeframe-aco-p1a")

print(f"Issue: {tree.issue_id}")
print(f"Blocked by (upstream): {tree.blockers}")
print(f"Blocks (downstream): {tree.blocked_by}")

# Check if issue is ready (no blockers)
if not tree.blockers:
    print("Issue is ready to work on!")
```

### 8. Detect Circular Dependencies

```python
# Check entire DAG for cycles
cycles = client.detect_dependency_cycles()

if cycles:
    print(f"WARNING: {len(cycles)} circular dependencies detected!")
    for cycle in cycles:
        print(f"  Cycle: {' → '.join(cycle)}")
else:
    print("No circular dependencies found. DAG is healthy!")
```

## Complete Example: Autonomous Work Selection

```python
"""
Example: Autonomous agent selecting and claiming next work item
"""
from beads import create_beads_client, IssueStatus

def select_next_task():
    """Select the highest priority ready task and claim it."""
    client = create_beads_client()

    # Get ready issues sorted by priority
    ready = client.get_ready_issues(limit=10)

    if not ready:
        print("No ready work available!")
        return None

    # Select highest priority (lowest number)
    next_task = min(ready, key=lambda issue: issue.priority)

    print(f"Selected: {next_task.id} - {next_task.title} (P{next_task.priority})")

    # Claim the issue
    client.update_issue_status(next_task.id, IssueStatus.IN_PROGRESS)

    print(f"Claimed issue {next_task.id} for processing")

    return next_task

# Usage
if __name__ == "__main__":
    task = select_next_task()
    if task:
        print(f"Now working on: {task.title}")
```

## Complete Example: Discovering and Creating Related Issues

```python
"""
Example: Discovering gaps during implementation and creating linked issues
"""
from beads import create_beads_client, IssueType, DependencyType

def discover_gap(current_issue_id: str, gap_title: str, gap_description: str):
    """Create a new issue for discovered work and link it."""
    client = create_beads_client()

    # Create new issue for the gap
    new_issue_id = client.create_issue(
        title=gap_title,
        issue_type=IssueType.TASK,
        priority=1,  # High priority since it's blocking current work
        description=gap_description
    )

    print(f"Created gap issue: {new_issue_id}")

    # Link new issue with discovered-from relationship
    client.add_dependency(
        blocked_id=current_issue_id,
        blocker_id=new_issue_id,
        dep_type=DependencyType.DISCOVERED_FROM
    )

    print(f"Linked {new_issue_id} as blocker of {current_issue_id}")

    return new_issue_id

# Usage
if __name__ == "__main__":
    gap_id = discover_gap(
        current_issue_id="codeframe-aco-2sd",
        gap_title="Design tool integration interface",
        gap_description="Need standard interface for external tools before cycle processor can use them"
    )
```

## Error Handling

```python
from beads import (
    BeadsError,
    BeadsIssueNotFoundError,
    BeadsDependencyCycleError,
    BeadsCommandError
)

try:
    # Try to get an issue
    issue = client.get_issue("nonexistent-id")

except BeadsIssueNotFoundError as e:
    print(f"Issue not found: {e.issue_id}")

except BeadsDependencyCycleError as e:
    print(f"Cycle detected: {' → '.join(e.cycle_path)}")

except BeadsCommandError as e:
    print(f"Command failed: {e.command}")
    print(f"Exit code: {e.returncode}")
    print(f"Error: {e.stderr}")

except BeadsError as e:
    print(f"Generic Beads error: {e}")
```

## Testing Usage

```python
# For testing, use sandbox mode to disable daemon and Git sync
import tempfile
import subprocess
from pathlib import Path

def test_with_isolated_database():
    """Create isolated test database for unit tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Initialize Beads in temp directory
        subprocess.run(
            ['bd', 'init', '--prefix', 'test'],
            cwd=tmp_path,
            check=True
        )

        # Create client with sandbox mode
        client = create_beads_client(
            db_path=str(tmp_path / '.beads'),
            sandbox=True
        )

        # Run tests against isolated database
        issue_id = client.create_issue(
            title="Test issue",
            issue_type=IssueType.TASK,
            priority=2
        )

        issue = client.get_issue(issue_id)
        assert issue.title == "Test issue"

        print("Test passed!")

# Usage
if __name__ == "__main__":
    test_with_isolated_database()
```

## Best Practices

### 1. Always Check for Ready Issues Before Assigning Work

```python
# GOOD: Check if issue is actually ready
ready_issues = client.get_ready_issues()
ready_ids = {issue.id for issue in ready_issues}

if "codeframe-aco-xon" in ready_ids:
    client.update_issue_status("codeframe-aco-xon", IssueStatus.IN_PROGRESS)
else:
    print("Issue has blockers, cannot start yet")

# BAD: Blindly updating status without checking dependencies
# client.update_issue_status("codeframe-aco-xon", IssueStatus.IN_PROGRESS)
```

### 2. Handle Cycles Before Adding Dependencies

```python
# GOOD: Check for cycles after adding dependency
try:
    client.add_dependency("issue-A", "issue-B")
    cycles = client.detect_dependency_cycles()
    if cycles:
        # Rollback or handle cycle
        client.remove_dependency("issue-A", "issue-B")
        raise ValueError("Dependency would create cycle!")
except BeadsDependencyCycleError as e:
    print(f"Cycle detected immediately: {e}")

# BAD: Adding dependencies without validation
# client.add_dependency("issue-A", "issue-B")
```

### 3. Use Enums for Type Safety

```python
# GOOD: Use enums
from beads import IssueStatus, IssueType

client.update_issue_status(issue_id, IssueStatus.IN_PROGRESS)
client.create_issue("Fix bug", IssueType.BUG, priority=0)

# BAD: Magic strings
# client.update_issue_status(issue_id, "in_progress")  # Typo-prone
# client.create_issue("Fix bug", "bug", priority=0)
```

### 4. Close Client Connections (Future Enhancement)

```python
# GOOD: Use context manager (when implemented)
# with create_beads_client() as client:
#     issues = client.get_ready_issues()

# For MVP, explicit cleanup not needed (CLI-based, no persistent connections)
client = create_beads_client()
issues = client.get_ready_issues()
# No cleanup required
```

## Troubleshooting

### Issue: "bd command not found"

**Solution**: Ensure Beads CLI is installed and in PATH:
```bash
which bd
# Should output: /path/to/bd

# If not found, install Beads or add to PATH
export PATH="$PATH:/home/user/go/bin"
```

### Issue: "No .beads directory found"

**Solution**: Initialize Beads in your project:
```bash
cd /path/to/project
bd init --prefix myproject
```

### Issue: JSON parse errors

**Solution**: Ensure you're using a recent version of Beads with `--json` support:
```bash
bd version
# Should be v0.9.0 or later
```

### Issue: Permission denied errors

**Solution**: Check file permissions on `.beads/` directory:
```bash
ls -la .beads/
chmod -R u+rw .beads/
```

## Next Steps

- Read the [full API contract](./contracts/beads_client_api.py) for detailed method documentation
- Review [data model documentation](./data-model.md) for entity details
- See [research notes](./research.md) for implementation decisions
- Check [plan.md](./plan.md) for project structure and architecture

## Support

For issues or questions:
1. Check Beads CLI documentation: `bd help <command>`
2. Review integration tests in `tests/integration/`
3. File issue in Beads: `bd create "Issue with Python interface"`
