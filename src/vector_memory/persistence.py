"""Git persistence operations for vector memory."""

import subprocess
from datetime import datetime
from pathlib import Path


class GitPersistence:
    """Handles Git operations for vector memory persistence."""

    def __init__(self, repo_path: Path):
        """
        Initialize Git persistence handler.

        Args:
            repo_path: Path to Git repository root
        """
        self.repo_path = repo_path

    def add_vector_memory(self) -> None:
        """
        Add .vector-memory/ directory to Git staging area.

        Raises:
            subprocess.CalledProcessError: If git add fails
        """
        subprocess.run(
            ["git", "add", ".vector-memory/"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

    def commit(self, message: str | None = None, decision_count: int = 0) -> bool:
        """
        Create a Git commit with vector memory changes.

        Args:
            message: Optional custom commit message
            decision_count: Number of decisions being committed

        Returns:
            True if commit was created, False if nothing to commit

        Raises:
            subprocess.CalledProcessError: If git commit fails
        """
        # Generate default message if none provided
        if message is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"vector-memory: sync {decision_count} decision(s) at {timestamp}"

        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            # Check if it's just "nothing to commit"
            if "nothing to commit" in e.stdout or "nothing to commit" in e.stderr:
                return False
            # Otherwise, it's a real error
            raise

    def get_status(self) -> str:
        """
        Get Git status for .vector-memory/ directory.

        Returns:
            Git status output

        Raises:
            subprocess.CalledProcessError: If git status fails
        """
        result = subprocess.run(
            ["git", "status", ".vector-memory/", "--short"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def has_changes(self) -> bool:
        """
        Check if there are uncommitted changes in .vector-memory/.

        Returns:
            True if there are changes, False otherwise
        """
        status = self.get_status()
        return bool(status.strip())
