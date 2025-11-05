
# earcut-py

Fast, pure-Python polygon triangulation

This is a Python port of [earcut.js](https://github.com/mapbox/earcut) and [mapbox/earcut.hpp](https://github.com/mapbox/earcut.hpp), a fast polygon triangulation library.

The library implements a modified ear slicing algorithm, optimized by [z-order curve](http://en.wikipedia.org/wiki/Z-order_curve) hashing and extended to handle holes, twisted polygons, degeneracies and self-intersections in a way that doesn't guarantee correctness of triangulation, but attempts to always produce acceptable results for practical data like geographical shapes.

It's based on ideas from [FIST: Fast Industrial-Strength Triangulation of Polygons](http://www.cosy.sbg.ac.at/~held/projects/triang/triang.html) by Martin Held and [Triangulation by Ear Clipping](http://www.geometrictools.com/Documentation/TriangulationByEarClipping.pdf) by David Eberly.

## Usage

```python
from earcut_py.earcut import earcut, flatten, deviation

# Example: Triangulate a simple polygon
polygon = [10, 0, 0, 50, 60, 60, 70, 10] # [x0, y0, x1, y1, ...]
triangles = earcut(polygon)
print(triangles)  # [1, 0, 3, 3, 2, 1]

# Example: Polygon with holes

triangles = earcut([0,0, 100,0, 100,100, 0,100,  20,20, 80,20, 80,80, 20,80], [4]);
print(triangles)
# [0, 4, 7, 5, 4, 0, 3, 0, 7, 5, 0, 1, 2, 3, 7, 6, 5, 1, 2, 7, 6, 6, 1, 2]
# Note: an earlier example in the upstream JS README shows a slightly different
# triangulation for this case. That example and the output here are both valid —
# the polygon region in question is ambiguous and admits two correct diagonals.
# The current upstream JavaScript implementation and this Python port produce
# the same triangulation when run today.


# Calculate deviation (area error)
err = deviation(flat['vertices'], flat['holes'], flat['dimensions'], triangles)
print(f"Deviation: {err}")
```

## License

MIT License. See [LICENSE](./LICENSE) for details.

---

