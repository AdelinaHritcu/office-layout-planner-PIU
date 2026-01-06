from dataclasses import dataclass

from office_layout.algorithms.routing import (
    _astar_path,
    _build_occupancy_grid,
    _nearest_free_cell,
    find_shortest_path_to_exit,
)
from office_layout.models.object_types import ObjectType
from office_layout.utils.geometry import world_to_cell


@dataclass
class Obj:
    id: int
    type: ObjectType
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0
    metadata: dict | None = None


class DummyLayout:
    def __init__(self, objects, room_w=100.0, room_h=40.0, grid_size=10.0, exit_points=None):
        self.room_width = float(room_w)
        self.room_height = float(room_h)
        self.grid_size = float(grid_size)
        self._objects = {o.id: o for o in objects}
        self.exit_points = list(exit_points or [])

    def all_objects(self):
        return list(self._objects.values())


def test_astar_path_simple_line():
    grid = [[0] * 5 for _ in range(5)]
    path = _astar_path(grid, (0, 0), (0, 4))
    assert path is not None
    assert path[0] == (0, 0)
    assert path[-1] == (0, 4)
    assert len(path) == 5


def test_astar_path_blocked_goal_returns_none():
    grid = [[0] * 5 for _ in range(5)]
    grid[0][4] = 1
    assert _astar_path(grid, (0, 0), (0, 4)) is None


def test_nearest_free_cell_returns_same_if_free():
    grid = [[0, 0], [0, 0]]
    assert _nearest_free_cell(grid, (1, 1)) == (1, 1)


def test_nearest_free_cell_finds_neighbor_when_blocked():
    grid = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    c = _nearest_free_cell(grid, (1, 1), max_radius=1)
    assert c is not None
    assert c != (1, 1)


def test_build_grid_marks_desk_as_obstacle_but_not_door():
    desk = Obj(1, ObjectType.DESK, 0, 0, 20, 20)
    door = Obj(2, ObjectType.DOOR, 40, 0, 10, 10)
    layout = DummyLayout([desk, door], room_w=100, room_h=40, grid_size=10)

    grid, room, cell = _build_occupancy_grid(layout, cell_size=10)

    dr, dc = world_to_cell(5 - room.left, 5 - room.top, cell)
    assert grid[dr][dc] == 1

    rr, cc = world_to_cell(45 - room.left, 5 - room.top, cell)
    assert grid[rr][cc] == 0


def test_find_shortest_path_to_exit_returns_none_if_no_exits():
    layout = DummyLayout([Obj(1, ObjectType.DESK, 10, 10, 10, 10)], exit_points=[])
    assert find_shortest_path_to_exit(layout, start_xy=(15, 15)) is None


def test_find_shortest_path_to_exit_blocked_by_full_wall_returns_none():
    wall = Obj(1, ObjectType.WALL, 50, 0, 10, 40)
    desk = Obj(2, ObjectType.DESK, 10, 10, 10, 10)
    layout = DummyLayout([wall, desk], room_w=100, room_h=40, grid_size=10, exit_points=[(90, 20)])
    assert find_shortest_path_to_exit(layout, start_xy=(15, 15), cell_size=10) is None


def test_find_shortest_path_to_exit_with_door_through_wall_exists():
    wall = Obj(1, ObjectType.WALL, 50, 0, 10, 40)
    door = Obj(2, ObjectType.DOOR, 45, 15, 10, 10)
    desk = Obj(3, ObjectType.DESK, 10, 10, 10, 10)
    layout = DummyLayout([wall, door, desk], room_w=100, room_h=40, grid_size=10, exit_points=[(90, 20)])
    path = find_shortest_path_to_exit(layout, start_xy=(15, 15), cell_size=10)
    assert path is not None
    assert path[-1] == (90, 20)
