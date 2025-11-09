#!/usr/bin/env python3
"""Example: Autonomous work selection from ready issues.

This example demonstrates how an autonomous agent would use BeadsClient
to select the next task to work on from the ready issues queue.

The agent:
1. Queries ready issues (no blocking dependencies)
2. Filters by priority and type
3. Selects the highest priority task
4. Updates status to in_progress
5. Begins work

Usage:
    python examples/select_task.py
"""

from beads import BeadsClient, IssueStatus, IssueType


def select_next_task(
    client: BeadsClient,
    preferred_types: list[IssueType] = None,
    max_priority: int = 4
) -> str:
    """Select the next task for an autonomous agent to work on.

    Args:
        client: BeadsClient instance
        preferred_types: List of issue types to prefer (None = any type)
        max_priority: Only consider issues with priority <= this value

    Returns:
        Issue ID of selected task, or None if no tasks available

    Strategy:
        1. Get all ready issues
        2. Filter by type preference (if specified)
        3. Filter by max priority
        4. Select highest priority (lowest number)
        5. Break ties by created_at (oldest first)
    """
    # Step 1: Get all ready issues
    print("Querying ready issues...")
    ready_issues = client.get_ready_issues()

    if not ready_issues:
        print("No ready issues found.")
        return None

    print(f"Found {len(ready_issues)} ready issues")

    # Step 2: Filter by type preference
    if preferred_types:
        type_names = [t.value for t in preferred_types]
        ready_issues = [
            issue for issue in ready_issues
            if issue.issue_type in preferred_types
        ]
        print(f"Filtered to {len(ready_issues)} issues of type {type_names}")

    # Step 3: Filter by max priority
    ready_issues = [
        issue for issue in ready_issues
        if issue.priority <= max_priority
    ]
    print(f"Filtered to {len(ready_issues)} issues with priority <= {max_priority}")

    if not ready_issues:
        print("No issues match filters.")
        return None

    # Step 4 & 5: Select highest priority, oldest first
    selected = min(
        ready_issues,
        key=lambda issue: (issue.priority, issue.created_at)
    )

    print(f"\nSelected issue: {selected.id}")
    print(f"  Title: {selected.title}")
    print(f"  Type: {selected.issue_type.value}")
    print(f"  Priority: {selected.priority}")
    print(f"  Status: {selected.status.value}")

    return selected.id


def claim_task(client: BeadsClient, issue_id: str) -> None:
    """Claim a task by updating its status to in_progress.

    Args:
        client: BeadsClient instance
        issue_id: ID of issue to claim
    """
    print(f"\nClaiming task {issue_id}...")

    # Update status to in_progress
    updated_issue = client.update_issue(
        issue_id,
        status=IssueStatus.IN_PROGRESS
    )

    print(f"Task claimed successfully!")
    print(f"  Status: {updated_issue.status.value}")
    print(f"  Updated at: {updated_issue.updated_at}")


def main():
    """Main example workflow."""
    print("=" * 60)
    print("Autonomous Work Selection Example")
    print("=" * 60)
    print()

    # Initialize client
    client = BeadsClient()

    # Example 1: Select any task
    print("Example 1: Select any ready task")
    print("-" * 60)
    task_id = select_next_task(client)

    if task_id:
        # Claim the task
        claim_task(client, task_id)
        print("\nAgent would now begin working on this task...")
    else:
        print("\nNo tasks available for work.")

    print()
    print("=" * 60)

    # Example 2: Select bug or feature with high priority
    print("\nExample 2: Select high-priority bug or feature")
    print("-" * 60)
    task_id = select_next_task(
        client,
        preferred_types=[IssueType.BUG, IssueType.FEATURE],
        max_priority=1  # P0 or P1 only
    )

    if task_id:
        print(f"\nFound high-priority task: {task_id}")
        print("(Not claiming to avoid duplicate work)")
    else:
        print("\nNo high-priority bugs or features available.")

    print()
    print("=" * 60)

    # Example 3: Show all ready issues
    print("\nExample 3: List all ready issues")
    print("-" * 60)
    ready = client.get_ready_issues()

    if ready:
        print(f"\n{len(ready)} ready issues:\n")
        for issue in sorted(ready, key=lambda i: (i.priority, i.created_at)):
            print(f"  [{issue.priority}] {issue.id}: {issue.title}")
            print(f"      Type: {issue.issue_type.value}, Status: {issue.status.value}")
    else:
        print("\nNo ready issues.")

    print()
    print("=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        raise
