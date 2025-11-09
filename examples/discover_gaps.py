#!/usr/bin/env python3
"""
Example: Discovering and Creating Related Issues

This script demonstrates how cycle processors can discover gaps during
implementation and autonomously create new issues linked to the current work.

User Story 4 (US4): Create New Issues (P4)

This example shows:
1. Discovering a gap while working on a current issue
2. Creating a new issue for the discovered work
3. Linking the new issue with a discovered-from dependency
4. Verifying the new issue appears in Beads
"""

from beads import create_beads_client, IssueType, DependencyType, IssueStatus


def discover_gap(current_issue_id: str, gap_title: str, gap_description: str):
    """
    Create a new issue for discovered work and link it.

    Args:
        current_issue_id: ID of the issue being worked on
        gap_title: Title for the new gap issue
        gap_description: Description of the gap discovered

    Returns:
        ID of the newly created gap issue

    Example:
        >>> gap_id = discover_gap(
        ...     current_issue_id="codeframe-aco-2sd",
        ...     gap_title="Design tool integration interface",
        ...     gap_description="Need standard interface before cycle processor can use it"
        ... )
        Created gap issue: codeframe-aco-xyz
        Linked codeframe-aco-xyz as blocker of codeframe-aco-2sd
    """
    client = create_beads_client()

    # Create new issue for the gap
    new_issue = client.create_issue(
        title=gap_title,
        issue_type=IssueType.TASK,
        priority=1,  # High priority since it's blocking current work
        description=gap_description
    )

    print(f"Created gap issue: {new_issue.id}")
    print(f"  Title: {new_issue.title}")
    print(f"  Type: {new_issue.issue_type.value}")
    print(f"  Priority: {new_issue.priority}")
    print(f"  Status: {new_issue.status.value}")

    # Note: Dependency management will be implemented in Phase 7 (US5)
    # For now, we'll document the intended relationship
    print(f"\nNote: In Phase 7, this issue would be linked with:")
    print(f"  blocked_id={current_issue_id}")
    print(f"  blocker_id={new_issue.id}")
    print(f"  dep_type={DependencyType.DISCOVERED_FROM.value}")

    return new_issue.id


def simulate_gap_discovery_workflow():
    """
    Simulate a cycle processor discovering gaps during implementation.

    This demonstrates the workflow:
    1. Processor starts working on an issue
    2. Discovers a gap (missing prerequisite)
    3. Creates a new issue for the gap
    4. Links the gap to the current issue
    5. Continues with other work
    """
    client = create_beads_client()

    print("=" * 70)
    print("Simulating Cycle Processor Gap Discovery Workflow")
    print("=" * 70)

    # Step 1: Select and start work on an issue
    print("\n[1] Selecting next ready issue...")
    ready_issues = client.get_ready_issues(limit=1)

    if not ready_issues:
        print("No ready issues available. Creating a test issue...")
        current_issue = client.create_issue(
            title="Implement state machine orchestrator",
            description="Build orchestrator to process issues through dev cycle",
            issue_type=IssueType.FEATURE,
            priority=0
        )
        print(f"Created test issue: {current_issue.id}")
    else:
        current_issue = ready_issues[0]
        print(f"Selected issue: {current_issue.id}")

    print(f"  Title: {current_issue.title}")
    print(f"  Status: {current_issue.status.value}")

    # Step 2: Start work by updating status
    print(f"\n[2] Starting work on {current_issue.id}...")
    client.update_issue_status(current_issue.id, IssueStatus.IN_PROGRESS)
    print(f"  Status updated: {IssueStatus.IN_PROGRESS.value}")

    # Step 3: Discover gaps during implementation
    print(f"\n[3] Discovering gaps while implementing {current_issue.id}...")

    gaps = [
        {
            "title": "Design tool integration interface",
            "description": "Need standard interface for external tools before cycle processor can use them"
        },
        {
            "title": "Implement vector memory query layer",
            "description": "Need efficient vector queries to retrieve context for orchestration"
        },
        {
            "title": "Add error recovery mechanism",
            "description": "Need rollback capability when issues fail mid-cycle"
        }
    ]

    created_gaps = []
    for gap in gaps:
        print(f"\n  Discovered gap: {gap['title']}")
        gap_id = discover_gap(
            current_issue_id=current_issue.id,
            gap_title=gap['title'],
            gap_description=gap['description']
        )
        created_gaps.append(gap_id)

    # Step 4: Verify all gaps were created
    print(f"\n[4] Verifying {len(created_gaps)} gap issues were created...")
    for gap_id in created_gaps:
        gap_issue = client.get_issue(gap_id)
        print(f"  ✓ {gap_id}: {gap_issue.title}")

    # Step 5: List all open issues to show the expanded DAG
    print(f"\n[5] Listing all open issues (original + discovered gaps)...")
    all_open = client.list_issues(status=IssueStatus.OPEN)
    print(f"  Total open issues: {len(all_open)}")
    for issue in all_open:
        marker = "📍" if issue.id == current_issue.id else "  "
        print(f"  {marker} {issue.id}: {issue.title} (P{issue.priority})")

    print("\n" + "=" * 70)
    print("Gap Discovery Workflow Complete!")
    print("=" * 70)
    print(f"\nSummary:")
    print(f"  Original issue: {current_issue.id}")
    print(f"  Gaps discovered: {len(created_gaps)}")
    print(f"  New issues created: {created_gaps}")
    print(f"\nNext steps:")
    print(f"  1. In Phase 7, add dependencies linking gaps to {current_issue.id}")
    print(f"  2. Update {current_issue.id} status to 'blocked' until gaps resolved")
    print(f"  3. Work on gap issues (now in ready list)")
    print(f"  4. Once gaps closed, {current_issue.id} becomes ready again")


