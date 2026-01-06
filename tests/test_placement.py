from dataclasses import dataclass
from math import sqrt
import pytest

from office_layout.algorithms import placement
from office_layout.algorithms.placement import (
    Rect,
    collides,
    fits_in_room,
    distance_between,
    snap_to_grid,
    can_place_object,
    move_object,
)


@dataclass
class Obj:
    id: str
    x: float
    y: float
    width: float
    height: float


class DummyLayout:
    def __init__(self, objects, room_rect, min_clearance=0.0):
        self._objects = list(objects)
        self.room_rect = room_rect
        self.min_clearance = min_clearance

    def get_object(self, obj_id):
        for o in self._objects:
            if getattr(o, "id", None) == obj_id:
                return o
        raise KeyError(obj_id)


def test_to_rect_from_rect():
    r = Rect(0, 0, 10, 20)
    assert placement._to_rect(r) == r


def test_to_rect_from_dict():
    out = placement._to_rect({"x": 1, "y": 2, "width": 3, "height": 4})
    assert (out.x, out.y, out.width, out.height) == (1.0, 2.0, 3.0, 4.0)


def test_to_rect_from_object():
    o = Obj("a", 5, 6, 7, 8)
    out = placement._to_rect(o)
    assert (out.x, out.y, out.width, out.height) == (5.0, 6.0, 7.0, 8.0)


def test_collides_overlap():
    assert collides(Rect(0, 0, 10, 10), Rect(5, 5, 10, 10))


def test_collides_no_overlap():
    assert not collides(Rect(0, 0, 10, 10), Rect(20, 0, 10, 10))


def test_collides_touching_edge_not():
    assert not collides(Rect(0, 0, 10, 10), Rect(10, 0, 10, 10))


def test_fits_in_room_true():
    assert fits_in_room(Rect(10, 10, 20, 20), Rect(0, 0, 100, 100))


def test_fits_in_room_false():
    assert not fits_in_room(Rect(90, 90, 20, 20), Rect(0, 0, 100, 100))


def test_distance_between_overlap():
    assert distance_between(Rect(0, 0, 10, 10), Rect(5, 5, 10, 10)) == 0.0


def test_distance_between_horizontal():
    assert distance_between(Rect(0, 0, 10, 10), Rect(20, 0, 10, 10)) == pytest.approx(10.0)


def test_distance_between_diagonal():
    assert distance_between(Rect(0, 0, 10, 10), Rect(20, 30, 10, 10)) == pytest.approx(sqrt(500))


def test_snap_to_grid_basic():
    assert snap_to_grid(23, 27, 10) == (20, 30)


def test_snap_to_grid_rounding():
    assert snap_to_grid(4.9, 5.1, 10) == (0, 10)


def test_can_place_outside_room():
    layout = DummyLayout([], Rect(0, 0, 100, 100))
    ok, _ = can_place_object(layout, Rect(95, 95, 20, 20))
    assert not ok


def test_can_place_collision():
    existing = Obj("a", 10, 10, 20, 20)
    layout = DummyLayout([existing], Rect(0, 0, 100, 100))
    ok, _ = can_place_object(layout, Rect(15, 15, 20, 20))
    assert not ok


def test_can_place_too_close():
    existing = Obj("a", 10, 10, 10, 10)
    layout = DummyLayout([existing], Rect(0, 0, 100, 100), min_clearance=15)
    ok, _ = can_place_object(layout, Rect(25, 10, 10, 10))
    assert not ok


def test_can_place_valid():
    existing = Obj("a", 10, 10, 10, 10)
    layout = DummyLayout([existing], Rect(0, 0, 100, 100), min_clearance=5)
    ok, _ = can_place_object(layout, Rect(30, 10, 10, 10))
    assert ok


def test_move_object_success():
    obj = Obj("a", 10, 10, 10, 10)
    layout = DummyLayout([obj], Rect(0, 0, 100, 100))
    ok, _ = move_object(layout, "a", 50, 50)
    assert ok
    assert (obj.x, obj.y) == (50.0, 50.0)


def test_move_object_collision():
    obj1 = Obj("a", 10, 10, 10, 10)
    obj2 = Obj("b", 40, 10, 10, 10)
    layout = DummyLayout([obj1, obj2], Rect(0, 0, 100, 100))
    ok, _ = move_object(layout, "a", 38, 10)
    assert not ok
    assert (obj1.x, obj1.y) == (10.0, 10.0)


def test_move_object_id_not_found():
    layout = DummyLayout([], Rect(0, 0, 100, 100))
    ok, msg = move_object(layout, "missing", 10, 10)
    assert not ok
    assert "missing" in msg
