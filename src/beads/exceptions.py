"""Custom exception classes for Beads Integration Layer.

This module provides a hierarchy of exceptions for handling various
error scenarios when interacting with the Beads CLI.
"""

from typing import List, Optional


# T016: Base exception
class BeadsError(Exception):
    """Base exception for all Beads operations.

    All custom Beads exceptions inherit from this class, allowing
    users to catch all Beads-related errors with a single except clause.
    """

    pass


# T017: CLI command errors
class BeadsCommandError(BeadsError):
    """CLI command failed with non-zero exit code.

    Attributes:
        message: Human-readable error description
        command: The bd command that failed (list of args)
        returncode: Exit code from the failed command
        stderr: Standard error output from the command
    """

    def __init__(
        self,
        message: str,
        command: Optional[List[str]] = None,
        returncode: Optional[int] = None,
        stderr: Optional[str] = None,
    ):
        super().__init__(message)
        self.command = command or []
        self.returncode = returncode
        self.stderr = stderr or ""

    def __str__(self) -> str:
        """Format error message with command context."""
        parts = [super().__str__()]
        if self.command:
            parts.append(f"Command: {' '.join(self.command)}")
        if self.returncode is not None:
            parts.append(f"Exit code: {self.returncode}")
        if self.stderr:
            parts.append(f"Error output: {self.stderr}")
        return " | ".join(parts)


# T018: JSON parsing errors
class BeadsJSONParseError(BeadsError):
    """Failed to parse JSON output from bd command.

    Attributes:
        message: Human-readable error description
        json_content: The raw JSON content that failed to parse
        original_error: The original parsing error message
    """

    def __init__(
        self,
        message: str,
        json_content: Optional[str] = None,
        original_error: Optional[str] = None,
    ):
        super().__init__(message)
        self.json_content = json_content or ""
        self.original_error = original_error or ""

    def __str__(self) -> str:
        """Format error message with JSON context."""
        parts = [super().__str__()]
        if self.original_error:
            parts.append(f"Parse error: {self.original_error}")
        if self.json_content:
            # Truncate long JSON content for readability
            content_preview = (
                self.json_content[:100] + "..."
                if len(self.json_content) > 100
                else self.json_content
            )
            parts.append(f"Content: {content_preview}")
        return " | ".join(parts)


# T019: Issue not found errors
class BeadsIssueNotFoundError(BeadsError):
    """Issue ID does not exist in the Beads database.

    Attributes:
        issue_id: The issue ID that was not found
    """

    def __init__(self, issue_id: str):
        self.issue_id = issue_id
        super().__init__(f"Issue not found: {issue_id}")


# T020: Dependency cycle errors
class BeadsDependencyCycleError(BeadsError):
    """Circular dependency detected in the DAG.

    Attributes:
        cycle_path: List of issue IDs forming the cycle (first == last)
    """

    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
        cycle_str = " → ".join(cycle_path)
        super().__init__(f"Circular dependency detected: {cycle_str}")
