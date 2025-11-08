"""
Vector Memory Manager - Coordinate-based storage system for AI agent decisions.

This package provides a 3D coordinate-based storage system that enables AI agents
to store and retrieve decisions using coordinates (x=issue, y=cycle stage, z=memory layer).

Key features:
- Store/retrieve decisions at 3D coordinates
- Immutable architecture layer (z=1)
- Git-backed persistence
- Partial ordering queries for rollback support
- Content-based search
"""

from vector_memory.coordinate import VectorCoordinate
from vector_memory.exceptions import (
    ConcurrencyError,
    CoordinateValidationError,
    ImmutableLayerError,
    QueryError,
    StorageError,
    VectorMemoryError,
)
from vector_memory.manager import VectorMemoryManager
from vector_memory.storage import MemoryLayer, StoredDecision

__version__ = "0.1.0"

__all__ = [
    # Main API
    "VectorMemoryManager",
    # Data structures
    "VectorCoordinate",
    "StoredDecision",
    "MemoryLayer",
    # Exceptions
    "VectorMemoryError",
    "CoordinateValidationError",
    "ImmutableLayerError",
    "ConcurrencyError",
    "StorageError",
    "QueryError",
]