def demonstrate_gap_priority_handling():
    """
    Demonstrate how gap priority affects work selection.

    Shows that:
    - Critical gaps (P0) get worked on before the original issue
    - Lower priority gaps (P2-P4) may be deferred
    - The orchestrator can dynamically adjust based on gap severity
    """
    client = create_beads_client()

    print("\n" + "=" * 70)
    print("Demonstrating Gap Priority Handling")
    print("=" * 70)

    # Create a medium-priority parent issue
    parent = client.create_issue(
        title="Add user authentication",
        description="Implement OAuth2 authentication flow",
        issue_type=IssueType.FEATURE,
        priority=2
    )
    print(f"\nCreated parent issue: {parent.id} (P{parent.priority})")

    # Discover critical gap - should be worked on immediately
    critical_gap = client.create_issue(
        title="Fix security vulnerability in auth library",
        description="CVE-2024-XXXX requires immediate patch",
        issue_type=IssueType.BUG,
        priority=0  # Critical
    )
    print(f"Discovered CRITICAL gap: {critical_gap.id} (P{critical_gap.priority})")

    # Discover nice-to-have gap - can be deferred
    optional_gap = client.create_issue(
        title="Add auth metrics dashboard",
        description="Nice-to-have monitoring for auth events",
        issue_type=IssueType.FEATURE,
        priority=4  # Backlog
    )
    print(f"Discovered optional gap: {optional_gap.id} (P{optional_gap.priority})")

    # Query ready issues to see work order
    print("\nRecommended work order (by priority):")
    ready = client.get_ready_issues()
    sorted_by_priority = sorted(ready, key=lambda i: i.priority)

    for idx, issue in enumerate(sorted_by_priority[:5], 1):
        print(f"  {idx}. P{issue.priority} - {issue.id}: {issue.title}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    import sys

    print("Beads Integration Layer - Gap Discovery Example")
    print("=" * 70)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "discover":
            # Discover a single gap
            if len(sys.argv) < 4:
                print("Usage: python discover_gaps.py discover <current_issue_id> <gap_title> [gap_description]")
                sys.exit(1)

            current_id = sys.argv[2]
            gap_title = sys.argv[3]
            gap_desc = sys.argv[4] if len(sys.argv) > 4 else ""

            gap_id = discover_gap(current_id, gap_title, gap_desc)
            print(f"\nSuccess! Created gap issue: {gap_id}")

        elif command == "simulate":
            # Simulate full workflow
            simulate_gap_discovery_workflow()

        elif command == "priority":
            # Demonstrate priority handling
            demonstrate_gap_priority_handling()

        else:
            print(f"Unknown command: {command}")
            print("Available commands: discover, simulate, priority")
            sys.exit(1)
    else:
        # Run default simulation
        simulate_gap_discovery_workflow()
        print("\n")
        demonstrate_gap_priority_handling()
