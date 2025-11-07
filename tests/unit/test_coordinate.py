"""Unit tests for VectorCoordinate."""

from pathlib import Path

import pytest

from vector_memory.coordinate import VectorCoordinate
from vector_memory.exceptions import CoordinateValidationError


class TestVectorCoordinateValidation:
    """Test coordinate validation rules."""

    def test_valid_coordinate(self):
        """Test creating valid coordinates."""
        coord = VectorCoordinate(x=5, y=2, z=1)
        assert coord.x == 5
        assert coord.y == 2
        assert coord.z == 1

    def test_x_too_small(self):
        """Test x value below minimum."""
        with pytest.raises(CoordinateValidationError, match="x must be in"):
            VectorCoordinate(x=0, y=2, z=1)

    def test_x_too_large(self):
        """Test x value above maximum."""
        with pytest.raises(CoordinateValidationError, match="x must be in"):
            VectorCoordinate(x=1001, y=2, z=1)

    def test_y_invalid(self):
        """Test invalid y value."""
        with pytest.raises(CoordinateValidationError, match="y must be in"):
            VectorCoordinate(x=5, y=6, z=1)

    def test_z_invalid(self):
        """Test invalid z value."""
        with pytest.raises(CoordinateValidationError, match="z must be in"):
            VectorCoordinate(x=5, y=2, z=5)

    def test_all_valid_y_values(self):
        """Test all valid y values (1-5)."""
        for y in [1, 2, 3, 4, 5]:
            coord = VectorCoordinate(x=1, y=y, z=1)
            assert coord.y == y

    def test_all_valid_z_values(self):
        """Test all valid z values (1-4)."""
        for z in [1, 2, 3, 4]:
            coord = VectorCoordinate(x=1, y=1, z=z)
            assert coord.z == z


class TestVectorCoordinateOperations:
    """Test coordinate operations."""

    def test_to_tuple(self):
        """Test conversion to tuple."""
        coord = VectorCoordinate(x=5, y=2, z=1)
        assert coord.to_tuple() == (5, 2, 1)

    def test_to_path(self):
        """Test conversion to file path."""
        coord = VectorCoordinate(x=5, y=2, z=1)
        path = coord.to_path()
        assert str(path) == ".vector-memory/x-005/y-2-z-1.json"

    def test_to_path_padding(self):
        """Test x value padding in path."""
        coord = VectorCoordinate(x=1, y=2, z=1)
        path = coord.to_path()
        assert "x-001" in str(path)

    def test_from_path(self):
        """Test parsing coordinate from path."""
        path = Path(".vector-memory/x-005/y-2-z-1.json")
        coord = VectorCoordinate.from_path(path)
        assert coord.x == 5
        assert coord.y == 2
        assert coord.z == 1

    def test_from_path_windows(self):
        """Test parsing coordinate from Windows-style path."""
        path = Path(".vector-memory\\x-010\\y-3-z-2.json")
        coord = VectorCoordinate.from_path(path)
        assert coord.x == 10
        assert coord.y == 3
        assert coord.z == 2

    def test_from_path_invalid(self):
        """Test parsing invalid path."""
        path = Path("invalid/path.json")
        with pytest.raises(ValueError, match="Invalid coordinate path"):
            VectorCoordinate.from_path(path)

    def test_coordinate_equality(self):
        """Test coordinate equality."""
        coord1 = VectorCoordinate(x=5, y=2, z=1)
        coord2 = VectorCoordinate(x=5, y=2, z=1)
        coord3 = VectorCoordinate(x=5, y=2, z=2)

        assert coord1 == coord2
        assert coord1 != coord3

    def test_coordinate_hash(self):
        """Test coordinate hashing for dict keys."""
        coord1 = VectorCoordinate(x=5, y=2, z=1)
        coord2 = VectorCoordinate(x=5, y=2, z=1)

        coord_dict = {coord1: "value1"}
        assert coord_dict[coord2] == "value1"

    def test_coordinate_sorting(self):
        """Test lexicographic coordinate sorting."""
        coords = [
            VectorCoordinate(x=5, y=2, z=1),
            VectorCoordinate(x=1, y=5, z=1),
            VectorCoordinate(x=5, y=1, z=1),
            VectorCoordinate(x=3, y=3, z=1),
        ]

        sorted_coords = sorted(coords)

        assert sorted_coords[0].x == 1
        assert sorted_coords[1].x == 3
        assert sorted_coords[2].x == 5 and sorted_coords[2].y == 1
        assert sorted_coords[3].x == 5 and sorted_coords[3].y == 2


class TestVectorCoordinateBoundaries:
    """Test boundary conditions."""

    def test_minimum_values(self):
        """Test minimum valid values."""
        coord = VectorCoordinate(x=1, y=1, z=1)
        assert coord.to_tuple() == (1, 1, 1)

    def test_maximum_values(self):
        """Test maximum valid values."""
        coord = VectorCoordinate(x=1000, y=5, z=4)
        assert coord.to_tuple() == (1000, 5, 4)

    def test_roundtrip_conversion(self):
        """Test path conversion roundtrip."""
        original = VectorCoordinate(x=42, y=3, z=2)
        path = original.to_path()
        recovered = VectorCoordinate.from_path(path)
        assert original == recovered


