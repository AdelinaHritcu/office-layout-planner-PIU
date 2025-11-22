from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Tuple, Optional
from math import sqrt
from heapq import heappush, heappop

from office_layout.algorithms.placement import (
    _to_rect,
    distance_between,
    fits_in_room,
    collides,
)


@dataclass
class ValidationError:
    code: str
    message: str
    objects_involved: List[Any]


def _iter_objects(layout_model: Any):
    objs = getattr(layout_model, "objects", None)
    if objs is not None:
        return objs
    if hasattr(layout_model, "iter_objects"):
        return layout_model.iter_objects()
    raise AttributeError


def _room_rect(layout_model: Any):
    r = getattr(layout_model, "room_rect", None)
    if r is not None:
        return r
    if hasattr(layout_model, "get_room_rect"):
        return layout_model.get_room_rect()
    raise AttributeError


def _rules(layout_model: Any):
    min_dist = getattr(layout_model, "min_clearance", 0.0)
    min_to_wall = getattr(layout_model, "min_distance_wall", 0.0)
    corridor_width = getattr(layout_model, "min_corridor_width", 0.0)
    return float(min_dist), float(min_to_wall), float(corridor_width)


def _min_distance_wall(obj: Any, room: Any) -> float:
    r = _to_rect(obj)
    room = _to_rect(room)
    d_left = r.left - room.left
    d_top = r.top - room.top
    d_right = room.right - r.right
    d_bottom = room.bottom - r.bottom
    return min(d_left, d_top, d_right, d_bottom)


def _detect_overcrowding(objects, threshold: float) -> List[Tuple[Any, Any]]:
    result = []
    objs = list(objects)
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            d = distance_between(objs[i], objs[j])
            if d < threshold:
                result.append((objs[i], objs[j]))
    return result


def _neighbors(cell, grid, w, h):
    x, y = cell
    if x > 0:
        yield x - 1, y
    if x < w - 1:
        yield x + 1, y
    if y > 0:
        yield x, y - 1
    if y < h - 1:
        yield x, y + 1


def _astar(grid, start, goal):
    w = len(grid[0])
    h = len(grid)

    open_list = []
    heappush(open_list, (0, start))
    came_from = {start: None}
    g_score = {start: 0}

    while open_list:
        _, current = heappop(open_list)

        if current == goal:
            return True

        for n in _neighbors(current, grid, w, h):
            if grid[n[1]][n[0]] == 1:
                continue
            tentative = g_score[current] + 1
            if n not in g_score or tentative < g_score[n]:
                g_score[n] = tentative
                f = tentative + abs(goal[0] - n[0]) + abs(goal[1] - n[1])
                heappush(open_list, (f, n))
                came_from[n] = current

    return False


def _build_grid(layout_model: Any, cell_size: float = 20.0):
    room = _to_rect(_room_rect(layout_model))
    w = int(room.width / cell_size)
    h = int(room.height / cell_size)
    grid = [[0 for _ in range(w)] for _ in range(h)]

    for obj in _iter_objects(layout_model):
        r = _to_rect(obj)
        x1 = int((r.left - room.left) / cell_size)
        y1 = int((r.top - room.top) / cell_size)
        x2 = int((r.right - room.left) / cell_size)
        y2 = int((r.bottom - room.top) / cell_size)

        for y in range(max(0, y1), min(h, y2 + 1)):
            for x in range(max(0, x1), min(w, x2 + 1)):
                grid[y][x] = 1

    return grid, room, cell_size


def _find_access_points(layout_model: Any):
    pts = getattr(layout_model, "access_points", None)
    if pts is not None:
        return pts
    return []


def validate_layout(layout_model: Any) -> List[ValidationError]:
    errors: List[ValidationError] = []
    objects = list(_iter_objects(layout_model))
    room = _room_rect(layout_model)
    min_dist, min_wall, corridor_w = _rules(layout_model)

    for obj in objects:
        if not fits_in_room(obj, room):
            errors.append(ValidationError("OUT_OF_BOUNDS", "Object is outside room.", [obj]))

    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            if collides(objects[i], objects[j]):
                errors.append(
                    ValidationError("COLLISION", "Objects overlap.", [objects[i], objects[j]])
                )

    if min_dist > 0:
        for i in range(len(objects)):
            for j in range(i + 1, len(objects)):
                d = distance_between(objects[i], objects[j])
                if d < min_dist:
                    errors.append(
                        ValidationError("DISTANCE_TOO_SMALL", "Distance below minimum.", [objects[i], objects[j]])
                    )

    if min_wall > 0:
        for obj in objects:
            d = _min_distance_wall(obj, room)
            if d < min_wall:
                errors.append(
                    ValidationError("WALL_DISTANCE", "Too close to wall.", [obj])
                )

    overcrowded = _detect_overcrowding(objects, threshold=min_dist * 0.7 if min_dist > 0 else 30)
    for a, b in overcrowded:
        errors.append(
            ValidationError("OVER_CROWDING", "Area is cluttered.", [a, b])
        )

    if corridor_w > 0:
        pass

    access_points = _find_access_points(layout_model)
    if len(access_points) >= 2:
        grid, room_r, cell = _build_grid(layout_model)

        sx, sy = access_points[0]
        gx, gy = access_points[1]

        sx = int((sx - room_r.x) / cell)
        sy = int((sy - room_r.y) / cell)
        gx = int((gx - room_r.x) / cell)
        gy = int((gy - room_r.y) / cell)

        if not _astar(grid, (sx, sy), (gx, gy)):
            errors.append(
                ValidationError("NO_PATH", "No valid path between access points.", [])
            )

    return errors
