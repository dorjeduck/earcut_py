import math
from typing import List, Optional, Dict, Any, Union

from .list import linked_list
from .node import Node, create_node
from .utils import (
    area,
    equals,
    intersects,
    intersects_polygon,
    is_collinear,
    get_leftmost,
    point_in_triangle,
    point_in_triangle_except_first,
    signed_area,
    z_order,
)

# Note: remove_node is assumed to be imported from .list alongside linked_list.
from .list import remove_node


# --- Auxiliary Export Functions ---


def flatten(data: List[List[Any]]) -> Dict[str, Any]:
    """
    (JS: flatten) turn a polygon in a multi-dimensional array form (e.g. as in GeoJSON)
    into a form Earcut accepts (flat list of vertices, list of hole indices).
    """
    vertices: List[float] = []
    holes: List[int] = []
    dimensions = 0
    hole_index = 0
    prev_len = 0

    if (
        not data
        or not isinstance(data[0], (list, tuple))
        or not isinstance(data[0][0], (list, tuple))
    ):
        return {"vertices": [], "holes": None, "dimensions": 2}

    dimensions = len(data[0][0])

    for ring in data:
        if not isinstance(ring, (list, tuple)):
            continue

        for p in ring:
            if not isinstance(p, (list, tuple)):
                continue

            if len(p) >= dimensions:
                for d in range(dimensions):
                    vertices.append(p[d])

        if prev_len:
            hole_index += prev_len
            holes.append(hole_index)
        prev_len = len(ring)

    return {
        "vertices": vertices,
        "holes": holes if len(holes) > 0 else None,
        "dimensions": dimensions,
    }


def filter_points(start: Optional[Node], end: Optional[Node] = None) -> Optional[Node]:
    """
    (JS: filterPoints) Eliminate colinear or duplicate points from a list ring.
    """
    if start is None:
        return start
    if end is None:
        end = start

    p = start
    again = True

    while again or p != end:
        again = False

        if not p.steiner and (equals(p, p.next) or area(p.prev, p, p.next) == 0):
            remove_node(p)
            p = end = p.prev
            if p == p.next:
                break
            again = True
        else:
            p = p.next

    return end


# --- Z-Order Curve Indexing and Sorting ---


def index_curve(start: Node, min_x: float, min_y: float, inv_size: float) -> None:
    """(JS: indexCurve) Interlink polygon nodes in z-order."""
    p = start
    while True:
        if p.z == 0:
            p.z = z_order(p.x, p.y, min_x, min_y, inv_size)

        p.prev_z = p.prev
        p.next_z = p.next
        p = p.next

        if p == start:
            break

    if p.prev_z:
        p.prev_z.next_z = None
    p.prev_z = None

    sort_linked(p)


def sort_linked(list_head: Node) -> Optional[Node]:
    """
    (JS: sortLinked) Simon Tatham's linked list merge sort algorithm
    to sort nodes by their z-order value (p.z).
    """
    num_merges = 0
    in_size = 1

    list_result = None

    while True:
        p = list_head
        list_head = None
        tail = None
        num_merges = 0

        while p:
            num_merges += 1

            q = p
            p_size = 0
            for _ in range(in_size):
                p_size += 1
                q = q.next_z
                if not q:
                    break
            q_size = in_size

            while p_size > 0 or (q_size > 0 and q):

                if p_size != 0 and (q_size == 0 or not q or p.z <= q.z):
                    e = p
                    p = p.next_z
                    p_size -= 1
                else:
                    e = q
                    q = q.next_z
                    q_size -= 1

                if tail:
                    tail.next_z = e
                else:
                    list_head = e

                e.prev_z = tail
                tail = e

            p = q

        if tail:
            tail.next_z = None
        in_size *= 2

        if num_merges <= 1:
            break

    return list_head


# --- Ear Check Logic ---


def is_ear(ear: Node) -> bool:
    """(JS: isEar) Check whether a polygon node forms a valid ear."""
    a, b, c = ear.prev, ear, ear.next

    if area(a, b, c) >= 0:
        return False

    ax, bx, cx = a.x, b.x, c.x
    ay, by, cy = a.y, b.y, c.y

    x0, y0 = min(ax, bx, cx), min(ay, by, cy)
    x1, y1 = max(ax, bx, cx), max(ay, by, cy)

    p = c.next
    while p != a:
        if (
            p.x >= x0
            and p.x <= x1
            and p.y >= y0
            and p.y <= y1
            and point_in_triangle_except_first(ax, ay, bx, by, cx, cy, p.x, p.y)
            and area(p.prev, p, p.next) >= 0
        ):
            return False
        p = p.next

    return True


# --- Ear Check Optimization ---


