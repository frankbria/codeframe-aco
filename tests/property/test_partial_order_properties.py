"""Property-based tests for partial ordering (Phase 7 - User Story 5)."""

from hypothesis import given
from hypothesis import strategies as st

from vector_memory.query import PartialOrder


class TestPartialOrderProperties:
    """Property-based tests for partial ordering mathematical properties."""

    @given(
        x=st.integers(min_value=1, max_value=1000),
        y=st.integers(min_value=1, max_value=5),
    )
    def test_reflexive_property(self, x, y):
        """Test reflexive property: (x,y) <= (x,y) is always True."""
        coord = (x, y)
        # Reflexive: a <= a
        assert PartialOrder.less_equal(coord, coord) is True

    @given(
        x1=st.integers(min_value=1, max_value=500),
        y1=st.integers(min_value=1, max_value=5),
        x2=st.integers(min_value=501, max_value=1000),
        y2=st.integers(min_value=1, max_value=5),
    )
    def test_transitive_property(self, x1, y1, x2, y2):
        """Test transitive property: if a < b and b < c, then a < c."""
        # Arrange coordinates so (x1,y1) < (x2,y2) < (x3,y3)
        coord1 = (x1, y1)
        coord2 = (x2, y2)
        coord3 = (x2 + 1, y2)  # Guaranteed larger

        # Transitivity: if a < b and b < c, then a < c
        if PartialOrder.less_than(coord1, coord2) and PartialOrder.less_than(coord2, coord3):
            assert PartialOrder.less_than(coord1, coord3) is True

    @given(
        x1=st.integers(min_value=1, max_value=1000),
        y1=st.integers(min_value=1, max_value=5),
        x2=st.integers(min_value=1, max_value=1000),
        y2=st.integers(min_value=1, max_value=5),
    )
    def test_antisymmetric_property(self, x1, y1, x2, y2):
        """Test antisymmetric property: if a <= b and b <= a, then a == b."""
        coord1 = (x1, y1)
        coord2 = (x2, y2)

        # Antisymmetry: if a <= b and b <= a, then a == b
        if PartialOrder.less_equal(coord1, coord2) and PartialOrder.less_equal(coord2, coord1):
            assert coord1 == coord2

    @given(
        x=st.integers(min_value=1, max_value=1000),
        y=st.integers(min_value=1, max_value=5),
    )
    def test_not_less_than_self(self, x, y):
        """Test that (x,y) is not less than itself."""
        coord = (x, y)
        assert PartialOrder.less_than(coord, coord) is False

    @given(
        x1=st.integers(min_value=1, max_value=999),
        y1=st.integers(min_value=1, max_value=5),
        y2=st.integers(min_value=1, max_value=5),
    )
    def test_x_ordering_dominates(self, x1, y1, y2):
        """Test that x coordinate ordering dominates y coordinate."""
        x2 = x1 + 1
        coord1 = (x1, y1)
        coord2 = (x2, y2)

        # If x1 < x2, then (x1, y1) < (x2, y2) regardless of y1, y2
        assert PartialOrder.less_than(coord1, coord2) is True
        assert PartialOrder.less_than(coord2, coord1) is False

    @given(
        x=st.integers(min_value=1, max_value=1000),
        y1=st.integers(min_value=1, max_value=4),
    )
    def test_y_ordering_when_x_equal(self, x, y1):
        """Test that y coordinate matters when x coordinates are equal."""
        y2 = y1 + 1
        coord1 = (x, y1)
        coord2 = (x, y2)

        # When x values equal, y determines ordering
        assert PartialOrder.less_than(coord1, coord2) is True
        assert PartialOrder.less_than(coord2, coord1) is False

    @given(
        x_threshold=st.integers(min_value=1, max_value=1000),
        y_threshold=st.integers(min_value=1, max_value=5),
    )
    def test_find_before_includes_only_smaller(self, x_threshold, y_threshold):
        """Test that find_before() only returns coordinates before threshold."""
        # Generate test coordinates
        coords = [
            (x_threshold - 1, y_threshold - 1, 1) if x_threshold > 1 and y_threshold > 1 else None,
            (x_threshold - 1, y_threshold, 1) if x_threshold > 1 else None,
            (x_threshold, y_threshold - 1, 1) if y_threshold > 1 else None,
            (x_threshold, y_threshold, 1),
            (x_threshold + 1, y_threshold, 1) if x_threshold < 1000 else None,
        ]

        # Filter out None values
        coords = [c for c in coords if c is not None]

        result = PartialOrder.find_before(coords, (x_threshold, y_threshold))

        # Verify all results are before threshold
        for coord in result:
            x, y, z = coord
            assert x < x_threshold or (x == x_threshold and y < y_threshold)

    @given(
        x1=st.integers(min_value=1, max_value=1000),
        y1=st.integers(min_value=1, max_value=5),
        x2=st.integers(min_value=1, max_value=1000),
        y2=st.integers(min_value=1, max_value=5),
    )
    def test_comparable_is_symmetric(self, x1, y1, x2, y2):
        """Test that comparable() is symmetric: comparable(a,b) == comparable(b,a)."""
        coord1 = (x1, y1)
        coord2 = (x2, y2)

        # Symmetric property
        assert PartialOrder.comparable(coord1, coord2) == PartialOrder.comparable(coord2, coord1)

    @given(
        x=st.integers(min_value=1, max_value=1000),
        y=st.integers(min_value=1, max_value=5),
        z=st.integers(min_value=1, max_value=4),
    )
    def test_z_coordinate_ignored_in_ordering(self, x, y, z):
        """Test that z coordinate doesn't affect partial ordering."""
        coord1 = (x, y, 1)
        coord2 = (x, y, 4)

        # Z coordinate should not affect ordering
        result1 = PartialOrder.find_before([coord1, coord2], (x + 1, y))
        result2 = PartialOrder.find_before([coord1, coord2], (x, y + 1))

        # Both should be included if before threshold, regardless of z
        assert len(result1) == 2 or (x == 1000)  # Unless at max x
        if y < 5:
            assert len(result2) == 2
