"""Query operations and partial ordering utilities."""


class PartialOrder:
    """
    Utility class for partial ordering operations on (x, y) coordinate pairs.

    Implements partial ordering where (x, y) < (x₁, y₁) if and only if:
    - x < x₁ (earlier issue in DAG), OR
    - x == x₁ AND y < y₁ (same issue, earlier stage)

    Note: x-coordinates are Beads issue IDs (strings). Ordering can use either:
    - Lexicographic string comparison (default)
    - DAG topological sort positions (when dag_order provided)
    """

    @staticmethod
    def less_than(
        coord1: tuple[str, int], coord2: tuple[str, int], dag_order: dict[str, int] | None = None
    ) -> bool:
        """
        Check if coord1 < coord2 in partial order.

        Args:
            coord1: First coordinate (issue_id, cycle_stage)
            coord2: Second coordinate (issue_id, cycle_stage)
            dag_order: Optional mapping of issue_id → topological position.
                      If None, uses lexicographic string ordering.

        Returns:
            True if coord1 < coord2 in partial ordering
        """
        x1, y1 = coord1
        x2, y2 = coord2

        # Determine x-ordering
        if dag_order is not None:
            # Use DAG topological sort positions
            x1_pos = dag_order.get(x1, float("inf"))
            x2_pos = dag_order.get(x2, float("inf"))
            x_less = x1_pos < x2_pos
            x_equal = x1 == x2
        else:
            # Fallback: lexicographic string comparison
            x_less = x1 < x2
            x_equal = x1 == x2

        return x_less or (x_equal and y1 < y2)

    @staticmethod
    def less_equal(
        coord1: tuple[str, int], coord2: tuple[str, int], dag_order: dict[str, int] | None = None
    ) -> bool:
        """
        Check if coord1 <= coord2 in partial order.

        Args:
            coord1: First coordinate (issue_id, cycle_stage)
            coord2: Second coordinate (issue_id, cycle_stage)
            dag_order: Optional DAG ordering map

        Returns:
            True if coord1 <= coord2 in partial ordering
        """
        return coord1 == coord2 or PartialOrder.less_than(coord1, coord2, dag_order)

    @staticmethod
    def comparable(
        coord1: tuple[str, int], coord2: tuple[str, int], dag_order: dict[str, int] | None = None
    ) -> bool:
        """
        Check if coord1 and coord2 are comparable.

        Two coordinates are comparable if one is less than or equal to the other.

        Args:
            coord1: First coordinate (issue_id, cycle_stage)
            coord2: Second coordinate (issue_id, cycle_stage)
            dag_order: Optional DAG ordering map

        Returns:
            True if coordinates are comparable
        """
        return PartialOrder.less_equal(coord1, coord2, dag_order) or PartialOrder.less_equal(
            coord2, coord1, dag_order
        )
