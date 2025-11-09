#!/usr/bin/env python3
"""
Example: Track Work Progress Through Development Cycle

This example demonstrates how to use the Beads Integration Layer to track
the progress of issues through the development lifecycle by updating their
status and priority.

User Story 2 (US2): Enable cycle processors to track work progress through
status updates (open → in_progress → closed).
"""

from beads import create_beads_client, IssueStatus, IssueType


def track_issue_progress():
    """Demonstrate tracking an issue through its complete lifecycle."""
    # Create client
    client = create_beads_client()

    print("=" * 70)
    print("Example: Tracking Issue Progress Through Development Cycle")
    print("=" * 70)
    print()

    # Step 1: Create a new issue
    print("Step 1: Creating a new issue...")
    issue = client.create_issue(
        title="Implement user authentication",
        description="Add OAuth2-based authentication for users",
        issue_type=IssueType.FEATURE,
        priority=0  # Critical priority
    )

    print(f"✓ Created issue: {issue.id}")
    print(f"  Title: {issue.title}")
    print(f"  Status: {issue.status.value}")
    print(f"  Priority: P{issue.priority}")
    print()

    # Step 2: Start work on the issue
    print("Step 2: Starting work on the issue...")
    issue = client.update_issue_status(issue.id, IssueStatus.IN_PROGRESS)

    print(f"✓ Updated status to: {issue.status.value}")
    print()

    # Step 3: Adjust priority (discovered it's blocking other work)
    print("Step 3: Elevating priority (blocking other work)...")
    issue = client.update_issue_priority(issue.id, 0)

    print(f"✓ Updated priority to: P{issue.priority}")
    print()

    # Step 4: Complete the issue
    print("Step 4: Completing the issue...")
    issue = client.close_issue(issue.id)

    print(f"✓ Closed issue: {issue.id}")
    print(f"  Final status: {issue.status.value}")
    print()

    # Step 5: Verify the issue is no longer in ready queue
    print("Step 5: Verifying issue is no longer in ready queue...")
    ready_issues = client.get_ready_issues()
    ready_ids = {i.id for i in ready_issues}

    if issue.id not in ready_ids:
        print(f"✓ Issue {issue.id} is no longer in ready queue (as expected)")
    else:
        print(f"✗ WARNING: Closed issue still appears in ready queue")

    print()
    print("=" * 70)
    print("Issue lifecycle tracking complete!")
    print("=" * 70)


def track_multiple_issues():
    """Demonstrate tracking multiple issues simultaneously."""
    client = create_beads_client()

    print()
    print("=" * 70)
    print("Example: Tracking Multiple Issues Simultaneously")
    print("=" * 70)
    print()

    # Create multiple issues
    print("Creating 3 issues...")
    issue_ids = []

    for i in range(3):
        issue = client.create_issue(
            title=f"Task {i+1}: Implement feature component",
            description=f"Component {i+1} implementation",
            issue_type=IssueType.TASK,
            priority=2
        )
        issue_ids.append(issue.id)
        print(f"✓ Created: {issue.id} - {issue.title}")

    print()

    # Start work on all issues
    print("Starting work on all issues...")
    for issue_id in issue_ids:
        client.update_issue_status(issue_id, IssueStatus.IN_PROGRESS)
        print(f"✓ Started: {issue_id}")

    print()

    # Complete issues one by one
    print("Completing issues...")
    for i, issue_id in enumerate(issue_ids):
        client.close_issue(issue_id)
        print(f"✓ Completed: {issue_id} ({i+1}/{len(issue_ids)} done)")

    print()
    print("All issues completed!")
    print("=" * 70)


def demonstrate_priority_adjustments():
    """Demonstrate adjusting priorities based on changing requirements."""
    client = create_beads_client()

    print()
    print("=" * 70)
    print("Example: Dynamic Priority Adjustment")
    print("=" * 70)
    print()

    # Create an issue
    print("Creating issue with medium priority (P2)...")
    issue = client.create_issue(
        title="Optimize database queries",
        description="Improve query performance for dashboard",
        issue_type=IssueType.TASK,
        priority=2  # Medium priority initially
    )

    print(f"✓ Created: {issue.id} at P{issue.priority}")
    print()

    # Discover it's causing production issues
    print("ALERT: Production slowdown detected!")
    print("Escalating priority to P0 (critical)...")

    issue = client.update_issue_priority(issue.id, 0)
    print(f"✓ Escalated to: P{issue.priority}")
    print()

    # Start work immediately
    print("Starting emergency work...")
    issue = client.update_issue_status(issue.id, IssueStatus.IN_PROGRESS)
    print(f"✓ Status updated to: {issue.status.value}")
    print()

    # Complete the fix
    print("Deploying fix...")
    issue = client.close_issue(issue.id)
    print(f"✓ Issue resolved: {issue.id}")
    print()

    print("=" * 70)
    print("Priority escalation workflow complete!")
    print("=" * 70)


def main():
    """Run all examples."""
    try:
        # Example 1: Single issue lifecycle
        track_issue_progress()

        # Example 2: Multiple issues
        track_multiple_issues()

        # Example 3: Priority adjustments
        demonstrate_priority_adjustments()

        print()
        print("✓ All examples completed successfully!")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
