"""VectorCoordinate - 3D coordinate system for addressing stored information."""

import re
from dataclasses import dataclass
from pathlib import Path

from vector_memory.exceptions import CoordinateValidationError


@dataclass(frozen=True)
class VectorCoordinate:
    """
    Represents a position in 3D space used to address stored information.

    Attributes:
        x: Beads issue ID (e.g., "codeframe-aco-t49", "codeframe-aco-xon")
        y: Development cycle stage (1=architect, 2=test, 3=implement, 4=review, 5=merge)
        z: Memory layer (1=Architecture, 2=Interfaces, 3=Implementation, 4=Ephemeral)
    """

    x: str  # Beads issue ID
    y: int
    z: int

    def __post_init__(self) -> None:
        """Validate coordinate values on construction."""
        # Validate Beads issue ID format: prefix-hash (e.g., "codeframe-aco-t49")
        if not isinstance(self.x, str) or not re.match(r'^[\w-]+-[a-z0-9]{3}$', self.x):
            raise CoordinateValidationError(
                f"x must be a valid Beads issue ID (format: 'project-prefix-xxx'), got: {self.x}"
            )
        if self.y not in {1, 2, 3, 4, 5}:
            raise CoordinateValidationError(f"y must be in {{1, 2, 3, 4, 5}}, got {self.y}")
        if self.z not in {1, 2, 3, 4}:
            raise CoordinateValidationError(f"z must be in {{1, 2, 3, 4}}, got {self.z}")

    def to_tuple(self) -> tuple[str, int, int]:
        """
        Convert to tuple for use as dict key.

        Returns:
            Tuple of (x, y, z) values
        """
        return (self.x, self.y, self.z)

    def to_path(self) -> Path:
        """
        Convert to file system path.

        Returns:
            Path object like .vector-memory/x-codeframe-aco-t49/y-2-z-1.json
        """
        return Path(f".vector-memory/x-{self.x}/y-{self.y}-z-{self.z}.json")

    @staticmethod
    def from_path(path: Path) -> "VectorCoordinate":
        """
        Parse coordinate from file path.

        Args:
            path: File path to parse (e.g., .vector-memory/x-codeframe-aco-t49/y-2-z-1.json)

        Returns:
            VectorCoordinate parsed from path

        Raises:
            ValueError: If path format is invalid
        """
        # Match pattern: x-{issue-id}/y-N-z-N.json
        path_str = str(path).replace("\\", "/")  # Normalize Windows paths
        match = re.search(r"x-([\w-]+)/y-(\d+)-z-(\d+)\.json", path_str)
        if not match:
            raise ValueError(f"Invalid coordinate path: {path}")

        x = match.group(1)  # issue ID (string)
        y = int(match.group(2))
        z = int(match.group(3))
        return VectorCoordinate(x=x, y=y, z=z)

    def __lt__(self, other: "VectorCoordinate") -> bool:
        """
        Lexicographic comparison for sorting.

        Args:
            other: Another VectorCoordinate

        Returns:
            True if self < other lexicographically
        """
        return self.to_tuple() < other.to_tuple()

    def __hash__(self) -> int:
        """
        Hash function for use in sets and dict keys.

        Returns:
            Hash of coordinate tuple
        """
        return hash(self.to_tuple())