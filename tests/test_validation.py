from dataclasses import dataclass

from office_layout.algorithms.validation import validate_layout
from office_layout.models.object_types import ObjectType
from office_layout.utils.geometry import Rect


@dataclass
class Obj:
    id: int
    type: ObjectType | None
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0
    metadata: dict | None = None


class DummyLayout:
    def __init__(self, objects, room_rect, grid_size=10.0, exit_points=None):
        self.objects = list(objects)
        self.room_rect = room_rect
        self.grid_size = float(grid_size)
        self.exit_points = list(exit_points or [])


def _codes(errors):
    return {e.code for e in errors}


def test_out_of_bounds():
    obj = Obj(1, ObjectType.DESK, 90, 90, 20, 20)
    errors = validate_layout(DummyLayout([obj], Rect(0, 0, 100, 100)))
    assert "OUT_OF_BOUNDS" in _codes(errors)


def test_collision_between_non_walls():
    a = Obj(1, ObjectType.DESK, 10, 10, 20, 20)
    b = Obj(2, ObjectType.DESK, 25, 15, 20, 20)
    errors = validate_layout(DummyLayout([a, b], Rect(0, 0, 100, 100)))
    assert "COLLISION" in _codes(errors)


def test_wall_wall_collision_is_ignored():
    w1 = Obj(1, ObjectType.WALL, 0, 20, 100, 10)
    w2 = Obj(2, ObjectType.WALL, 50, 0, 10, 40)
    errors = validate_layout(DummyLayout([w1, w2], Rect(0, 0, 100, 40)))
    assert "COLLISION" not in _codes(errors)


def test_wall_convention_collision_with_desk():
    wall = Obj(1, ObjectType.WALL, 0, 20, 100, 10)
    desk = Obj(2, ObjectType.DESK, 10, 14, 10, 10)
    errors = validate_layout(DummyLayout([wall, desk], Rect(0, 0, 100, 40)))
    assert "COLLISION" in _codes(errors)


def test_min_distance_rule_same_type_triggers_distance_too_small():
    a = Obj(1, ObjectType.DESK, 0, 0, 10, 10)
    b = Obj(2, ObjectType.DESK, 50, 0, 10, 10)
    errors = validate_layout(DummyLayout([a, b], Rect(0, 0, 200, 100)))
    assert "DISTANCE_TOO_SMALL" in _codes(errors)


def test_overcrowding_can_trigger_without_types():
    a = Obj(1, None, 0, 0, 10, 10)
    b = Obj(2, None, 10, 0, 10, 10)
    errors = validate_layout(DummyLayout([a, b], Rect(0, 0, 100, 100)))
    assert "OVER_CROWDING" in _codes(errors)


def test_no_path_to_exit_when_blocked_by_full_wall():
    wall = Obj(1, ObjectType.WALL, 50, 0, 10, 40)
    desk = Obj(2, ObjectType.DESK, 10, 10, 10, 10)
    layout = DummyLayout([wall, desk], Rect(0, 0, 100, 40), grid_size=10, exit_points=[(90, 20)])
    errors = validate_layout(layout)
    assert "NO_PATH_TO_EXIT" in _codes(errors)


def test_door_opens_path_through_wall_so_no_no_path_error():
    wall = Obj(1, ObjectType.WALL, 50, 0, 10, 40)
    door = Obj(2, ObjectType.DOOR, 45, 15, 10, 10)
    desk = Obj(3, ObjectType.DESK, 10, 10, 10, 10)
    layout = DummyLayout([wall, door, desk], Rect(0, 0, 100, 40), grid_size=10, exit_points=[(90, 20)])
    errors = validate_layout(layout)
    assert "NO_PATH_TO_EXIT" not in _codes(errors)
