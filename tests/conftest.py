"""Shared test fixtures and configuration."""

import pytest

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
