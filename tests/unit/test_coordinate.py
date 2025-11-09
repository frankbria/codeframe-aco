"""Unit tests for VectorCoordinate."""

from pathlib import Path

import pytest

from vector_memory.coordinate import VectorCoordinate
from vector_memory.exceptions import CoordinateValidationError


class TestVectorCoordinateValidation:
    """Test coordinate validation rules."""

    def test_valid_coordinate(self, mock_issue_id):
        """Test creating valid coordinates."""
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        assert coord.x == mock_issue_id(5)
        assert coord.y == 2
        assert coord.z == 1

    def test_x_invalid_format(self, mock_issue_id):
        """Test x value with invalid format."""
        with pytest.raises(CoordinateValidationError, match="x must be a valid Beads issue ID"):
            VectorCoordinate(x="invalid-id", y=2, z=1)

    def test_x_integer_not_allowed(self, mock_issue_id):
        """Test that integer x values are rejected."""
        with pytest.raises(CoordinateValidationError, match="x must be a valid Beads issue ID"):
            VectorCoordinate(x=5, y=2, z=1)

    def test_y_invalid(self, mock_issue_id):
        """Test invalid y value."""
        with pytest.raises(CoordinateValidationError, match="y must be in"):
            VectorCoordinate(x=mock_issue_id(5), y=6, z=1)

    def test_z_invalid(self, mock_issue_id):
        """Test invalid z value."""
        with pytest.raises(CoordinateValidationError, match="z must be in"):
            VectorCoordinate(x=mock_issue_id(5), y=2, z=5)

    def test_all_valid_y_values(self, mock_issue_id):
        """Test all valid y values (1-5)."""
        for y in [1, 2, 3, 4, 5]:
            coord = VectorCoordinate(x=mock_issue_id(1), y=y, z=1)
            assert coord.y == y

    def test_all_valid_z_values(self, mock_issue_id):
        """Test all valid z values (1-4)."""
        for z in [1, 2, 3, 4]:
            coord = VectorCoordinate(x=mock_issue_id(1), y=1, z=z)
            assert coord.z == z


class TestVectorCoordinateOperations:
    """Test coordinate operations."""

    def test_to_tuple(self, mock_issue_id):
        """Test conversion to tuple."""
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        assert coord.to_tuple() == (mock_issue_id(5), 2, 1)

    def test_to_path(self, mock_issue_id):
        """Test conversion to file path."""
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        path = coord.to_path()
        assert str(path) == f".vector-memory/x-{mock_issue_id(5)}/y-2-z-1.json"

    def test_to_path_format(self, mock_issue_id):
        """Test x value format in path."""
        coord = VectorCoordinate(x=mock_issue_id(1), y=2, z=1)
        path = coord.to_path()
        assert f"x-{mock_issue_id(1)}" in str(path)

    def test_from_path(self, mock_issue_id):
        """Test parsing coordinate from path."""
        path = Path(f".vector-memory/x-{mock_issue_id(5)}/y-2-z-1.json")
        coord = VectorCoordinate.from_path(path)
        assert coord.x == mock_issue_id(5)
        assert coord.y == 2
        assert coord.z == 1

    def test_from_path_windows(self, mock_issue_id):
        """Test parsing coordinate from Windows-style path."""
        path = Path(f".vector-memory\\x-{mock_issue_id(10)}\\y-3-z-2.json")
        coord = VectorCoordinate.from_path(path)
        assert coord.x == mock_issue_id(10)
        assert coord.y == 3
        assert coord.z == 2

    def test_from_path_invalid(self, mock_issue_id):
        """Test parsing invalid path."""
        path = Path("invalid/path.json")
        with pytest.raises(ValueError, match="Invalid coordinate path"):
            VectorCoordinate.from_path(path)

    def test_coordinate_equality(self, mock_issue_id):
        """Test coordinate equality."""
        coord1 = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        coord2 = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        coord3 = VectorCoordinate(x=mock_issue_id(5), y=2, z=2)

        assert coord1 == coord2
        assert coord1 != coord3

    def test_coordinate_hash(self, mock_issue_id):
        """Test coordinate hashing for dict keys."""
        coord1 = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        coord2 = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)

        coord_dict = {coord1: "value1"}
        assert coord_dict[coord2] == "value1"

    def test_coordinate_sorting(self, mock_issue_id):
        """Test lexicographic coordinate sorting."""
        coords = [
            VectorCoordinate(x=mock_issue_id(5), y=2, z=1),
            VectorCoordinate(x=mock_issue_id(1), y=5, z=1),
            VectorCoordinate(x=mock_issue_id(5), y=1, z=1),
            VectorCoordinate(x=mock_issue_id(3), y=3, z=1),
        ]

        sorted_coords = sorted(coords)

        assert sorted_coords[0].x == mock_issue_id(1)
        assert sorted_coords[1].x == mock_issue_id(3)
        assert sorted_coords[2].x == mock_issue_id(5) and sorted_coords[2].y == 1
        assert sorted_coords[3].x == mock_issue_id(5) and sorted_coords[3].y == 2


class TestVectorCoordinateBoundaries:
    """Test boundary conditions."""

    def test_minimum_values(self, mock_issue_id):
        """Test minimum valid values."""
        coord = VectorCoordinate(x=mock_issue_id(1), y=1, z=1)
        assert coord.to_tuple() == (mock_issue_id(1), 1, 1)

    def test_maximum_values(self, mock_issue_id):
        """Test maximum valid values."""
        coord = VectorCoordinate(x=mock_issue_id(999), y=5, z=4)
        assert coord.to_tuple() == (mock_issue_id(999), 5, 4)

    def test_roundtrip_conversion(self, mock_issue_id):
        """Test path conversion roundtrip."""
        original = VectorCoordinate(x=mock_issue_id(42), y=3, z=2)
        path = original.to_path()
        recovered = VectorCoordinate.from_path(path)
        assert original == recovered


class TestVectorCoordinateEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_x_format_no_hash(self, mock_issue_id):
        """Test x value without hash suffix."""
        with pytest.raises(CoordinateValidationError, match="x must be a valid Beads issue ID"):
            VectorCoordinate(x="test-issue", y=2, z=1)

    def test_float_y_value(self, mock_issue_id):
        """Test non-integer y value."""
        with pytest.raises((TypeError, CoordinateValidationError)):
            VectorCoordinate(x=mock_issue_id(5), y=2.5, z=1)

    def test_float_z_value(self, mock_issue_id):
        """Test non-integer z value."""
        with pytest.raises((TypeError, CoordinateValidationError)):
            VectorCoordinate(x=mock_issue_id(5), y=2, z=1.5)

    def test_invalid_x_format_short_string(self, mock_issue_id):
        """Test x value with invalid format (too short)."""
        with pytest.raises(CoordinateValidationError, match="x must be a valid Beads issue ID"):
            VectorCoordinate(x="short", y=2, z=1)

    def test_none_x_value(self, mock_issue_id):
        """Test None x value."""
        with pytest.raises((TypeError, CoordinateValidationError)):
            VectorCoordinate(x=None, y=2, z=1)

    def test_integer_x_rejected(self, mock_issue_id):
        """Test integer x value is rejected."""
        with pytest.raises(CoordinateValidationError, match="x must be a valid Beads issue ID"):
            VectorCoordinate(x=-1, y=2, z=1)

    def test_negative_y_value(self, mock_issue_id):
        """Test negative y value."""
        with pytest.raises(CoordinateValidationError, match="y must be in"):
            VectorCoordinate(x=mock_issue_id(5), y=-1, z=1)

    def test_negative_z_value(self, mock_issue_id):
        """Test negative z value."""
        with pytest.raises(CoordinateValidationError, match="z must be in"):
            VectorCoordinate(x=mock_issue_id(5), y=2, z=-1)

    def test_empty_x_value(self, mock_issue_id):
        """Test empty string x value."""
        with pytest.raises(CoordinateValidationError, match="x must be a valid Beads issue ID"):
            VectorCoordinate(x="", y=2, z=1)

    def test_zero_y_value(self, mock_issue_id):
        """Test zero y value (y must be >= 1)."""
        with pytest.raises(CoordinateValidationError, match="y must be in"):
            VectorCoordinate(x=mock_issue_id(5), y=0, z=1)

    def test_zero_z_value(self, mock_issue_id):
        """Test zero z value (z must be >= 1)."""
        with pytest.raises(CoordinateValidationError, match="z must be in"):
            VectorCoordinate(x=mock_issue_id(5), y=2, z=0)

    def test_from_path_with_extra_directories(self, mock_issue_id):
        """Test parsing path with extra directory levels."""
        path = Path(f"some/deep/.vector-memory/x-{mock_issue_id(5)}/y-2-z-1.json")
        coord = VectorCoordinate.from_path(path)
        assert coord.x == mock_issue_id(5)
        assert coord.y == 2
        assert coord.z == 1

    def test_from_path_wrong_file_extension(self, mock_issue_id):
        """Test parsing path with wrong file extension."""
        path = Path(f".vector-memory/x-{mock_issue_id(5)}/y-2-z-1.txt")
        with pytest.raises(ValueError, match="Invalid coordinate path"):
            VectorCoordinate.from_path(path)

    def test_from_path_missing_components(self, mock_issue_id):
        """Test parsing incomplete coordinate path."""
        path = Path(f".vector-memory/x-{mock_issue_id(5)}/y-2.json")
        with pytest.raises(ValueError, match="Invalid coordinate path"):
            VectorCoordinate.from_path(path)

    def test_from_path_malformed_x(self, mock_issue_id):
        """Test parsing path with malformed x component."""
        path = Path(".vector-memory/x-invalid/y-2-z-1.json")
        with pytest.raises((ValueError, CoordinateValidationError)):
            VectorCoordinate.from_path(path)

    def test_repr_string(self, mock_issue_id):
        """Test string representation of coordinate."""
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        repr_str = repr(coord)
        assert mock_issue_id(5) in repr_str
        assert "2" in repr_str
        assert "1" in repr_str

    def test_coordinate_immutability(self, mock_issue_id):
        """Test that coordinates are immutable (dataclass frozen)."""
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        with pytest.raises(AttributeError):
            coord.x = mock_issue_id(10)

    def test_large_x_boundary(self, mock_issue_id):
        """Test x value at maximum boundary."""
        coord = VectorCoordinate(x=mock_issue_id(999), y=1, z=1)
        assert coord.x == mock_issue_id(999)

    def test_valid_x_format_verified(self, mock_issue_id):
        """Test that valid x format is accepted."""
        coord = VectorCoordinate(x=mock_issue_id(100), y=1, z=1)
        assert coord.x == mock_issue_id(100)

    def test_all_boundaries_together(self, mock_issue_id):
        """Test all boundaries at maximum values."""
        coord = VectorCoordinate(x=mock_issue_id(999), y=5, z=4)
        path = coord.to_path()
        assert f"x-{mock_issue_id(999)}" in str(path)
        assert "y-5-z-4" in str(path)
