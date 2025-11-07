"""Custom exceptions for the Vector Memory Manager."""


class VectorMemoryError(Exception):
    """Base exception for all vector memory errors."""

    pass


class CoordinateValidationError(VectorMemoryError):
    """Coordinate values out of range or invalid."""

    pass


class ImmutableLayerError(VectorMemoryError):
    """Attempt to modify immutable architecture layer (z=1)."""

    pass


class ConcurrencyError(VectorMemoryError):
    """Concurrent access conflict or lock timeout."""

    pass


class StorageError(VectorMemoryError):
    """File system or Git operation failed."""

    pass


class QueryError(VectorMemoryError):
    """Query parameters invalid or malformed."""

    pass
