from typing import List, Optional

from .node import Node, create_node
from .utils import signed_area, equals


def insert_node(i: int, x: float, y: float, last: Optional[Node]) -> Node:
    """(JS: insertNode) Create a node and link it into the circular list after 'last'."""
    p = create_node(i, x, y)

    if last is None:
        p.prev = p
        p.next = p
    else:
        # Insert p between last and last.next
        p.next = last.next
        p.prev = last
        # if last.next:
        last.next.prev = p
        last.next = p
    return p


def remove_node(p: Node) -> None:
    """(JS: removeNode) Remove a node from both the polygon ring and the Z-order list."""
    # Remove from polygon ring
    if p.next:
        p.next.prev = p.prev
    if p.prev:
        p.prev.next = p.next

    # Remove from Z-order list
    if p.prev_z:
        p.prev_z.next_z = p.next_z
    if p.next_z:
        p.next_z.prev_z = p.prev_z


def linked_list(
    data: List[float], start: int, end: int, dim: int, clockwise: bool
) -> Optional[Node]:
    """(JS: linkedList) Creates a circular doubly linked list from polygon points."""

    if end - start < dim:
        return None

    if not data:
        return None

    # Check winding using signed area
    area_sum = signed_area(data, start, end, dim)
    is_clockwise = area_sum > 0

    last = None

    # Build list in correct winding order
    if clockwise == is_clockwise:
        # Standard order
        i = start
        while i < end:
            vertex_index = i // dim
            last = insert_node(vertex_index, data[i], data[i + 1], last)
            i += dim
    else:
        # Reversed order
        i = end - dim
        while i >= start:
            vertex_index = i // dim
            last = insert_node(vertex_index, data[i], data[i + 1], last)
            i -= dim

    # Eliminate duplicate points at the start/end of the ring
    if last and last.next and equals(last, last.next):
        ##if last and equals(last, last.next):
        remove_node(last)
        last = last.next

    return last
