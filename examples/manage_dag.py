#!/usr/bin/env python3
"""
Example: DAG Manipulation - Managing Dependencies

This script demonstrates how orchestrators can dynamically manage the DAG
structure by adding and removing dependencies between issues.

User Story 5 (US5): Manage Dependencies (P5)

This example shows:
1. Adding dependencies between issues (all 4 types)
2. Removing dependencies when they're no longer needed
3. Querying dependency trees to understand relationships
4. Detecting circular dependencies in the DAG
"""

from beads import create_beads_client, DependencyType, IssueType


def demonstrate_add_dependency():
    """
    Demonstrate adding dependencies between issues.

    Shows how to create relationships that control work order.
    """
    client = create_beads_client()

    print("=" * 70)
    print("Adding Dependencies Between Issues")
    print("=" * 70)

    # Create two test issues
    print("\n[1] Creating two test issues...")
    issue_a = client.create_issue(
        title="Implement authentication system",
        description="Build OAuth2 authentication",
        issue_type=IssueType.FEATURE,
        priority=1
    )

    issue_b = client.create_issue(
        title="Set up database schema",
        description="Create users and sessions tables",
        issue_type=IssueType.TASK,
        priority=0
    )

    print(f"  Created: {issue_a.id} - {issue_a.title}")
    print(f"  Created: {issue_b.id} - {issue_b.title}")

    # Add a blocking dependency
    print(f"\n[2] Adding dependency: {issue_a.id} is blocked by {issue_b.id}")
    print("    (Authentication needs database schema first)")

    dep = client.add_dependency(
        blocked_id=issue_a.id,
        blocker_id=issue_b.id,
        dep_type=DependencyType.BLOCKS
    )

    print(f"  ✓ Dependency added: {dep.dependency_type.value}")

    # Verify issue_a is no longer in ready list
    print(f"\n[3] Verifying {issue_a.id} is now blocked...")
    ready_issues = client.get_ready_issues()
    ready_ids = {issue.id for issue in ready_issues}

    if issue_a.id not in ready_ids:
        print(f"  ✓ {issue_a.id} is blocked (not in ready list)")
    else:
        print(f"  ✗ {issue_a.id} is still ready (unexpected)")

    if issue_b.id in ready_ids:
        print(f"  ✓ {issue_b.id} is ready (blocker can be worked on)")

    return issue_a.id, issue_b.id


def demonstrate_all_dependency_types():
    """
    Demonstrate all 4 dependency types.

    Shows how different relationship semantics work.
    """
    client = create_beads_client()

    print("\n" + "=" * 70)
    print("All 4 Dependency Types")
    print("=" * 70)

    # Create issues for demonstration
    issue_main = client.create_issue(
        title="Main feature",
        description="Primary feature implementation",
        issue_type=IssueType.FEATURE,
        priority=1
    )

    issue_blocker = client.create_issue(
        title="Prerequisite task",
        description="Must complete before main feature",
        issue_type=IssueType.TASK,
        priority=0
    )

    issue_related = client.create_issue(
        title="Related refactoring",
        description="Good to do around same time",
        issue_type=IssueType.CHORE,
        priority=2
    )

    issue_subtask = client.create_issue(
        title="Subtask of main feature",
        description="Part of main feature epic",
        issue_type=IssueType.TASK,
        priority=1
    )

    # 1. BLOCKS - Hard dependency
    print("\n1. BLOCKS (Hard dependency):")
    print(f"   {issue_main.id} is blocked by {issue_blocker.id}")
    client.add_dependency(
        blocked_id=issue_main.id,
        blocker_id=issue_blocker.id,
        dep_type=DependencyType.BLOCKS
    )
    print("   → Blocker must complete before blocked can close")

    # 2. RELATED - Soft association
    print("\n2. RELATED (Soft association):")
    print(f"   {issue_main.id} is related to {issue_related.id}")
    client.add_dependency(
        blocked_id=issue_main.id,
        blocker_id=issue_related.id,
        dep_type=DependencyType.RELATED
    )
    print("   → Informational link, no blocking")

    # 3. PARENT_CHILD - Hierarchical
    print("\n3. PARENT_CHILD (Hierarchical):")
    print(f"   {issue_subtask.id} is child of {issue_main.id}")
    client.add_dependency(
        blocked_id=issue_subtask.id,
        blocker_id=issue_main.id,
        dep_type=DependencyType.PARENT_CHILD
    )
    print("   → Epic/subtask relationship")

    # 4. DISCOVERED_FROM - Provenance
    print("\n4. DISCOVERED_FROM (Provenance):")
    discovered = client.create_issue(
        title="Gap discovered during implementation",
        description="Found while working on main feature",
        issue_type=IssueType.TASK,
        priority=1
    )
    print(f"   {discovered.id} was discovered from {issue_main.id}")
    client.add_dependency(
        blocked_id=discovered.id,
        blocker_id=issue_main.id,
        dep_type=DependencyType.DISCOVERED_FROM
    )
    print("   → Tracks where gaps were found")