def is_ear_hashed(ear: Node, min_x: float, min_y: float, inv_size: float) -> bool:
    """(JS: isEarHashed) Optimized ear check using Z-order curve indexing."""
    a, b, c = ear.prev, ear, ear.next

    if area(a, b, c) >= 0:
        return False

    ax, bx, cx = a.x, b.x, c.x
    ay, by, cy = a.y, b.y, c.y

    x0, y0 = min(ax, bx, cx), min(ay, by, cy)
    x1, y1 = max(ax, bx, cx), max(ay, by, cy)

    min_z = z_order(x0, y0, min_x, min_y, inv_size)
    max_z = z_order(x1, y1, min_x, min_y, inv_size)

    p, n = ear.prev_z, ear.next_z

    while p and p.z >= min_z and n and n.z <= max_z:
        if (
            p.x >= x0
            and p.x <= x1
            and p.y >= y0
            and p.y <= y1
            and p != a
            and p != c
            and point_in_triangle_except_first(ax, ay, bx, by, cx, cy, p.x, p.y)
            and area(p.prev, p, p.next) >= 0
        ):
            return False
        p = p.prev_z

        if (
            n.x >= x0
            and n.x <= x1
            and n.y >= y0
            and n.y <= y1
            and n != a
            and n != c
            and point_in_triangle_except_first(ax, ay, bx, by, cx, cy, n.x, n.y)
            and area(n.prev, n, n.next) >= 0
        ):
            return False
        n = n.next_z

    while p and p.z >= min_z:
        if (
            p.x >= x0
            and p.x <= x1
            and p.y >= y0
            and p.y <= y1
            and p != a
            and p != c
            and point_in_triangle_except_first(ax, ay, bx, by, cx, cy, p.x, p.y)
            and area(p.prev, p, p.next) >= 0
        ):
            return False
        p = p.prev_z

    while n and n.z <= max_z:
        if (
            n.x >= x0
            and n.x <= x1
            and n.y >= y0
            and n.y <= y1
            and n != a
            and n != c
            and point_in_triangle_except_first(ax, ay, bx, by, cx, cy, n.x, n.y)
            and area(n.prev, n, n.next) >= 0
        ):
            return False
        n = n.next_z

    return True


# --- Diagonal and Intersection Helpers ---


def locally_inside(a: Node, b: Node) -> bool:
    """
    (JS: locallyInside) Check if a diagonal (a, b) is locally inside the polygon at vertex 'a'.
    """
    if area(a.prev, a, a.next) < 0:
        return area(a, b, a.next) >= 0 and area(a, a.prev, b) >= 0
    else:
        return area(a, b, a.prev) < 0 or area(a, a.next, b) < 0


def middle_inside(a: Node, b: Node) -> bool:
    """
    (JS: middleInside) Check if the middle point of a diagonal (a, b) is inside the polygon.
    """
    p = a
    inside = False
    px, py = (a.x + b.x) / 2, (a.y + b.y) / 2

    while True:
        if (
            ((p.y > py) != (p.next.y > py))
            and p.next.y != p.y
            and (px < (p.next.x - p.x) * (py - p.y) / (p.next.y - p.y) + p.x)
        ):
            inside = not inside

        p = p.next
        if p == a:
            break

    return inside


def sector_contains_sector(m: Node, p: Node) -> bool:
    """
    (JS: sectorContainsSector) Whether sector in vertex m contains sector in vertex p.
    """
    return area(m.prev, m, p.prev) < 0 and area(p.next, m, m.next) < 0


def is_valid_diagonal(a: Node, b: Node) -> bool:
    """
    (JS: isValidDiagonal) Check if a diagonal between two polygon nodes is valid.
    """
    cond1 = a.next.i != b.i and a.prev.i != b.i and not intersects_polygon(a, b)
    cond2 = (
        locally_inside(a, b)
        and locally_inside(b, a)
        and middle_inside(a, b)
        and (
            area(a.prev, a, b.prev)
            or area(a, b.prev, b)
            or (
                equals(a, b)
                and area(a.prev, a, a.next) > 0
                and area(b.prev, b, b.next) > 0
            )
        )
    )
    result = cond1 and cond2

    return result


# --- Polygon Modification ---


def split_polygon(a: Node, b: Node) -> Node:
    """
    (JS: splitPolygon) Link two vertices (a, b) with a bridge.
    Returns the head of the new ring created.
    """
    a2 = create_node(a.i, a.x, a.y)
    b2 = create_node(b.i, b.x, b.y)

    an, bp = a.next, b.prev

    a.next = b
    b.prev = a

    a2.next = an
    an.prev = a2

    b2.next = a2
    a2.prev = b2

    bp.next = b2
    b2.prev = bp

    return b2


# --- Last Resort Logic ---


