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
        x: Issue number in the DAG (range: 1-1000 for MVP)
        y: Development cycle stage (1=architect, 2=test, 3=implement, 4=review, 5=merge)
        z: Memory layer (1=Architecture, 2=Interfaces, 3=Implementation, 4=Ephemeral)
    """

    x: int
    y: int
    z: int

    def __post_init__(self) -> None:
        """Validate coordinate values on construction."""
        if not (1 <= self.x <= 1000):
            raise CoordinateValidationError(f"x must be in [1, 1000], got {self.x}")
        if self.y not in {1, 2, 3, 4, 5}:
            raise CoordinateValidationError(f"y must be in {{1, 2, 3, 4, 5}}, got {self.y}")
        if self.z not in {1, 2, 3, 4}:
            raise CoordinateValidationError(f"z must be in {{1, 2, 3, 4}}, got {self.z}")

    def to_tuple(self) -> tuple[int, int, int]:
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
            Path object like .vector-memory/x-005/y-2-z-1.json
        """
        return Path(f".vector-memory/x-{self.x:03d}/y-{self.y}-z-{self.z}.json")

    @staticmethod
    def from_path(path: Path) -> "VectorCoordinate":
        """
        Parse coordinate from file path.

        Args:
            path: File path to parse (e.g., .vector-memory/x-005/y-2-z-1.json)

        Returns:
            VectorCoordinate parsed from path

        Raises:
            ValueError: If path format is invalid
        """
        # Match pattern: x-NNN/y-N-z-N.json
        path_str = str(path).replace("\\", "/")  # Normalize Windows paths
        match = re.search(r"x-(\d+)/y-(\d+)-z-(\d+)\.json", path_str)
        if not match:
            raise ValueError(f"Invalid coordinate path: {path}")

        x, y, z = map(int, match.groups())
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
