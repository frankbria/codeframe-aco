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
        x_id = f"test-issue-{x}"
        coord = (x_id, y)
        dag_order = {x_id: x}
        # Reflexive: a <= a
        assert PartialOrder.less_equal(coord, coord, dag_order) is True

    @given(
        x1=st.integers(min_value=1, max_value=500),
        y1=st.integers(min_value=1, max_value=5),
        x2=st.integers(min_value=501, max_value=1000),
        y2=st.integers(min_value=1, max_value=5),
    )
    def test_transitive_property(self, x1, y1, x2, y2):
        """Test transitive property: if a < b and b < c, then a < c."""
        # Arrange coordinates so (x1,y1) < (x2,y2) < (x3,y3)
        x3 = x2 + 1
        x1_id, x2_id, x3_id = f"test-issue-{x1}", f"test-issue-{x2}", f"test-issue-{x3}"
        coord1 = (x1_id, y1)
        coord2 = (x2_id, y2)
        coord3 = (x3_id, y2)  # Guaranteed larger x
        dag_order = {x1_id: x1, x2_id: x2, x3_id: x3}

        # Transitivity: if a < b and b < c, then a < c
        if PartialOrder.less_than(coord1, coord2, dag_order) and PartialOrder.less_than(
            coord2, coord3, dag_order
        ):
            assert PartialOrder.less_than(coord1, coord3, dag_order) is True

    @given(
        x1=st.integers(min_value=1, max_value=1000),
        y1=st.integers(min_value=1, max_value=5),
        x2=st.integers(min_value=1, max_value=1000),
        y2=st.integers(min_value=1, max_value=5),
    )
    def test_antisymmetric_property(self, x1, y1, x2, y2):
        """Test antisymmetric property: if a <= b and b <= a, then a == b."""
        x1_id, x2_id = f"test-issue-{x1}", f"test-issue-{x2}"
        coord1 = (x1_id, y1)
        coord2 = (x2_id, y2)
        dag_order = {x1_id: x1, x2_id: x2}

        # Antisymmetry: if a <= b and b <= a, then a == b
        if PartialOrder.less_equal(coord1, coord2, dag_order) and PartialOrder.less_equal(
            coord2, coord1, dag_order
        ):
            assert coord1 == coord2

    @given(
        x=st.integers(min_value=1, max_value=1000),
        y=st.integers(min_value=1, max_value=5),
    )
    def test_not_less_than_self(self, x, y):
        """Test that (x,y) is not less than itself."""
        x_id = f"test-issue-{x}"
        coord = (x_id, y)
        dag_order = {x_id: x}
        assert PartialOrder.less_than(coord, coord, dag_order) is False

    @given(
        x1=st.integers(min_value=1, max_value=999),
        y1=st.integers(min_value=1, max_value=5),
        y2=st.integers(min_value=1, max_value=5),
    )
    def test_x_ordering_dominates(self, x1, y1, y2):
        """Test that x coordinate ordering dominates y coordinate."""
        x2 = x1 + 1
        x1_id, x2_id = f"test-issue-{x1}", f"test-issue-{x2}"
        coord1 = (x1_id, y1)
        coord2 = (x2_id, y2)
        dag_order = {x1_id: x1, x2_id: x2}

        # If x1 < x2, then (x1, y1) < (x2, y2) regardless of y1, y2
        assert PartialOrder.less_than(coord1, coord2, dag_order) is True
        assert PartialOrder.less_than(coord2, coord1, dag_order) is False

    @given(
        x=st.integers(min_value=1, max_value=1000),
        y1=st.integers(min_value=1, max_value=4),
    )
    def test_y_ordering_when_x_equal(self, x, y1):
        """Test that y coordinate matters when x coordinates are equal."""
        y2 = y1 + 1
        x_id = f"test-issue-{x}"
        coord1 = (x_id, y1)
        coord2 = (x_id, y2)
        dag_order = {x_id: x}

        # When x values equal, y determines ordering
        assert PartialOrder.less_than(coord1, coord2, dag_order) is True
        assert PartialOrder.less_than(coord2, coord1, dag_order) is False

    # TODO: Uncomment when find_before() is implemented
    # @given(
    #     x_threshold=st.integers(min_value=1, max_value=1000),
    #     y_threshold=st.integers(min_value=1, max_value=5),
    # )
    # def test_find_before_includes_only_smaller(self, x_threshold, y_threshold):
    #     """Test that find_before() only returns coordinates before threshold."""
    #     # Generate test coordinates
    #     x_ids = [f"test-issue-{i}" for i in range(x_threshold - 1, x_threshold + 2)]
    #     coords = [
    #         (x_ids[0], y_threshold - 1, 1) if x_threshold > 1 and y_threshold > 1 else None,
    #         (x_ids[0], y_threshold, 1) if x_threshold > 1 else None,
    #         (x_ids[1], y_threshold - 1, 1) if y_threshold > 1 else None,
    #         (x_ids[1], y_threshold, 1),
    #         (x_ids[2], y_threshold, 1) if x_threshold < 1000 else None,
    #     ]
    #
    #     # Filter out None values
    #     coords = [c for c in coords if c is not None]
    #     dag_order = {x_id: idx for idx, x_id in enumerate(x_ids)}
    #
    #     result = PartialOrder.find_before(coords, (x_ids[1], y_threshold), dag_order)
    #
    #     # Verify all results are before threshold
    #     for coord in result:
    #         x, y, z = coord
    #         assert dag_order[x] < dag_order[x_ids[1]] or (x == x_ids[1] and y < y_threshold)

    @given(
        x1=st.integers(min_value=1, max_value=1000),
        y1=st.integers(min_value=1, max_value=5),
        x2=st.integers(min_value=1, max_value=1000),
        y2=st.integers(min_value=1, max_value=5),
    )
    def test_comparable_is_symmetric(self, x1, y1, x2, y2):
        """Test that comparable() is symmetric: comparable(a,b) == comparable(b,a)."""
        x1_id, x2_id = f"test-issue-{x1}", f"test-issue-{x2}"
        coord1 = (x1_id, y1)
        coord2 = (x2_id, y2)
        dag_order = {x1_id: x1, x2_id: x2}

        # Symmetric property
        assert PartialOrder.comparable(coord1, coord2, dag_order) == PartialOrder.comparable(
            coord2, coord1, dag_order
        )

    # TODO: Uncomment when find_before() is implemented
    # @given(
    #     x=st.integers(min_value=1, max_value=1000),
    #     y=st.integers(min_value=1, max_value=5),
    #     z=st.integers(min_value=1, max_value=4),
    # )
    # def test_z_coordinate_ignored_in_ordering(self, x, y, z):
    #     """Test that z coordinate doesn't affect partial ordering."""
    #     x_id = f"test-issue-{x}"
    #     coord1 = (x_id, y, 1)
    #     coord2 = (x_id, y, 4)
    #     dag_order = {x_id: x, f"test-issue-{x+1}": x+1}
    #
    #     # Z coordinate should not affect ordering
    #     result1 = PartialOrder.find_before([coord1, coord2], (f"test-issue-{x+1}", y), dag_order)
    #     result2 = PartialOrder.find_before([coord1, coord2], (x_id, y + 1), dag_order)
    #
    #     # Both should be included if before threshold, regardless of z
    #     assert len(result1) == 2 or (x == 1000)  # Unless at max x
    #     if y < 5:
    #         assert len(result2) == 2
