"""Unit tests for utility functions (_run_bd_command, JSON parsing)."""

import json
import subprocess
from unittest.mock import Mock, patch
import pytest


# Tests for T023: _run_bd_command helper
class TestRunBdCommand:
    """Test _run_bd_command subprocess helper with mocking."""

    @patch("subprocess.run")
    def test_run_bd_command_success(self, mock_run):
        """Test successful bd command execution returns parsed JSON."""
        from beads.utils import _run_bd_command

        # Mock successful subprocess result
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"result": "success"}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = _run_bd_command(["list"])

        assert result == {"result": "success"}
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["bd", "--json", "list"]

    @patch("subprocess.run")
    def test_run_bd_command_with_multiple_args(self, mock_run):
        """Test that command args are passed correctly."""
        from beads.utils import _run_bd_command

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"id": "test-123"}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        _run_bd_command(["create", "Test issue", "--priority", "1"])

        call_args = mock_run.call_args
        assert call_args[0][0] == ["bd", "--json", "create", "Test issue", "--priority", "1"]

    @patch("subprocess.run")
    def test_run_bd_command_with_empty_output(self, mock_run):
        """Test that empty stdout returns empty dict."""
        from beads.utils import _run_bd_command

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = _run_bd_command(["list"])

        assert result == {}

    @patch("subprocess.run")
    def test_run_bd_command_failure_raises_command_error(self, mock_run):
        """Test that non-zero exit code raises BeadsCommandError."""
        from beads.utils import _run_bd_command
        from beads.exceptions import BeadsCommandError

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: issue not found"
        mock_run.return_value = mock_result

        with pytest.raises(BeadsCommandError) as exc_info:
            _run_bd_command(["show", "invalid-id"])

        error = exc_info.value
        assert error.returncode == 1
        assert "Error: issue not found" in error.stderr
        assert ["bd", "--json", "show", "invalid-id"] == error.command

    @patch("subprocess.run")
    def test_run_bd_command_malformed_json_raises_parse_error(self, mock_run):
        """Test that invalid JSON raises BeadsJSONParseError."""
        from beads.utils import _run_bd_command
        from beads.exceptions import BeadsJSONParseError

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{invalid: json}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with pytest.raises(BeadsJSONParseError) as exc_info:
            _run_bd_command(["list"])

        error = exc_info.value
        assert "{invalid: json}" in error.json_content

    @patch("subprocess.run")
    def test_run_bd_command_uses_timeout(self, mock_run):
        """Test that timeout parameter is passed to subprocess."""
        from beads.utils import _run_bd_command

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        _run_bd_command(["list"])

        call_kwargs = mock_run.call_args[1]
        assert "timeout" in call_kwargs
        # Default timeout should be 30s
        assert call_kwargs["timeout"] == 30

    @patch("subprocess.run")
    def test_run_bd_command_captures_output(self, mock_run):
        """Test that stdout and stderr are captured."""
        from beads.utils import _run_bd_command

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        _run_bd_command(["list"])

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["capture_output"] is True
        assert call_kwargs["text"] is True


# Tests for T024: JSON parsing utilities
class TestJSONParsing:
    """Test JSON parsing helper functions."""

    def test_parse_issue_json_valid(self):
        """Test parsing valid issue JSON."""
        from beads.utils import parse_issue_json

        json_data = {
            "id": "test-123",
            "title": "Test Issue",
            "description": "Description",
            "status": "open",
            "priority": 1,
            "issue_type": "feature",
            "created_at": "2025-11-07T12:00:00Z",
            "updated_at": "2025-11-07T12:00:00Z",
            "content_hash": "abc123",
            "source_repo": "."
        }

        # This should not raise an error
        result = parse_issue_json(json_data)
        assert result["id"] == "test-123"
        assert result["title"] == "Test Issue"

    def test_parse_issue_json_missing_required_field(self):
        """Test that missing required fields raise appropriate errors."""
        from beads.utils import parse_issue_json

        incomplete_data = {
            "id": "test-123",
            # Missing title and other required fields
        }

        with pytest.raises((KeyError, ValueError)):
            parse_issue_json(incomplete_data)

    def test_parse_issues_list_json(self):
        """Test parsing list of issues JSON."""
        from beads.utils import parse_issues_list_json

        json_data = [
            {
                "id": "test-1",
                "title": "Issue 1",
                "status": "open",
                "priority": 0,
                "issue_type": "bug",
                "description": "",
                "created_at": "2025-11-07T12:00:00Z",
                "updated_at": "2025-11-07T12:00:00Z",
                "content_hash": "hash1",
                "source_repo": "."
            },
            {
                "id": "test-2",
                "title": "Issue 2",
                "status": "in_progress",
                "priority": 1,
                "issue_type": "feature",
                "description": "",
                "created_at": "2025-11-07T12:00:00Z",
                "updated_at": "2025-11-07T12:00:00Z",
                "content_hash": "hash2",
                "source_repo": "."
            }
        ]

        result = parse_issues_list_json(json_data)
        assert len(result) == 2
        assert result[0]["id"] == "test-1"
        assert result[1]["id"] == "test-2"

    def test_parse_issues_list_json_empty(self):
        """Test parsing empty issues list."""
        from beads.utils import parse_issues_list_json

        result = parse_issues_list_json([])
        assert result == []

    def test_parse_dependency_tree_json(self):
        """Test parsing dependency tree JSON."""
        from beads.utils import parse_dependency_tree_json

        json_data = {
            "issue_id": "test-123",
            "blockers": ["issue-A", "issue-B"],
            "blocked_by": ["issue-C"]
        }

        result = parse_dependency_tree_json(json_data)
        assert result["issue_id"] == "test-123"
        assert result["blockers"] == ["issue-A", "issue-B"]
        assert result["blocked_by"] == ["issue-C"]

    def test_parse_cycles_json(self):
        """Test parsing cycles JSON."""
        from beads.utils import parse_cycles_json

        json_data = {
            "cycles": [
                ["issue-A", "issue-B", "issue-A"],
                ["issue-X", "issue-Y", "issue-Z", "issue-X"]
            ]
        }

        result = parse_cycles_json(json_data)
        assert len(result) == 2
        assert result[0] == ["issue-A", "issue-B", "issue-A"]
        assert result[1] == ["issue-X", "issue-Y", "issue-Z", "issue-X"]

    def test_parse_cycles_json_no_cycles(self):
        """Test parsing cycles JSON when no cycles exist."""
        from beads.utils import parse_cycles_json

        json_data = {"cycles": []}

        result = parse_cycles_json(json_data)
        assert result == []
