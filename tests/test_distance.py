import pytest

from office_layout.utils.geometry import (
    Rect,
    cell_to_world_center,
    clamp,
    distance_point_to_rect,
    distance_points,
    distance_rect_to_rect,
    inflate_rect,
    neighbors_4,
    point_in_rect,
    rect_intersection_area,
    rect_to_covered_cells,
    rects_intersect,
    snap_point_to_grid,
    snap_value_to_grid,
    world_to_cell,
)


def test_rect_normalized_keeps_positive():
    r = Rect(1, 2, 3, 4).normalized()
    assert (r.x, r.y, r.width, r.height) == (1, 2, 3, 4)


def test_rect_normalized_flips_negative_width():
    r = Rect(10, 0, -5, 4).normalized()
    assert (r.x, r.y, r.width, r.height) == (5, 0, 5, 4)


def test_rect_normalized_flips_negative_height():
    r = Rect(0, 10, 5, -6).normalized()
    assert (r.x, r.y, r.width, r.height) == (0, 4, 5, 6)


def test_rect_normalized_flips_both():
    r = Rect(10, 10, -4, -6).normalized()
    assert (r.x, r.y, r.width, r.height) == (6, 4, 4, 6)


def test_distance_points():
    assert distance_points((0, 0), (3, 4)) == pytest.approx(5.0)


def test_clamp_inside():
    assert clamp(5, 0, 10) == 5


def test_clamp_low():
    assert clamp(-1, 0, 10) == 0


def test_clamp_high():
    assert clamp(11, 0, 10) == 10


def test_point_in_rect_inside():
    assert point_in_rect((5, 5), Rect(0, 0, 10, 10))


def test_point_in_rect_on_edge_inclusive():
    assert point_in_rect((0, 0), Rect(0, 0, 10, 10))
    assert point_in_rect((10, 10), Rect(0, 0, 10, 10))


def test_point_in_rect_outside():
    assert not point_in_rect((-0.001, 0), Rect(0, 0, 10, 10))


def test_distance_point_to_rect_inside_is_zero():
    assert distance_point_to_rect((5, 5), Rect(0, 0, 10, 10)) == pytest.approx(0.0)


def test_distance_point_to_rect_outside_horizontal():
    assert distance_point_to_rect((15, 5), Rect(0, 0, 10, 10)) == pytest.approx(5.0)


def test_rects_intersect_overlap():
    assert rects_intersect(Rect(0, 0, 10, 10), Rect(5, 5, 10, 10))


def test_rects_intersect_no_overlap():
    assert not rects_intersect(Rect(0, 0, 10, 10), Rect(20, 0, 10, 10))


def test_rects_intersect_touching_edge_is_false():
    assert not rects_intersect(Rect(0, 0, 10, 10), Rect(10, 0, 10, 10))


def test_rect_intersection_area_overlap():
    a = Rect(0, 0, 10, 10)
    b = Rect(5, 5, 10, 10)
    assert rect_intersection_area(a, b) == pytest.approx(25.0)


def test_rect_intersection_area_no_overlap():
    a = Rect(0, 0, 10, 10)
    b = Rect(20, 0, 10, 10)
    assert rect_intersection_area(a, b) == pytest.approx(0.0)


def test_inflate_rect():
    r = inflate_rect(Rect(10, 10, 20, 30), margin=5)
    assert (r.x, r.y, r.width, r.height) == (5, 5, 30, 40)


def test_distance_rect_to_rect_overlap_is_zero():
    assert distance_rect_to_rect(Rect(0, 0, 10, 10), Rect(5, 5, 10, 10)) == pytest.approx(0.0)


def test_distance_rect_to_rect_horizontal():
    assert distance_rect_to_rect(Rect(0, 0, 10, 10), Rect(25, 0, 10, 10)) == pytest.approx(15.0)


def test_distance_rect_to_rect_vertical():
    assert distance_rect_to_rect(Rect(0, 0, 10, 10), Rect(0, 30, 10, 10)) == pytest.approx(20.0)


def test_distance_rect_to_rect_diagonal():
    assert distance_rect_to_rect(Rect(0, 0, 10, 10), Rect(20, 30, 10, 10)) == pytest.approx((10**2 + 20**2) ** 0.5)


def test_snap_value_to_grid():
    assert snap_value_to_grid(23, 10) == 20
    assert snap_value_to_grid(26, 10) == 30


def test_snap_point_to_grid():
    assert snap_point_to_grid(4.9, 5.1, 10) == (0, 10)


def test_world_to_cell_basic():
    assert world_to_cell(0, 0, 10) == (0, 0)
    assert world_to_cell(9.999, 0, 10) == (0, 0)
    assert world_to_cell(10, 0, 10) == (0, 1)
    assert world_to_cell(0, 10, 10) == (1, 0)


def test_world_to_cell_invalid_grid_raises():
    with pytest.raises(ValueError):
        world_to_cell(0, 0, 0)


def test_cell_to_world_center():
    assert cell_to_world_center(0, 0, 10) == (5.0, 5.0)
    assert cell_to_world_center(2, 3, 10) == (35.0, 25.0)


def test_rect_to_covered_cells_single_cell():
    cells = rect_to_covered_cells(Rect(0, 0, 10, 10), grid=10, max_rows=10, max_cols=10)
    assert cells == [(0, 0)]


def test_rect_to_covered_cells_boundary_does_not_overflow():
    cells = rect_to_covered_cells(Rect(0, 0, 20, 10), grid=10, max_rows=10, max_cols=10)
    assert set(cells) == {(0, 0), (0, 1)}


def test_neighbors_4():
    assert neighbors_4(5, 7) == ((4, 7), (6, 7), (5, 6), (5, 8))