def cure_local_intersections(start: Node, triangles: List[int]) -> Node:
    """(JS: cureLocalIntersections) Go through nodes and cure small local self-intersections."""
    p = start
    while True:
        a = p.prev
        b = p.next.next

        if (
            not equals(a, b)
            and intersects(a, p, p.next, b)
            and locally_inside(a, b)
            and locally_inside(b, a)
        ):

            triangles.extend([a.i, p.i, b.i])

            remove_node(p)
            remove_node(p.next)

            p = start = b

        p = p.next
        if p == start:
            break

    return filter_points(p)


def split_earcut(
    start: Node,
    triangles: List[int],
    dim: int,
    min_x: float,
    min_y: float,
    inv_size: float,
) -> None:
    """(JS: splitEarcut) Try splitting the remaining polygon into two and triangulate independently."""
    a = start
    while True:
        b = a.next.next
        while b != a.prev:

            if a.i != b.i and is_valid_diagonal(a, b):
                c = split_polygon(a, b)

                a = filter_points(a, a.next)
                c = filter_points(c, c.next)

                earcut_linked(a, triangles, dim, min_x, min_y, inv_size, 0)
                earcut_linked(c, triangles, dim, min_x, min_y, inv_size, 0)
                return

            b = b.next

        a = a.next
        if a == start:
            break


# --- Hole Processing Helpers ---


def compare_xy_slope(a: Node, b: Node) -> float:
    result = a.x - b.x
    if result == 0:
        result = a.y - b.y
        if result == 0:
            a_slope = (a.next.y - a.y) / (a.next.x - a.x)
            b_slope = (b.next.y - b.y) / (b.next.x - b.x)
            result = a_slope - b_slope
    return result


def compare_xy_slope_2(a: Node, b: Node) -> float:
    """JavaScript-exact compareXYSlope function for hole sorting."""
    result = a.x - b.x
    if result == 0:
        result = a.y - b.y
        if result == 0:
            # JavaScript division behavior: handle zero denominator
            def js_divide(dy: float, dx: float) -> float:
                if dx == 0:
                    return (
                        float("inf")
                        if dy > 0
                        else float("-inf") if dy < 0 else float("nan")
                    )
                return dy / dx

            a_slope = js_divide(a.next.y - a.y, a.next.x - a.x)
            b_slope = js_divide(b.next.y - b.y, b.next.x - b.x)
            result = a_slope - b_slope

    return result


def eliminate_hole(hole: Node, outer_node: Node) -> Node:
    """
    (JS: eliminateHole) Finds a bridge between hole and outer polygon and links it.
    """
    bridge = find_hole_bridge(hole, outer_node)
    if bridge is None:
        return outer_node

    bridge_reverse = split_polygon(bridge, hole)

    filter_points(bridge_reverse, bridge_reverse.next)
    return filter_points(bridge, bridge.next)


def find_hole_bridge(hole: Node, outer_node: Node) -> Optional[Node]:
    """
    (JS: findHoleBridge) David Eberly's algorithm for finding the shortest valid
    bridge between a hole's leftmost point and the outer polygon.
    """
    p = outer_node
    hx, hy = hole.x, hole.y
    qx = -float("inf")
    m = None

    if equals(hole, p):
        return p

    while True:
        if equals(hole, p.next):
            return p.next

        elif hy <= p.y and hy >= p.next.y and p.next.y != p.y:
            x = p.x + (hy - p.y) * (p.next.x - p.x) / (p.next.y - p.y)

            if x <= hx and x > qx:
                qx = x
                m = p if p.x < p.next.x else p.next
                if x == hx:
                    return m

        p = p.next
        if p == outer_node:
            break

    if m is None:
        return None

    stop = m
    mx, my = m.x, m.y
    tan_min = float("inf")

    p = m
    while True:
        if (
            hx >= p.x
            and p.x >= mx
            and hx != p.x
            and point_in_triangle(
                hx if hy < my else qx, hy, mx, my, qx if hy < my else hx, hy, p.x, p.y
            )
        ):

            tan = math.fabs(hy - p.y) / (hx - p.x)

            if locally_inside(p, hole) and (
                tan < tan_min
                or (
                    tan == tan_min
                    and (p.x > m.x or (p.x == m.x and sector_contains_sector(m, p)))
                )
            ):
                m = p
                tan_min = tan

        p = p.next
        if p == stop:
            break

    return m


