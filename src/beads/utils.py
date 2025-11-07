"""Utility functions for Beads Integration Layer.

This module provides helper functions for executing bd CLI commands,
parsing JSON output, and handling errors.
"""

import json
import logging
import subprocess
import time
from typing import Any, Dict, List, Optional

from beads.exceptions import BeadsCommandError, BeadsJSONParseError

# Configure logging
logger = logging.getLogger(__name__)


# T025: Implement _run_bd_command with subprocess execution
def _run_bd_command(
    args: List[str],
    timeout: int = 30,
    **kwargs: Any
) -> Dict[str, Any]:
    """Execute bd command with JSON output and error handling.

    Args:
        args: Command arguments (excluding 'bd' and '--json')
        timeout: Timeout in seconds (default: 30)
        **kwargs: Additional arguments passed to subprocess.run()

    Returns:
        Dict containing parsed JSON output from bd command

    Raises:
        BeadsCommandError: If command fails (non-zero exit code)
        BeadsJSONParseError: If JSON parsing fails

    Example:
        >>> result = _run_bd_command(['list', '--status', 'open'])
        >>> issues = result  # List of issue dicts
    """
    # Build full command with JSON flag
    cmd = ['bd', '--json'] + args

    # Track execution time for performance monitoring (T027)
    start_time = time.perf_counter()

    try:
        # Execute command with timeout and output capture
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,  # Handle errors explicitly
            **kwargs
        )

        # Log execution time
        duration = time.perf_counter() - start_time
        logger.debug(f"bd {' '.join(args)} took {duration*1000:.1f}ms")

        # Check for command failure
        if result.returncode != 0:
            raise BeadsCommandError(
                message=f"bd command failed: {' '.join(args)}",
                command=cmd,
                returncode=result.returncode,
                stderr=result.stderr.strip()
            )

        # Handle empty output (some commands don't return JSON)
        if not result.stdout or result.stdout.strip() == "":
            return {}

        # Parse JSON output (T026)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise BeadsJSONParseError(
                message="Failed to parse JSON output from bd command",
                json_content=result.stdout,
                original_error=str(e)
            )

    except subprocess.TimeoutExpired as e:
        raise BeadsCommandError(
            message=f"bd command timed out after {timeout}s",
            command=cmd,
            returncode=-1,
            stderr=f"Timeout after {timeout} seconds"
        )


# T026: JSON parsing utilities with error handling

def parse_issue_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and validate issue JSON data.

    Args:
        data: Raw JSON dict from bd command

    Returns:
        Validated issue dict

    Raises:
        KeyError: If required fields are missing
        ValueError: If field values are invalid
    """
    # Validate required fields
    required_fields = [
        "id", "title", "description", "status", "priority",
        "issue_type", "created_at", "updated_at", "content_hash", "source_repo"
    ]

    for field in required_fields:
        if field not in data:
            raise KeyError(f"Missing required field: {field}")

    # Validate priority range
    if not (0 <= data["priority"] <= 4):
        raise ValueError(f"Invalid priority: {data['priority']} (must be 0-4)")

    return data


def parse_issues_list_json(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse and validate list of issues JSON data.

    Args:
        data: Raw JSON list from bd command

    Returns:
        List of validated issue dicts

    Raises:
        KeyError: If required fields are missing in any issue
        ValueError: If field values are invalid in any issue
    """
    return [parse_issue_json(issue) for issue in data]


def parse_dependency_tree_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and validate dependency tree JSON data.

    Args:
        data: Raw JSON dict from bd dep tree command

    Returns:
        Validated dependency tree dict with keys: issue_id, blockers, blocked_by

    Raises:
        KeyError: If required fields are missing
    """
    required_fields = ["issue_id", "blockers", "blocked_by"]

    for field in required_fields:
        if field not in data:
            raise KeyError(f"Missing required field in dependency tree: {field}")

    return data


def parse_cycles_json(data: Dict[str, Any]) -> List[List[str]]:
    """Parse and validate cycles JSON data.

    Args:
        data: Raw JSON dict from bd dep cycles command

    Returns:
        List of cycle paths, where each cycle is a list of issue IDs

    Raises:
        KeyError: If 'cycles' field is missing
    """
    if "cycles" not in data:
        raise KeyError("Missing 'cycles' field in JSON data")

    return data["cycles"]
