from dataclasses import dataclass
from office_layout.algorithms.validation import validate_layout
from office_layout.algorithms.placement import Rect


# Simple object for validation tests
@dataclass
class Obj:
    id: str
    x: float
    y: float
    width: float
    height: float


# Minimal layout used to test validation logic
class DummyLayoutValidation:
    def __init__(
        self,
        objects,
        room_rect,
        min_clearance=0.0,
        min_distance_wall=0.0,
        min_corridor_width=0.0,
        access_points=None,
    ):
        self.objects = list(objects)
        self.room_rect = room_rect
        self.min_clearance = min_clearance
        self.min_distance_wall = min_distance_wall
        self.min_corridor_width = min_corridor_width
        self.access_points = access_points or []


def _codes(errors):
    return {e.code for e in errors}


def test_out_of_bounds():
    obj = Obj("a", 90, 90, 20, 20)
    errors = validate_layout(DummyLayoutValidation([obj], Rect(0, 0, 100, 100)))
    assert "OUT_OF_BOUNDS" in _codes(errors)


def test_collision():
    a = Obj("a", 10, 10, 20, 20)
    b = Obj("b", 25, 15, 20, 20)
    errors = validate_layout(DummyLayoutValidation([a, b], Rect(0, 0, 100, 100)))
    assert "COLLISION" in _codes(errors)


def test_min_distance_and_overcrowding():
    a = Obj("a", 10, 10, 10, 10)
    b = Obj("b", 25, 10, 10, 10)
    errors = validate_layout(DummyLayoutValidation([a, b], Rect(0, 0, 100, 100), min_clearance=10))
    codes = _codes(errors)
    assert "DISTANCE_TOO_SMALL" in codes
    assert "OVER_CROWDING" in codes


def test_wall_distance():
    obj = Obj("a", 1, 20, 10, 10)
    errors = validate_layout(DummyLayoutValidation([obj], Rect(0, 0, 100, 100), min_distance_wall=5))
    assert "WALL_DISTANCE" in _codes(errors)


def test_overcrowding_default_threshold():
    a = Obj("a", 10, 10, 10, 10)
    b = Obj("b", 25, 10, 10, 10)
    errors = validate_layout(DummyLayoutValidation([a, b], Rect(0, 0, 200, 200)))
    assert "OVER_CROWDING" in _codes(errors)


def test_no_path_between_access_points():
    block = Obj("block", 20, 0, 60, 40)
    layout = DummyLayoutValidation(
        [block],
        Rect(0, 0, 100, 40),
        access_points=[(10, 20), (90, 20)],
    )
    errors = validate_layout(layout)
    assert "NO_PATH" in _codes(errors)
