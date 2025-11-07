"""Query operations and partial ordering utilities."""



class PartialOrder:
    """
    Utility class for partial ordering operations on (x, y) coordinate pairs.

    Implements partial ordering where (x, y) < (x₁, y₁) if and only if:
    - x < x₁ (earlier issue), OR
    - x == x₁ AND y < y₁ (same issue, earlier stage)
    """

    @staticmethod
    def less_than(coord1: tuple[int, int], coord2: tuple[int, int]) -> bool:
        """
        Check if coord1 < coord2 in partial order.

        Args:
            coord1: First coordinate (x, y)
            coord2: Second coordinate (x, y)

        Returns:
            True if coord1 < coord2 in partial ordering
        """
        x1, y1 = coord1
        x2, y2 = coord2
        return x1 < x2 or (x1 == x2 and y1 < y2)

    @staticmethod
    def less_equal(coord1: tuple[int, int], coord2: tuple[int, int]) -> bool:
        """
        Check if coord1 <= coord2 in partial order.

        Args:
            coord1: First coordinate (x, y)
            coord2: Second coordinate (x, y)

        Returns:
            True if coord1 <= coord2 in partial ordering
        """
        return coord1 == coord2 or PartialOrder.less_than(coord1, coord2)

    @staticmethod
    def comparable(coord1: tuple[int, int], coord2: tuple[int, int]) -> bool:
        """
        Check if coord1 and coord2 are comparable.

        Two coordinates are comparable if one is less than or equal to the other.

        Args:
            coord1: First coordinate (x, y)
            coord2: Second coordinate (x, y)

        Returns:
            True if coordinates are comparable
        """
        return PartialOrder.less_equal(coord1, coord2) or PartialOrder.less_equal(coord2, coord1)

    @staticmethod
    def find_before(
        coords: list[tuple[int, int, int]], threshold: tuple[int, int]
    ) -> list[tuple[int, int, int]]:
        """
        Find all coordinates where (x,y) < threshold in partial order.

        Args:
            coords: List of coordinate tuples (x, y, z)
            threshold: Threshold (x, y) values

        Returns:
            List of coordinates before threshold, sorted
        """
        x_threshold, y_threshold = threshold
        results = []

        for coord in coords:
            x, y, z = coord
            # Check partial ordering: (x,y) < (x_threshold, y_threshold)
            if PartialOrder.less_than((x, y), (x_threshold, y_threshold)):
                results.append(coord)

        return sorted(results)
