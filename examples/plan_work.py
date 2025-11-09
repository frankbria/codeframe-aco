#!/usr/bin/env python3
"""
Example: Context-Aware Work Planning

This example demonstrates how to use the Beads Integration Layer to retrieve
full issue context for intelligent work planning and prioritization.

User Story 3 (US3): Enable orchestrators to retrieve full issue context for
smart planning decisions.
"""

from beads import create_beads_client, IssueStatus, IssueType
from datetime import datetime


def analyze_work_queue():
    """Analyze the work queue and provide planning recommendations."""
    client = create_beads_client()

    print("=" * 70)
    print("Example: Context-Aware Work Planning")
    print("=" * 70)
    print()

    # Step 1: Get all ready work
    print("Step 1: Analyzing ready work...")
    ready_issues = client.get_ready_issues()

    print(f"✓ Found {len(ready_issues)} ready issues")
    print()

    # Step 2: Categorize by priority
    print("Step 2: Categorizing by priority...")
    by_priority = {}
    for issue in ready_issues:
        if issue.priority not in by_priority:
            by_priority[issue.priority] = []
        by_priority[issue.priority].append(issue)

    for priority in sorted(by_priority.keys()):
        count = len(by_priority[priority])
        priority_names = ["Critical (P0)", "High (P1)", "Medium (P2)", "Low (P3)", "Backlog (P4)"]
        print(f"  {priority_names[priority]}: {count} issues")

    print()

    # Step 3: Recommend next work
    print("Step 3: Recommending next work...")
    if not ready_issues:
        print("  No ready work available!")
    else:
        # Get highest priority issue
        next_task = min(ready_issues, key=lambda i: i.priority)
        print(f"  RECOMMENDED: {next_task.id}")
        print(f"    Title: {next_task.title}")
        print(f"    Priority: P{next_task.priority}")
        print(f"    Type: {next_task.issue_type.value}")
        print(f"    Status: {next_task.status.value}")

    print()
    print("=" * 70)


def filter_work_by_type():
    """Demonstrate filtering work by type for specialized agents."""
    client = create_beads_client()

    print()
    print("=" * 70)
    print("Example: Filtering Work by Type for Specialized Agents")
    print("=" * 70)
    print()

    # Get bugs for bug-fixing agent
    print("Bug-Fixing Agent - Available bugs:")
    bugs = client.list_issues(
        status=IssueStatus.OPEN,
        issue_type=IssueType.BUG
    )

    if bugs:
        for bug in bugs[:5]:  # Show first 5
            print(f"  • {bug.id}: {bug.title} (P{bug.priority})")
    else:
        print("  No bugs available")

    print()

    # Get features for feature-development agent
    print("Feature Development Agent - Available features:")
    features = client.list_issues(
        status=IssueStatus.OPEN,
        issue_type=IssueType.FEATURE
    )

    if features:
        for feature in features[:5]:  # Show first 5
            print(f"  • {feature.id}: {feature.title} (P{feature.priority})")
    else:
        print("  No features available")

    print()
    print("=" * 70)


def analyze_team_workload():
    """Analyze workload distribution across team members."""
    client = create_beads_client()

    print()
    print("=" * 70)
    print("Example: Team Workload Analysis")
    print("=" * 70)
    print()

    # Get all open and in-progress issues
    active_issues = []
    active_issues.extend(client.list_issues(status=IssueStatus.OPEN))
    active_issues.extend(client.list_issues(status=IssueStatus.IN_PROGRESS))

    # Group by assignee
    by_assignee = {}
    unassigned = []

    for issue in active_issues:
        if issue.assignee:
            if issue.assignee not in by_assignee:
                by_assignee[issue.assignee] = []
            by_assignee[issue.assignee].append(issue)
        else:
            unassigned.append(issue)

    # Print workload summary
    print("Team Workload Distribution:")
    print()

    for assignee in sorted(by_assignee.keys()):
        issues = by_assignee[assignee]
        in_progress = sum(1 for i in issues if i.status == IssueStatus.IN_PROGRESS)
        open_count = sum(1 for i in issues if i.status == IssueStatus.OPEN)

        print(f"  {assignee}:")
        print(f"    Total: {len(issues)} issues")
        print(f"    In Progress: {in_progress}")
        print(f"    Queued: {open_count}")

    if unassigned:
        print(f"\n  Unassigned: {len(unassigned)} issues")
        print("    Top priority unassigned:")
        sorted_unassigned = sorted(unassigned, key=lambda i: i.priority)
        for issue in sorted_unassigned[:3]:
            print(f"      • {issue.id}: {issue.title} (P{issue.priority})")

    print()
    print("=" * 70)


def get_issue_details_for_planning():
    """Retrieve complete issue details for planning decisions."""
    client = create_beads_client()

    print()
    print("=" * 70)
    print("Example: Retrieve Complete Issue Context")
    print("=" * 70)
    print()

    # Get ready issues
    ready = client.get_ready_issues(limit=1)

    if not ready:
        print("No ready issues available")
        return

    issue_id = ready[0].id

    # Get full details
    print(f"Retrieving full context for: {issue_id}")
    issue = client.get_issue(issue_id)

    print()
    print("Complete Issue Context:")
    print(f"  ID: {issue.id}")
    print(f"  Title: {issue.title}")
    print(f"  Description: {issue.description[:100]}..." if len(issue.description) > 100 else f"  Description: {issue.description}")
    print(f"  Status: {issue.status.value}")
    print(f"  Priority: P{issue.priority}")
    print(f"  Type: {issue.issue_type.value}")
    print(f"  Assignee: {issue.assignee or 'Unassigned'}")
    print(f"  Created: {issue.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Updated: {issue.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Labels: {', '.join(issue.labels) if issue.labels else 'None'}")

    print()
    print("Planning Decision:")

    # Make planning decision based on context
    if issue.priority == 0:
        print("  ⚠️  CRITICAL PRIORITY - Start immediately!")
    elif issue.priority == 1:
        print("  ⬆️  HIGH PRIORITY - Schedule soon")
    else:
        print("  ℹ️  Normal priority - Add to queue")

    if issue.assignee:
        print(f"  👤 Assigned to: {issue.assignee}")
    else:
        print("  👥 Available for claim by any agent")

    print()
    print("=" * 70)


def query_recent_work():
    """Query and analyze recently created or updated work."""
    client = create_beads_client()

    print()
    print("=" * 70)
    print("Example: Recent Work Analysis")
    print("=" * 70)
    print()

    # Get all issues (in real scenario, you might filter by date)
    all_issues = client.list_issues()

    if not all_issues:
        print("No issues found")
        return

    # Sort by updated_at (most recent first)
    recent_issues = sorted(all_issues, key=lambda i: i.updated_at, reverse=True)[:10]

    print("10 Most Recently Updated Issues:")
    print()

    for issue in recent_issues:
        age = datetime.now(issue.updated_at.tzinfo) - issue.updated_at
        age_str = f"{age.days}d ago" if age.days > 0 else f"{age.seconds // 3600}h ago"

        print(f"  • {issue.id}: {issue.title}")
        print(f"    Status: {issue.status.value} | Priority: P{issue.priority} | Updated: {age_str}")

    print()
    print("=" * 70)


def main():
    """Run all planning examples."""
    try:
        # Example 1: Analyze work queue
        analyze_work_queue()

        # Example 2: Filter by type
        filter_work_by_type()

        # Example 3: Team workload
        analyze_team_workload()

        # Example 4: Issue details
        get_issue_details_for_planning()

        # Example 5: Recent work
        query_recent_work()

        print()
        print("✓ All planning examples completed successfully!")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