def demonstrate_remove_dependency():
    """
    Demonstrate removing dependencies.

    Shows how dependencies can be removed when no longer needed.
    """
    client = create_beads_client()

    print("\n" + "=" * 70)
    print("Removing Dependencies")
    print("=" * 70)

    # Create and link issues
    issue_a = client.create_issue("Task A", "Description A", IssueType.TASK)
    issue_b = client.create_issue("Task B", "Description B", IssueType.TASK)

    # Add dependency
    print(f"\n[1] Adding dependency: {issue_a.id} → {issue_b.id}")
    client.add_dependency(issue_a.id, issue_b.id, DependencyType.BLOCKS)

    # Verify blocked
    ready = client.get_ready_issues()
    ready_ids = {i.id for i in ready}
    print(f"  {issue_a.id} is blocked: {issue_a.id not in ready_ids}")

    # Remove dependency
    print(f"\n[2] Removing dependency...")
    client.remove_dependency(issue_a.id, issue_b.id)

    # Verify unblocked
    ready_after = client.get_ready_issues()
    ready_ids_after = {i.id for i in ready_after}
    print(f"  {issue_a.id} is now ready: {issue_a.id in ready_ids_after}")

    # Idempotent: remove again (no error)
    print(f"\n[3] Removing same dependency again (idempotent)...")
    client.remove_dependency(issue_a.id, issue_b.id)
    print("  ✓ No error when removing non-existent dependency")


def demonstrate_dependency_tree():
    """
    Demonstrate querying dependency trees.

    Shows how to visualize the full dependency graph for an issue.
    """
    client = create_beads_client()

    print("\n" + "=" * 70)
    print("Querying Dependency Trees")
    print("=" * 70)

    # Create a chain of dependencies
    issue_root = client.create_issue("Root issue", "Main task", IssueType.FEATURE)
    issue_dep1 = client.create_issue("Dependency 1", "First blocker", IssueType.TASK)
    issue_dep2 = client.create_issue("Dependency 2", "Second blocker", IssueType.TASK)

    # Create chain: root blocked by dep1, dep1 blocked by dep2
    client.add_dependency(issue_root.id, issue_dep1.id, DependencyType.BLOCKS)
    client.add_dependency(issue_dep1.id, issue_dep2.id, DependencyType.BLOCKS)

    print(f"\n[1] Created dependency chain:")
    print(f"    {issue_root.id} ← {issue_dep1.id} ← {issue_dep2.id}")

    # Query tree for root issue
    print(f"\n[2] Dependency tree for {issue_root.id}:")
    tree = client.get_dependency_tree(issue_root.id)

    print(f"    Issue: {tree.issue_id}")
    print(f"    Blockers (upstream): {tree.blockers}")
    print(f"    Blocked by (downstream): {tree.blocked_by}")

    if len(tree.blockers) > 0:
        print(f"\n    ✓ Found {len(tree.blockers)} blocker(s)")
    else:
        print(f"\n    No blockers found")


def demonstrate_cycle_detection():
    """
    Demonstrate cycle detection.

    Shows how the system prevents circular dependencies.
    """
    client = create_beads_client()

    print("\n" + "=" * 70)
    print("Detecting Circular Dependencies")
    print("=" * 70)

    # Check for cycles (should be none initially)
    print("\n[1] Checking for cycles in DAG...")
    cycles = client.detect_dependency_cycles()

    if len(cycles) == 0:
        print("  ✓ No cycles detected (DAG is healthy)")
    else:
        print(f"  ✗ Found {len(cycles)} cycle(s):")
        for cycle in cycles:
            print(f"    Cycle: {' → '.join(cycle)}")

    # Try to create a cycle (bd will prevent it)
    print("\n[2] Attempting to create a cycle...")
    issue_x = client.create_issue("Issue X", "Test issue", IssueType.TASK)
    issue_y = client.create_issue("Issue Y", "Test issue", IssueType.TASK)

    # Add X → Y
    client.add_dependency(issue_x.id, issue_y.id, DependencyType.BLOCKS)
    print(f"  ✓ Added: {issue_x.id} → {issue_y.id}")

    # Try to add Y → X (creates cycle)
    print(f"  Attempting: {issue_y.id} → {issue_x.id} (would create cycle)")
    try:
        client.add_dependency(issue_y.id, issue_x.id, DependencyType.BLOCKS)
        print("  ✗ Cycle was allowed (unexpected)")
    except Exception as e:
        print(f"  ✓ Cycle prevented: {str(e)[:60]}...")


if __name__ == "__main__":
    import sys

    print("Beads Integration Layer - DAG Manipulation Example")
    print("=" * 70)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "add":
            demonstrate_add_dependency()
        elif command == "types":
            demonstrate_all_dependency_types()
        elif command == "remove":
            demonstrate_remove_dependency()
        elif command == "tree":
            demonstrate_dependency_tree()
        elif command == "cycles":
            demonstrate_cycle_detection()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: add, types, remove, tree, cycles")
            sys.exit(1)
    else:
        # Run all demonstrations
        demonstrate_add_dependency()
        demonstrate_all_dependency_types()
        demonstrate_remove_dependency()
        demonstrate_dependency_tree()
        demonstrate_cycle_detection()

        print("\n" + "=" * 70)
        print("All DAG Manipulation Demonstrations Complete!")
        print("=" * 70)
