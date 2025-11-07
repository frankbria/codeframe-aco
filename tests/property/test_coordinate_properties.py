"""Property-based tests for VectorCoordinate using hypothesis."""

from hypothesis import given
from hypothesis import strategies as st

from vector_memory.coordinate import VectorCoordinate
from vector_memory.exceptions import CoordinateValidationError

# Define valid coordinate strategies
valid_x = st.integers(min_value=1, max_value=1000)
valid_y = st.integers(min_value=1, max_value=5)
valid_z = st.integers(min_value=1, max_value=4)


class TestCoordinateProperties:
    """Property-based tests for coordinate operations."""

    @given(x=valid_x, y=valid_y, z=valid_z)
    def test_coordinate_roundtrip(self, x, y, z):
        """Test that coordinate → path → coordinate is identity."""
        coord = VectorCoordinate(x, y, z)
        path = coord.to_path()
        recovered = VectorCoordinate.from_path(path)
        assert recovered == coord

    @given(x=valid_x, y=valid_y, z=valid_z)
    def test_to_tuple_consistency(self, x, y, z):
        """Test that to_tuple returns consistent values."""
        coord = VectorCoordinate(x, y, z)
        tuple_result = coord.to_tuple()
        assert tuple_result == (x, y, z)
        # Multiple calls should return same result
        assert coord.to_tuple() == tuple_result

    @given(x=valid_x, y=valid_y, z=valid_z)
    def test_hash_stability(self, x, y, z):
        """Test that hash is stable across equal coordinates."""
        coord1 = VectorCoordinate(x, y, z)
        coord2 = VectorCoordinate(x, y, z)
        assert hash(coord1) == hash(coord2)
        assert coord1 == coord2

    @given(
        x1=valid_x,
        y1=valid_y,
        z1=valid_z,
        x2=valid_x,
        y2=valid_y,
        z2=valid_z,
    )
    def test_sorting_transitive(self, x1, y1, z1, x2, y2, z2):
        """Test that sorting is transitive."""
        coord1 = VectorCoordinate(x1, y1, z1)
        coord2 = VectorCoordinate(x2, y2, z2)

        # If coord1 < coord2, then sorted list should have coord1 first
        coords = [coord1, coord2]
        sorted_coords = sorted(coords)

        if coord1 < coord2:
            assert sorted_coords[0] == coord1
        elif coord2 < coord1:
            assert sorted_coords[0] == coord2
        else:  # equal
            assert coord1 == coord2

    @given(x=valid_x, y=valid_y, z=valid_z)
    def test_path_contains_coordinates(self, x, y, z):
        """Test that path string contains coordinate values."""
        coord = VectorCoordinate(x, y, z)
        path_str = str(coord.to_path())

        # Path should contain x value (zero-padded)
        assert f"x-{x:03d}" in path_str

        # Path should contain y and z values
        assert f"y-{y}" in path_str
        assert f"z-{z}" in path_str

    @given(x=st.integers(max_value=0))
    def test_invalid_x_below_minimum(self, x):
        """Test that x values below 1 are rejected."""
        try:
            VectorCoordinate(x=x, y=1, z=1)
            # Should not reach here
            raise AssertionError(f"Expected CoordinateValidationError for x={x}")
        except CoordinateValidationError:
            pass  # Expected

    @given(x=st.integers(min_value=1001))
    def test_invalid_x_above_maximum(self, x):
        """Test that x values above 1000 are rejected."""
        try:
            VectorCoordinate(x=x, y=1, z=1)
            raise AssertionError(f"Expected CoordinateValidationError for x={x}")
        except CoordinateValidationError:
            pass  # Expected

    @given(y=st.integers().filter(lambda y: y not in {1, 2, 3, 4, 5}))
    def test_invalid_y_values(self, y):
        """Test that y values outside {1,2,3,4,5} are rejected."""
        try:
            VectorCoordinate(x=1, y=y, z=1)
            raise AssertionError(f"Expected CoordinateValidationError for y={y}")
        except CoordinateValidationError:
            pass  # Expected

    @given(z=st.integers().filter(lambda z: z not in {1, 2, 3, 4}))
    def test_invalid_z_values(self, z):
        """Test that z values outside {1,2,3,4} are rejected."""
        try:
            VectorCoordinate(x=1, y=1, z=z)
            raise AssertionError(f"Expected CoordinateValidationError for z={z}")
        except CoordinateValidationError:
            pass  # Expected
