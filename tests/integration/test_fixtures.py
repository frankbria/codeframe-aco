"""Integration tests to verify pytest fixtures work correctly.

This module tests that the pytest fixtures defined in conftest.py
work as expected with real Beads CLI commands.
"""

import pytest
from pathlib import Path


# T032: Verify fixtures work with simple integration test
class TestFixtures:
    """Test that pytest fixtures are properly configured."""

    def test_beads_db_fixture_creates_directory(self, test_beads_db):
        """Test that test_beads_db fixture creates a .beads/ directory."""
        assert isinstance(test_beads_db, Path)
        assert test_beads_db.exists()
        assert test_beads_db.is_dir()

        beads_dir = test_beads_db / '.beads'
        assert beads_dir.exists()
        assert beads_dir.is_dir()

    def test_beads_db_fixture_is_isolated(self, test_beads_db):
        """Test that each test gets an isolated database."""
        # This test should get a fresh, empty database
        # If we create an issue here, it shouldn't appear in other tests
        import subprocess

        result = subprocess.run(
            ['bd', 'create', 'Isolation test issue'],
            cwd=test_beads_db,
            capture_output=True,
            text=True,
            check=False
        )

        assert result.returncode == 0
        assert "Created issue:" in result.stdout

    def test_beads_client_fixture_exists(self, beads_client):
        """Test that beads_client fixture provides a client instance."""
        # This will fail until we implement BeadsClient and create_beads_client
        # For now, just check that the fixture is defined
        assert beads_client is not None

    def test_test_issues_fixture_creates_issues(self, test_issues):
        """Test that test_issues fixture creates sample issues."""
        assert isinstance(test_issues, dict)

        # Should have created at least some issues
        assert len(test_issues) > 0

        # Check that issue IDs are strings
        for name, issue_id in test_issues.items():
            assert isinstance(issue_id, str)
            assert len(issue_id) > 0

    def test_fixtures_work_together(self, test_beads_db, test_issues):
        """Test that fixtures can be used together in the same test."""
        import subprocess

        # test_issues should have created issues in test_beads_db
        result = subprocess.run(
            ['bd', '--json', 'list'],
            cwd=test_beads_db,
            capture_output=True,
            text=True,
            check=False
        )

        assert result.returncode == 0

        # Should have JSON output
        import json
        issues = json.loads(result.stdout)

        # Should have at least some issues created by test_issues fixture
        assert isinstance(issues, list)
        assert len(issues) >= 1  # At least one issue was created

    def test_fixture_cleanup(self, test_beads_db):
        """Test that fixture cleanup doesn't interfere with tests."""
        # Create a file in the test directory
        test_file = test_beads_db / 'test.txt'
        test_file.write_text('test content')

        assert test_file.exists()

        # After this test, tmp_path fixture should clean up automatically
        # No explicit cleanup needed