class TestVectorCoordinateEdgeCases:
    """Test edge cases and error conditions."""

    def test_float_x_value(self):
        """Test non-integer x value - Python dataclass accepts floats."""
        # Python dataclass with int type hint doesn't enforce type at runtime
        coord = VectorCoordinate(x=5.5, y=2, z=1)
        assert coord.x == 5.5  # Float is accepted
        # Note: In production, could add runtime type checking if needed

    def test_float_y_value(self):
        """Test non-integer y value."""
        with pytest.raises((TypeError, CoordinateValidationError)):
            VectorCoordinate(x=5, y=2.5, z=1)

    def test_float_z_value(self):
        """Test non-integer z value."""
        with pytest.raises((TypeError, CoordinateValidationError)):
            VectorCoordinate(x=5, y=2, z=1.5)

    def test_string_x_value(self):
        """Test string x value."""
        with pytest.raises((TypeError, CoordinateValidationError)):
            VectorCoordinate(x="5", y=2, z=1)

    def test_none_x_value(self):
        """Test None x value."""
        with pytest.raises((TypeError, CoordinateValidationError)):
            VectorCoordinate(x=None, y=2, z=1)

    def test_negative_x_value(self):
        """Test negative x value."""
        with pytest.raises(CoordinateValidationError, match="x must be in"):
            VectorCoordinate(x=-1, y=2, z=1)

    def test_negative_y_value(self):
        """Test negative y value."""
        with pytest.raises(CoordinateValidationError, match="y must be in"):
            VectorCoordinate(x=5, y=-1, z=1)

    def test_negative_z_value(self):
        """Test negative z value."""
        with pytest.raises(CoordinateValidationError, match="z must be in"):
            VectorCoordinate(x=5, y=2, z=-1)

    def test_zero_x_value(self):
        """Test zero x value (x must be >= 1)."""
        with pytest.raises(CoordinateValidationError, match="x must be in"):
            VectorCoordinate(x=0, y=2, z=1)

    def test_zero_y_value(self):
        """Test zero y value (y must be >= 1)."""
        with pytest.raises(CoordinateValidationError, match="y must be in"):
            VectorCoordinate(x=5, y=0, z=1)

    def test_zero_z_value(self):
        """Test zero z value (z must be >= 1)."""
        with pytest.raises(CoordinateValidationError, match="z must be in"):
            VectorCoordinate(x=5, y=2, z=0)

    def test_from_path_with_extra_directories(self):
        """Test parsing path with extra directory levels."""
        path = Path("some/deep/.vector-memory/x-005/y-2-z-1.json")
        coord = VectorCoordinate.from_path(path)
        assert coord.x == 5
        assert coord.y == 2
        assert coord.z == 1

    def test_from_path_wrong_file_extension(self):
        """Test parsing path with wrong file extension."""
        path = Path(".vector-memory/x-005/y-2-z-1.txt")
        with pytest.raises(ValueError, match="Invalid coordinate path"):
            VectorCoordinate.from_path(path)

    def test_from_path_missing_components(self):
        """Test parsing incomplete coordinate path."""
        path = Path(".vector-memory/x-005/y-2.json")
        with pytest.raises(ValueError, match="Invalid coordinate path"):
            VectorCoordinate.from_path(path)

    def test_from_path_malformed_x(self):
        """Test parsing path with malformed x component."""
        path = Path(".vector-memory/x-abc/y-2-z-1.json")
        with pytest.raises((ValueError, CoordinateValidationError)):
            VectorCoordinate.from_path(path)

    def test_repr_string(self):
        """Test string representation of coordinate."""
        coord = VectorCoordinate(x=5, y=2, z=1)
        repr_str = repr(coord)
        assert "5" in repr_str
        assert "2" in repr_str
        assert "1" in repr_str

    def test_coordinate_immutability(self):
        """Test that coordinates are immutable (dataclass frozen)."""
        coord = VectorCoordinate(x=5, y=2, z=1)
        with pytest.raises(AttributeError):
            coord.x = 10

    def test_large_x_boundary(self):
        """Test x value at maximum boundary."""
        coord = VectorCoordinate(x=1000, y=1, z=1)
        assert coord.x == 1000

    def test_large_x_over_boundary(self):
        """Test x value just over maximum boundary."""
        with pytest.raises(CoordinateValidationError, match="x must be in"):
            VectorCoordinate(x=1001, y=1, z=1)

    def test_all_boundaries_together(self):
        """Test all boundaries at maximum values."""
        coord = VectorCoordinate(x=1000, y=5, z=4)
        path = coord.to_path()
        assert "x-1000" in str(path)
        assert "y-5-z-4" in str(path)