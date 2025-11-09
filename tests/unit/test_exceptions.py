"""Unit tests for custom exception classes."""


# Tests for T016: BeadsError base exception
class TestBeadsError:
    """Test BeadsError base exception."""

    def test_beads_error_exists(self):
        """Test that BeadsError exception class exists."""
        from beads.exceptions import BeadsError

        assert issubclass(BeadsError, Exception)

    def test_beads_error_message(self):
        """Test that BeadsError can be raised with a message."""
        from beads.exceptions import BeadsError

        error = BeadsError("Test error message")
        assert str(error) == "Test error message"

    def test_beads_error_inheritance(self):
        """Test that BeadsError is a direct subclass of Exception."""
        from beads.exceptions import BeadsError

        assert BeadsError.__bases__ == (Exception,)


# Tests for T017: BeadsCommandError exception
class TestBeadsCommandError:
    """Test BeadsCommandError exception."""

    def test_beads_command_error_exists(self):
        """Test that BeadsCommandError exception class exists."""
        from beads.exceptions import BeadsCommandError

        assert issubclass(BeadsCommandError, Exception)

    def test_beads_command_error_inherits_from_beads_error(self):
        """Test that BeadsCommandError inherits from BeadsError."""
        from beads.exceptions import BeadsCommandError, BeadsError

        assert issubclass(BeadsCommandError, BeadsError)

    def test_beads_command_error_with_command_and_stderr(self):
        """Test BeadsCommandError with command and stderr attributes."""
        from beads.exceptions import BeadsCommandError

        error = BeadsCommandError(
            message="Command failed",
            command=["bd", "create", "test"],
            returncode=1,
            stderr="Error: invalid syntax",
        )

        assert "Command failed" in str(error)
        assert error.command == ["bd", "create", "test"]
        assert error.returncode == 1
        assert error.stderr == "Error: invalid syntax"


# Tests for T018: BeadsJSONParseError exception
class TestBeadsJSONParseError:
    """Test BeadsJSONParseError exception."""

    def test_beads_json_parse_error_exists(self):
        """Test that BeadsJSONParseError exception class exists."""
        from beads.exceptions import BeadsJSONParseError

        assert issubclass(BeadsJSONParseError, Exception)

    def test_beads_json_parse_error_inherits_from_beads_error(self):
        """Test that BeadsJSONParseError inherits from BeadsError."""
        from beads.exceptions import BeadsError, BeadsJSONParseError

        assert issubclass(BeadsJSONParseError, BeadsError)

    def test_beads_json_parse_error_with_context(self):
        """Test BeadsJSONParseError with JSON content and error."""
        from beads.exceptions import BeadsJSONParseError

        error = BeadsJSONParseError(
            message="Failed to parse JSON",
            json_content='{"invalid": json}',
            original_error="Expecting value: line 1 column 12 (char 11)",
        )

        assert "Failed to parse JSON" in str(error)
        assert error.json_content == '{"invalid": json}'
        assert error.original_error == "Expecting value: line 1 column 12 (char 11)"


# Tests for T019: BeadsIssueNotFoundError exception
class TestBeadsIssueNotFoundError:
    """Test BeadsIssueNotFoundError exception."""

    def test_beads_issue_not_found_error_exists(self):
        """Test that BeadsIssueNotFoundError exception class exists."""
        from beads.exceptions import BeadsIssueNotFoundError

        assert issubclass(BeadsIssueNotFoundError, Exception)

    def test_beads_issue_not_found_error_inherits_from_beads_error(self):
        """Test that BeadsIssueNotFoundError inherits from BeadsError."""
        from beads.exceptions import BeadsError, BeadsIssueNotFoundError

        assert issubclass(BeadsIssueNotFoundError, BeadsError)

    def test_beads_issue_not_found_error_with_issue_id(self):
        """Test BeadsIssueNotFoundError with issue_id attribute."""
        from beads.exceptions import BeadsIssueNotFoundError

        error = BeadsIssueNotFoundError(issue_id="codeframe-aco-xyz")

        assert "codeframe-aco-xyz" in str(error)
        assert error.issue_id == "codeframe-aco-xyz"


# Tests for T020: BeadsDependencyCycleError exception
class TestBeadsDependencyCycleError:
    """Test BeadsDependencyCycleError exception."""

    def test_beads_dependency_cycle_error_exists(self):
        """Test that BeadsDependencyCycleError exception class exists."""
        from beads.exceptions import BeadsDependencyCycleError

        assert issubclass(BeadsDependencyCycleError, Exception)

    def test_beads_dependency_cycle_error_inherits_from_beads_error(self):
        """Test that BeadsDependencyCycleError inherits from BeadsError."""
        from beads.exceptions import BeadsDependencyCycleError, BeadsError

        assert issubclass(BeadsDependencyCycleError, BeadsError)

    def test_beads_dependency_cycle_error_with_cycle_path(self):
        """Test BeadsDependencyCycleError with cycle_path attribute."""
        from beads.exceptions import BeadsDependencyCycleError

        cycle = ["issue-A", "issue-B", "issue-C", "issue-A"]
        error = BeadsDependencyCycleError(cycle_path=cycle)

        error_str = str(error)
        assert "circular dependency" in error_str.lower()
        assert error.cycle_path == cycle

    def test_beads_dependency_cycle_error_format(self):
        """Test BeadsDependencyCycleError formats cycle path nicely."""
        from beads.exceptions import BeadsDependencyCycleError

        cycle = ["issue-A", "issue-B", "issue-C", "issue-A"]
        error = BeadsDependencyCycleError(cycle_path=cycle)

        # Should contain some representation of the cycle
        error_str = str(error)
        assert "issue-A" in error_str
        assert "issue-B" in error_str
        assert "issue-C" in error_str