def eliminate_holes(
    data: List[float], hole_indices: List[int], outer_node: Node, dim: int
) -> Node:
    """
    (JS: eliminateHoles) Link every hole into the outer loop, producing a single-ring polygon.
    """
    queue: List[Node] = []
    len_holes = len(hole_indices)

    for i in range(len_holes):
        start = hole_indices[i] * dim
        end = hole_indices[i + 1] * dim if i < len_holes - 1 else len(data)

        list_head = linked_list(data, start, end, dim, False)

        if list_head is None:
            continue

        if list_head == list_head.next:
            list_head.steiner = True

        queue.append(get_leftmost(list_head))

    # Use functools.cmp_to_key to convert comparison function to key function
    from functools import cmp_to_key

    queue.sort(key=cmp_to_key(compare_xy_slope))

    for hole_node in queue:
        outer_node = eliminate_hole(hole_node, outer_node)

    return outer_node


# --- Main Earcut Functions ---


def earcut_linked(
    ear: Optional[Node],
    triangles: List[int],
    dim: int,
    min_x: float,
    min_y: float,
    inv_size: float,
    pass_num: int,
) -> None:
    """
    (JS: earcutLinked) Main ear slicing loop which triangulates a polygon.
    """
    if not ear:
        return

    if pass_num == 0 and inv_size != 0.0:
        index_curve(ear, min_x, min_y, inv_size)

    stop = ear

    while ear.prev != ear.next:
        prev, next_node = ear.prev, ear.next

        # Use hashed ear detection for large datasets, regular ear detection otherwise
        if inv_size != 0.0:
            is_valid_ear = is_ear_hashed(ear, min_x, min_y, inv_size)
        else:
            is_valid_ear = is_ear(ear)

        if is_valid_ear:
            triangles.extend([prev.i, ear.i, next_node.i])

            remove_node(ear)

            ear = next_node.next
            stop = next_node.next

            continue

        ear = next_node

        if ear == stop:
            if pass_num == 0:
                ear = filter_points(ear)
                if ear:
                    earcut_linked(ear, triangles, dim, min_x, min_y, inv_size, 1)

            elif pass_num == 1:
                ear = cure_local_intersections(ear, triangles)
                if ear:
                    earcut_linked(ear, triangles, dim, min_x, min_y, inv_size, 2)

            elif pass_num == 2:
                split_earcut(ear, triangles, dim, min_x, min_y, inv_size)

            break


def earcut(
    data: List[float], hole_indices: Optional[List[int]] = None, dim: int = 2
) -> List[int]:
    """
    (JS: export default function earcut)
    Main Earcut function to triangulate a polygon with optional holes.
    """

    has_holes = hole_indices is not None and len(hole_indices) > 0
    outer_len = (
        hole_indices[0] * dim if has_holes and len(hole_indices) > 0 else len(data)
    )

    outer_node = linked_list(data, 0, outer_len, dim, True)
    triangles: List[int] = []

    if outer_node is None or outer_node.next == outer_node.prev:
        return triangles

    min_x, min_y, inv_size = 0.0, 0.0, 0.0

    if has_holes:
        outer_node = eliminate_holes(data, hole_indices, outer_node, dim)

    if len(data) > 80 * dim:
        min_x, min_y = data[0], data[1]
        max_x, max_y = min_x, min_y

        i = dim
        while i < outer_len:
            x, y = data[i], data[i + 1]
            min_x, min_y = min(min_x, x), min(min_y, y)
            max_x, max_y = max(max_x, x), max(max_y, y)
            i += dim

        inv_size = max(max_x - min_x, max_y - min_y)
        inv_size = 32767 / inv_size if inv_size != 0 else 0.0

    earcut_linked(outer_node, triangles, dim, min_x, min_y, inv_size, 0)

    return triangles


def deviation(
    data: List[float], hole_indices: Optional[List[int]], dim: int, triangles: List[int]
) -> float:
    """
    (JS: export function deviation)
    Return a percentage difference between the polygon area and its triangulation area.
    """
    has_holes = hole_indices is not None and len(hole_indices) > 0
    outer_len = (
        hole_indices[0] * dim if has_holes and len(hole_indices) > 0 else len(data)
    )

    polygon_area = math.fabs(signed_area(data, 0, outer_len, dim))
    if has_holes:
        len_holes = len(hole_indices)
        for i in range(len_holes):
            start = hole_indices[i] * dim
            end = hole_indices[i + 1] * dim if i < len_holes - 1 else len(data)
            polygon_area -= math.fabs(signed_area(data, start, end, dim))

    triangles_area = 0.0
    i = 0
    while i < len(triangles):
        a = triangles[i] * dim
        b = triangles[i + 1] * dim
        c = triangles[i + 2] * dim

        triangles_area += math.fabs(
            (data[a] - data[c]) * (data[b + 1] - data[a + 1])
            - (data[a] - data[b]) * (data[c + 1] - data[a + 1])
        )
        i += 3

    return (
        0.0
        if polygon_area == 0 and triangles_area == 0
        else math.fabs((triangles_area - polygon_area) / polygon_area)
    )
