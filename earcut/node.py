from typing import Optional


class Node:
    """A single vertex in the circular doubly linked list, used by Earcut."""

    def __init__(self, i: int, x: float, y: float):
        # Vertex properties
        self.i = i  # Vertex index in the coordinates array
        self.x = x  # Vertex x coordinate
        self.y = y  # Vertex y coordinate

        # Polygon ring pointers (for polygon traversal)
        self.prev: Optional["Node"] = None
        self.next: Optional["Node"] = None

        # Z-order curve properties (for fast intersection checks)
        self.z: int = 0
        self.prev_z: Optional["Node"] = None
        self.next_z: Optional["Node"] = None

        # Flag for Steiner points (used in eliminateHoles, defaults to False)
        self.steiner: bool = False


# Function alias for clarity, matching the JS structure
def create_node(i: int, x: float, y: float) -> Node:
    """Factory function for a new Node."""
    return Node(i, x, y)
