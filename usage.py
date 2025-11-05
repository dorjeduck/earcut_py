from earcut import earcut, flatten, deviation

# Example: Triangulate a simple polygon
polygon = [10, 0, 0, 50, 60, 60, 70, 10]  # flat list: [x0, y0, x1, y1, ...]
triangles = earcut(polygon)
print(triangles)  # [1, 0, 3, 3, 2, 1]

# Example: Polygon with holes

triangles_2 = earcut(
    [0, 0, 100, 0, 100, 100, 0, 100, 20, 20, 80, 20, 80, 80, 20, 80], [4]
)
print(triangles_2)
# [0, 4, 7, 5, 4, 0, 3, 0, 7, 5, 0, 1, 2, 3, 7, 6, 5, 1, 2, 7, 6, 6, 1, 2]

triangles_3 = earcut([10, 0, 1, 0, 50, 2, 60, 60, 3, 70, 10, 4], None, 3)
print(triangles_3)
# [1, 0, 3, 3, 2, 1]
