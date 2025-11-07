"""Shared test fixtures and configuration for Vector Memory and Beads tests."""

import subprocess
import pytest
from pathlib import Path
from typing import Generator

# =============================================================================
# Vector Memory Test Fixtures
# =============================================================================

# Generate 1000 mock Beads issue IDs for testing
# Format: test-issue-{letter}{letter}{digit}
# Examples: test-issue-aa0, test-issue-ab1, ..., test-issue-zz9
MOCK_BEADS_IDS = []
for i in range(1000):
    first_letter = chr(97 + (i // 260))  # a-z (loops after z)
    second_letter = chr(97 + ((i // 10) % 26))  # a-z
    digit = i % 10  # 0-9
    MOCK_BEADS_IDS.append(f"test-issue-{first_letter}{second_letter}{digit}")


def mock_issue_id_factory(index: int) -> str:
    """
    Get mock Beads issue ID by index (non-fixture version for use in hypothesis tests).

    Args:
        index: Index into MOCK_BEADS_IDS (0-999)

    Returns:
        Mock Beads issue ID string
    """
    if 0 <= index < len(MOCK_BEADS_IDS):
        return MOCK_BEADS_IDS[index]
    raise ValueError(f"Index {index} out of range [0, {len(MOCK_BEADS_IDS)-1}]")


@pytest.fixture
def mock_issue_id():
    """
    Get mock Beads issue ID for tests.

    Usage:
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)

    Returns:
        Function that takes an index and returns a mock issue ID
    """
    return mock_issue_id_factory


@pytest.fixture
def mock_dag_order():
    """
    Get mock DAG ordering for partial order tests.

    Maps issue IDs to topological sort positions (0-999).

    Returns:
        Dictionary mapping issue_id → position
    """
    return {issue_id: i for i, issue_id in enumerate(MOCK_BEADS_IDS)}


@pytest.fixture
def mock_issue_batch():
    """
    Get a batch of mock issue IDs.

    Usage:
        issue_ids = mock_issue_batch(10, 20)  # Get IDs 10-19

    Returns:
        Function that takes (start, end) and returns list of issue IDs
    """
    def _get_batch(start: int, end: int) -> list[str]:
        if not (0 <= start < end <= len(MOCK_BEADS_IDS)):
            raise ValueError(f"Invalid range [{start}, {end})")
        return MOCK_BEADS_IDS[start:end]
    return _get_batch


# =============================================================================
# Beads Integration Test Fixtures
# =============================================================================

# T029: Fixture for isolated .beads/ database
@pytest.fixture
def test_beads_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Create an isolated Beads database for testing.

    This fixture:
    - Creates a temporary directory
    - Initializes a new Beads database in that directory
    - Yields the path to the test directory
    - Cleanup is automatic via tmp_path fixture

    Args:
        tmp_path: pytest's built-in temporary directory fixture

    Yields:
        Path to the temporary directory containing .beads/

    Example:
        def test_something(test_beads_db):
            # test_beads_db points to a directory with a fresh .beads/ database
            pass
    """
    # Initialize Beads in the temporary directory
    result = subprocess.run(
        ['bd', 'init', '--prefix', 'test'],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode != 0:
        pytest.skip(f"bd init failed: {result.stderr}")

    # Verify .beads/ directory was created
    beads_dir = tmp_path / '.beads'
    if not beads_dir.exists():
        pytest.skip(".beads/ directory was not created by bd init")

    yield tmp_path

    # Cleanup is automatic via tmp_path fixture


# T030: Fixture for BeadsClient with sandbox mode
@pytest.fixture
def beads_client(test_beads_db: Path):
    """Create a BeadsClient pointing to an isolated test database.

    This fixture depends on test_beads_db and creates a BeadsClient
    instance configured to use the test database.

    Args:
        test_beads_db: Path to test directory with .beads/ database

    Returns:
        BeadsClient instance configured for testing

    Example:
        def test_get_ready_issues(beads_client):
            issues = beads_client.get_ready_issues()
            assert isinstance(issues, list)
    """
    # Import here to avoid circular dependencies during test collection
    from beads.client import create_beads_client

    # Create client pointing to test database
    client = create_beads_client(
        db_path=str(test_beads_db / '.beads'),
        timeout=10,  # Shorter timeout for tests
        sandbox=True  # Disable daemon and Git sync for tests
    )

    return client


# T031: Fixture for test issues with various states
@pytest.fixture
def test_issues(test_beads_db: Path) -> dict:
    """Create test issues in various states for testing.

    This fixture creates a set of issues with different statuses,
    priorities, and types that can be used for testing various scenarios.

    Args:
        test_beads_db: Path to test directory with .beads/ database

    Returns:
        Dict mapping descriptive names to issue IDs

    Example:
        def test_filtering(test_issues):
            # test_issues = {'open_p0': 'test-abc', 'in_progress_p1': 'test-def', ...}
            pass
    """
    issues = {}

    # Issue 1: Open, P0, bug (high priority ready issue)
    result = subprocess.run(
        ['bd', 'create', 'Test bug - high priority', '--type', 'bug', '--priority', '0'],
        cwd=test_beads_db,
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode == 0:
        # Extract issue ID from output (format: "Created issue: test-abc")
        output = result.stdout.strip()
        if "Created issue:" in output:
            issue_id = output.split("Created issue:")[-1].strip()
            issues['open_p0_bug'] = issue_id

    # Issue 2: Open, P2, feature (medium priority ready issue)
    result = subprocess.run(
        ['bd', 'create', 'Test feature - medium priority', '--type', 'feature', '--priority', '2'],
        cwd=test_beads_db,
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode == 0:
        output = result.stdout.strip()
        if "Created issue:" in output:
            issue_id = output.split("Created issue:")[-1].strip()
            issues['open_p2_feature'] = issue_id

    # Issue 3: Open, P3, task (low priority ready issue)
    result = subprocess.run(
        ['bd', 'create', 'Test task - low priority', '--type', 'task', '--priority', '3'],
        cwd=test_beads_db,
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode == 0:
        output = result.stdout.strip()
        if "Created issue:" in output:
            # Parse issue ID more carefully (just the ID, not the whole output)
            lines = output.split('\n')
            for line in lines:
                if "Created issue:" in line:
                    issue_id = line.split("Created issue:")[-1].strip().split()[0]
                    issues['open_p3_task'] = issue_id
                    break

    return issues
