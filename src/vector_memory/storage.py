"""Storage entities: StoredDecision and MemoryLayer."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from vector_memory.coordinate import VectorCoordinate
from vector_memory.exceptions import ImmutableLayerError


@dataclass
class StoredDecision:
    """
    Information stored at a specific coordinate, including content and metadata.

    Attributes:
        coordinate: Where this decision is stored
        content: The actual decision text (UTF-8)
        timestamp: When the decision was stored (ISO 8601)
        agent_id: Identifier of the agent that stored this decision
        issue_context: Additional context about the issue (optional)
    """

    coordinate: VectorCoordinate
    content: str
    timestamp: datetime
    agent_id: str
    issue_context: dict[str, str] | None = None

    def to_json(self) -> dict:
        """
        Serialize to JSON dict.

        Returns:
            Dictionary ready for JSON serialization
        """
        return {
            "coordinate": {
                "x": self.coordinate.x,
                "y": self.coordinate.y,
                "z": self.coordinate.z,
            },
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "issue_context": self.issue_context,
        }

    @staticmethod
    def from_json(data: dict) -> "StoredDecision":
        """
        Deserialize from JSON dict.

        Args:
            data: JSON dictionary with decision data

        Returns:
            StoredDecision instance
        """
        coord = VectorCoordinate(
            x=data["coordinate"]["x"],
            y=data["coordinate"]["y"],
            z=data["coordinate"]["z"],
        )
        return StoredDecision(
            coordinate=coord,
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            agent_id=data["agent_id"],
            issue_context=data.get("issue_context"),
        )

    def to_file(self, path: Path) -> None:
        """
        Write to JSON file with pretty-printing.

        Args:
            path: File path to write to
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def from_file(path: Path) -> "StoredDecision":
        """
        Read from JSON file.

        Args:
            path: File path to read from

        Returns:
            StoredDecision instance
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return StoredDecision.from_json(data)


class MemoryLayer:
    """
    Represents one of the four memory layers with different mutability characteristics.

    Attributes:
        z: Layer number (1-4)
        name: Layer name
        is_immutable: Whether layer can be modified after storage
    """

    ARCHITECTURE = None  # Will be initialized after class definition
    INTERFACES = None
    IMPLEMENTATION = None
    EPHEMERAL = None

    def __init__(self, z: int, name: str, is_immutable: bool):
        """
        Initialize a memory layer.

        Args:
            z: Layer number (1-4)
            name: Layer name
            is_immutable: Whether layer is immutable
        """
        self.z = z
        self.name = name
        self.is_immutable = is_immutable

    @classmethod
    def get_layer(cls, z: int) -> "MemoryLayer":
        """
        Get layer object for given z value.

        Args:
            z: Layer number (1-4)

        Returns:
            MemoryLayer object

        Raises:
            ValueError: If z is not in {1, 2, 3, 4}
        """
        layers = {
            1: cls.ARCHITECTURE,
            2: cls.INTERFACES,
            3: cls.IMPLEMENTATION,
            4: cls.EPHEMERAL,
        }
        if z not in layers:
            raise ValueError(f"Invalid layer z={z}, must be in {{1, 2, 3, 4}}")
        return layers[z]

    def validate_write(
        self, coord: VectorCoordinate, existing_decision: StoredDecision | None
    ) -> None:
        """
        Check if write is allowed at this coordinate.

        Args:
            coord: Coordinate to write to
            existing_decision: Existing decision at coordinate (None if empty)

        Raises:
            ImmutableLayerError: If trying to modify immutable layer
        """
        if self.is_immutable and existing_decision is not None:
            raise ImmutableLayerError(
                f"Cannot modify decision at {coord.to_tuple()} in {self.name} layer (z={self.z}). "
                f"Architecture layer decisions are immutable once stored."
            )

    def validate_delete(self, coord: VectorCoordinate) -> None:
        """
        Check if delete is allowed (always False for now).

        Args:
            coord: Coordinate to delete

        Raises:
            ImmutableLayerError: Always raises (deletion not supported)
        """
        raise ImmutableLayerError(
            f"Cannot delete decision at {coord.to_tuple()} in {self.name} layer. "
            f"Deletion is not supported for any layer."
        )


# Initialize layer constants
MemoryLayer.ARCHITECTURE = MemoryLayer(z=1, name="Architecture", is_immutable=True)
MemoryLayer.INTERFACES = MemoryLayer(z=2, name="Interfaces", is_immutable=False)
MemoryLayer.IMPLEMENTATION = MemoryLayer(z=3, name="Implementation", is_immutable=False)
MemoryLayer.EPHEMERAL = MemoryLayer(z=4, name="Ephemeral", is_immutable=False)
