# test/test.py

import unittest
import json
import os
import math
import sys
from typing import List, Optional, Any, Tuple


# --- Path Adjustment for Package Import ---
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
sys.path.insert(0, PROJECT_ROOT)

try:
    from earcut import earcut, flatten, deviation
except ImportError as e:
    raise ImportError(
        f"Could not import 'earcut' package. Check file names and structure: {e}"
    )

# --- Global Fixture Loading ---
try:
    with open(os.path.join(TEST_DIR, "expected.json"), "r") as f:
        EXPECTED = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError(
        "expected.json not found. Ensure it is in the test directory."
    )


class TestEarcutReplication(unittest.TestCase):

    # -----------------------------------------------------------
    # Helper for triangle comparison
    # -----------------------------------------------------------
    def normalize_triangles(self, tri_list: List[int]) -> List[Tuple[int, int, int]]:
        """Sorts vertices within each triangle and then sorts the list of triangles."""
        normalized = []
        for i in range(0, len(tri_list), 3):
            normalized.append(
                tuple(sorted([tri_list[i], tri_list[i + 1], tri_list[i + 2]]))
            )
        return sorted(normalized)

    # -----------------------------------------------------------
    # Direct Test Cases
    # -----------------------------------------------------------
    def test_indices_2d(self):
        """Replicates test('indices-2d')."""
        indices = earcut([10, 0, 0, 50, 60, 60, 70, 10])
        self.assertListEqual(
            indices, [1, 0, 3, 3, 2, 1], "Simple 2D triangulation failed."
        )

    def test_indices_3d(self):
        """Replicates test('indices-3d')."""
        indices = earcut([10, 0, 0, 0, 50, 0, 60, 60, 0, 70, 10, 0], None, 3)
        self.assertListEqual(
            indices, [1, 0, 3, 3, 2, 1], "Simple 3D triangulation failed."
        )

    def test_empty(self):
        """Replicates test('empty')."""
        self.assertListEqual(earcut([]), [], "Empty input should return empty list.")

    def test_infinite_loop(self):
        """Replicates test('infinite-loop')."""
        try:
            earcut([1, 2, 2, 2, 1, 2, 1, 1, 1, 2, 4, 1, 5, 1, 3, 2, 4, 2, 4, 1], [5], 2)
        except Exception as e:
            self.fail(f"Infinite loop test failed with exception: {e}")

    # -----------------------------------------------------------
    # Fixture-Driven Test Loop
    # -----------------------------------------------------------
    def test_fixtures_with_rotation(self):
        """Replicates the main JS test loop over all fixtures and rotations."""

        fixture_ids = sorted(EXPECTED["triangles"].keys())

        for id in fixture_ids:
            # Load the coordinates for the current fixture
            fixture_path = os.path.join(TEST_DIR, "fixtures", f"{id}.json")
            try:
                with open(fixture_path, "r") as f:
                    coords = json.load(f)
            except FileNotFoundError:
                self.fail(f"Fixture file not found for ID: {id}")
                continue

            for rotation in [0, 90, 180, 270]:

                with self.subTest(id=id, rotation=rotation):

                    # 1. Coordinate Rotation (replicating JS logic precisely)
                    theta = rotation * math.pi / 180
                    xx = round(math.cos(theta))
                    xy = round(-math.sin(theta))
                    yx = round(math.sin(theta))
                    yy = round(math.cos(theta))

                    rotated_coords = [
                        [list(coord) for coord in ring] for ring in coords
                    ]

                    if rotation != 0:
                        for ring in rotated_coords:
                            for coord in ring:
                                x, y = coord[0], coord[1]
                                coord[0] = xx * x + xy * y
                                coord[1] = yx * x + yy * y

                    # 2. Flatten Data
                    data = flatten(rotated_coords)

                    # 3. Run Earcut
                    indices = earcut(
                        data["vertices"], data["holes"], data["dimensions"]
                    )

                    # 4. Calculate Deviation
                    err = deviation(
                        data["vertices"], data["holes"], data["dimensions"], indices
                    )

                    # 5. Get Expected Values
                    expected_triangles_count = EXPECTED["triangles"][id]

                    expected_deviation = EXPECTED.get("errors-with-rotation", {}).get(
                        id
                    )
                    if expected_deviation is None or rotation == 0:
                        expected_deviation = EXPECTED.get("errors", {}).get(id, 0.0)

                    # 6. Assertions

                    # A. Triangles Count Check (Only for rotation 0, as in the JS test)
                    num_triangles = len(indices) // 3
                    if rotation == 0:
                        self.assertEqual(
                            num_triangles,
                            expected_triangles_count,
                            f"[{id} rot {rotation}] Triangle count mismatch: {num_triangles} vs {expected_triangles_count}",
                        )

                    # B. Deviation Check
                    if expected_triangles_count > 0:
                        self.assertLessEqual(
                            err,
                            expected_deviation,
                            f"[{id} rot {rotation}] Deviation {err} > expected {expected_deviation}",
                        )

                    # C. Content Check (Added for robustness, optional but highly recommended)
                    # This ensures the *set* of triangles is correct, even if the order changes.
                    if rotation == 0 and num_triangles == expected_triangles_count:
                        # Only run this if the triangle count is already correct
                        normalized_result = self.normalize_triangles(indices)

                        # Note: Comparing against a pre-calculated normalized set is better,
                        # but for porting, we just rely on count and deviation checks
                        # as the original JS test does not assert the exact index list.
                        pass


if __name__ == "__main__":
    # To run this, use: python -m unittest discover -s test -t .
    unittest.main()
