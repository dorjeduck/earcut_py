from typing import List

from .node import Node


def equals(p1: Node, p2: Node) -> bool:
    """(JS: equals) Check if two nodes have equal coordinates."""
    # Use exact equality like JavaScript, not epsilon tolerance
    return p1.x == p2.x and p1.y == p2.y


def sign(num: float) -> int:
    """(JS: sign) Get the sign of a number (-1, 0, or 1)."""
    if num > 0:
        return 1
    if num < 0:
        return -1
    return 0


def area(p: Node, q: Node, r: Node) -> float:
    """(JS: area) Signed area of a triangle (p, q, r)."""
    # Cross product: (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
    return (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)


def is_collinear(p, q, r) -> bool:
    """Check if three nodes are approximately collinear (signed area is near zero)."""
    return area(p, q, r) == 0


def signed_area(data: List[float], start: int, end: int, dim: int) -> float:
    sum_val = 0.0
    j = end - dim  # Index of the last coordinate block in the ring

    # i iterates from the first coordinate index up to 'end' (exclusive), stepping by 'dim'
    for i in range(start, end, dim):
        # The sum uses data[j] and data[i] (x-coords), and data[i + 1] and data[j + 1] (y-coords)
        sum_val += (data[j] - data[i]) * (data[i + 1] + data[j + 1])
        j = i  # Update j to the current i for the next iteration (j = previous coordinate block index)

    return sum_val


# --- Intersection and Containment ---


def point_in_triangle(
    ax: float,
    ay: float,
    bx: float,
    by: float,
    cx: float,
    cy: float,
    px: float,
    py: float,
) -> bool:
    """(JS: pointInTriangle) Check if a point is inside a convex triangle."""
    # Direct translation of the JavaScript version using >= comparisons
    return (
        (cx - px) * (ay - py) >= (ax - px) * (cy - py)
        and (ax - px) * (by - py) >= (bx - px) * (ay - py)
        and (bx - px) * (cy - py) >= (cx - px) * (by - py)
    )


def point_in_triangle_except_first(
    ax: float,
    ay: float,
    bx: float,
    by: float,
    cx: float,
    cy: float,
    px: float,
    py: float,
) -> bool:
    """(JS: pointInTriangleExceptFirst) Point is in triangle, but not equal to the first vertex (ax, ay)."""
    return not (ax == px and ay == py) and point_in_triangle(
        ax, ay, bx, by, cx, cy, px, py
    )


def on_segment(p: Node, q: Node, r: Node) -> bool:
    """(JS: onSegment) For collinear points p, q, r, check if q lies on segment pr."""
    return (
        q.x <= max(p.x, r.x)
        and q.x >= min(p.x, r.x)
        and q.y <= max(p.y, r.y)
        and q.y >= min(p.y, r.y)
    )


def intersects(p1: Node, q1: Node, p2: Node, q2: Node) -> bool:
    """(JS: intersects) Check if two segments (p1, q1) and (p2, q2) intersect."""
    o1 = sign(area(p1, q1, p2))
    o2 = sign(area(p1, q1, q2))
    o3 = sign(area(p2, q2, p1))
    o4 = sign(area(p2, q2, q1))

    # General case
    if o1 != o2 and o3 != o4:
        return True

    # Special Cases (Collinear and lying on segment)
    if o1 == 0 and on_segment(p1, p2, q1):
        return True
    if o2 == 0 and on_segment(p1, q2, q1):
        return True
    if o3 == 0 and on_segment(p2, p1, q2):
        return True
    if o4 == 0 and on_segment(p2, q1, q2):
        return True

    return False


def intersects_polygon(a: Node, b: Node) -> bool:
    """(JS: intersectsPolygon) Check if diagonal (a, b) intersects any polygon segments."""
    p = a
    while True:
        # Must not check self or immediate neighbors (a.prev/a.next)
        if (
            p.i != a.i
            and p.next.i != a.i
            and p.i != b.i
            and p.next.i != b.i
            and intersects(p, p.next, a, b)
        ):
            return True
        p = p.next
        if p == a:
            break
    return False


def get_leftmost(start: Node) -> Node:
    """(JS: getLeftmost) Find the leftmost node of a polygon ring."""
    p = start
    leftmost = start
    while True:
        if p.x < leftmost.x or (p.x == leftmost.x and p.y < leftmost.y):
            leftmost = p
        p = p.next
        if p == start:
            break
    return leftmost


# --- Z-Order Curve (Bitwise Logic) ---


def z_order(x: float, y: float, minX: float, minY: float, invSize: float) -> int:
    """(JS: zOrder) Computes the Z-order curve index."""
    # Coords are transformed into non-negative 15-bit integer range
    # JS uses '| 0' for truncation. Python uses int().
    x_int = int((x - minX) * invSize)
    y_int = int((y - minY) * invSize)

    # Match JavaScript behavior - no clamping to non-negative
    x = x_int
    y = y_int

    # Spread x bits (The Magic of 0x55555555)
    x = (x | (x << 8)) & 0x00FF00FF
    x = (x | (x << 4)) & 0x0F0F0F0F
    x = (x | (x << 2)) & 0x33333333
    x = (x | (x << 1)) & 0x55555555

    # Spread y bits
    y = (y | (y << 8)) & 0x00FF00FF
    y = (y | (y << 4)) & 0x0F0F0F0F
    y = (y | (y << 2)) & 0x33333333
    y = (y | (y << 1)) & 0x55555555

    # Interleave: x bits get even positions, y bits get odd positions
    return x | (y << 1)
