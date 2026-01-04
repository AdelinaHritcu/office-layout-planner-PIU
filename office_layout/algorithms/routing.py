from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import ceil
from typing import Any, Dict, List, Optional, Tuple

from office_layout.utils.geometry import (
    Rect,
    rect_to_covered_cells,
    world_to_cell,
)
from office_layout.models.object_types import ObjectType, is_walkable


Cell = Tuple[int, int]  # (row, col)


def _iter_objects(layout_model: Any) -> List[Any]:
    if hasattr(layout_model, "all_objects") and callable(getattr(layout_model, "all_objects")):
        return list(layout_model.all_objects())
    objs = getattr(layout_model, "objects", None)
    if objs is not None:
        return list(objs)
    if hasattr(layout_model, "iter_objects") and callable(getattr(layout_model, "iter_objects")):
        return list(layout_model.iter_objects())
    raise AttributeError("LayoutModel must expose all_objects() (preferred) or objects/iter_objects().")


def _room_rect(layout_model: Any) -> Rect:
    if hasattr(layout_model, "get_room_rect") and callable(getattr(layout_model, "get_room_rect")):
        d = layout_model.get_room_rect()
        return Rect(float(d["x"]), float(d["y"]), float(d["width"]), float(d["height"])).normalized()

    if hasattr(layout_model, "room_width") and hasattr(layout_model, "room_height"):
        return Rect(0.0, 0.0, float(layout_model.room_width), float(layout_model.room_height)).normalized()

    rr = getattr(layout_model, "room_rect", None)
    if rr is not None:
        if isinstance(rr, dict):
            return Rect(float(rr["x"]), float(rr["y"]), float(rr["width"]), float(rr["height"])).normalized()
        if isinstance(rr, Rect):
            return rr.normalized()

    raise AttributeError("LayoutModel must expose get_room_rect(), room_rect or room_width/room_height.")


def _get_grid_size(layout_model: Any) -> float:
    gs = getattr(layout_model, "grid_size", None)
    if gs is None:
        return 20.0
    try:
        v = float(gs)
    except Exception:
        return 20.0
    return v if v > 0 else 20.0


def _get_exit_points(layout_model: Any) -> List[Tuple[float, float]]:
    pts = getattr(layout_model, "exit_points", None)
    if not pts:
        return []
    out: List[Tuple[float, float]] = []
    for p in pts:
        if isinstance(p, dict):
            out.append((float(p["x"]), float(p["y"])))
        else:
            out.append((float(p[0]), float(p[1])))
    return out


def _ui_type(obj: Any) -> str:
    md = getattr(obj, "metadata", None)
    if isinstance(md, dict):
        v = md.get("ui_type")
        if isinstance(v, str) and v:
            return v
    t = getattr(obj, "type", None)
    if isinstance(t, ObjectType):
        return t.name.title()
    if isinstance(t, str):
        return t
    return "Unknown"


def _is_wall(obj: Any) -> bool:
    t = getattr(obj, "type", None)
    if t == ObjectType.WALL:
        return True
    return _ui_type(obj) == "Wall"


def _obj_rect(obj: Any) -> Rect:
    """
    Same wall convention as your project:
    - normal objects: x,y are top-left
    - walls:
        horizontal: x = left, y = centerline_y, width >= height
        vertical:   x = centerline_x, y = top, height > width
    """
    x = float(getattr(obj, "x"))
    y = float(getattr(obj, "y"))
    w = float(getattr(obj, "width"))
    h = float(getattr(obj, "height"))

    if _is_wall(obj):
        thickness = min(w, h)
        if w >= h:
            return Rect(x, y - thickness / 2.0, w, thickness).normalized()
        return Rect(x - thickness / 2.0, y, thickness, h).normalized()

    return Rect(x, y, w, h).normalized()


def _clamp_cell(cell: Cell, w: int, h: int) -> Cell:
    r, c = cell
    r = 0 if r < 0 else (h - 1 if r >= h else r)
    c = 0 if c < 0 else (w - 1 if c >= w else c)
    return r, c


def _neighbors_4(cell: Cell, w: int, h: int):
    r, c = cell
    if r > 0:
        yield (r - 1, c)
    if r < h - 1:
        yield (r + 1, c)
    if c > 0:
        yield (r, c - 1)
    if c < w - 1:
        yield (r, c + 1)


def _astar_path(grid: List[List[int]], start: Cell, goal: Cell) -> Optional[List[Cell]]:
    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    if w == 0:
        return None

    sr, sc = start
    gr, gc = goal
    if not (0 <= sr < h and 0 <= sc < w and 0 <= gr < h and 0 <= gc < w):
        return None
    if grid[sr][sc] == 1 or grid[gr][gc] == 1:
        return None

    open_heap: List[Tuple[int, Cell]] = []
    heappush(open_heap, (0, start))

    came_from: Dict[Cell, Optional[Cell]] = {start: None}
    gscore: Dict[Cell, int] = {start: 0}

    while open_heap:
        _, cur = heappop(open_heap)

        if cur == goal:
            # reconstruct
            path: List[Cell] = []
            x = cur
            while x is not None:
                path.append(x)
                x = came_from.get(x)
            path.reverse()
            return path

        for nb in _neighbors_4(cur, w, h):
            r, c = nb
            if grid[r][c] == 1:
                continue

            tentative = gscore[cur] + 1
            if nb not in gscore or tentative < gscore[nb]:
                gscore[nb] = tentative
                came_from[nb] = cur
                f = tentative + abs(gr - r) + abs(gc - c)  # Manhattan
                heappush(open_heap, (f, nb))

    return None


def _build_occupancy_grid(layout_model: Any, cell_size: float) -> Tuple[List[List[int]], Rect, float]:
    room = _room_rect(layout_model)
    w = max(1, int(ceil(room.width / cell_size)))
    h = max(1, int(ceil(room.height / cell_size)))
    grid: List[List[int]] = [[0 for _ in range(w)] for _ in range(h)]

    def _mark_rect(value: int, r: Rect) -> None:
        rr = r.normalized()
        local = Rect(rr.left - room.left, rr.top - room.top, rr.width, rr.height).normalized()
        cells = rect_to_covered_cells(local, grid=cell_size, max_rows=h, max_cols=w)
        for r0, c0 in cells:
            if 0 <= r0 < h and 0 <= c0 < w:
                grid[r0][c0] = value

    objects = _iter_objects(layout_model)

    # 1) obstacles
    for obj in objects:
        ui = _ui_type(obj)

        if ui == "Door":
            continue

        ot = getattr(obj, "type", None)
        if isinstance(ot, ObjectType) and is_walkable(ot):
            continue

        _mark_rect(1, _obj_rect(obj))

    # 2) open doors with padding so they reliably cut walls in grid
    door_pad = max(cell_size * 0.6, 6.0)
    for obj in objects:
        if _ui_type(obj) != "Door":
            continue
        r = _obj_rect(obj).normalized()
        opened = Rect(r.left - door_pad, r.top - door_pad, r.width + 2 * door_pad, r.height + 2 * door_pad)
        _mark_rect(0, opened)

    # 3) ensure exit cells are not blocked by rounding
    for ex, ey in _get_exit_points(layout_model):
        rr, cc = world_to_cell(ex - room.left, ey - room.top, cell_size)
        if 0 <= rr < h and 0 <= cc < w:
            grid[rr][cc] = 0

    return grid, room, cell_size


def _cell_center_world(room: Rect, cell_size: float, cell: Cell) -> Tuple[float, float]:
    r, c = cell
    x = room.left + (c + 0.5) * cell_size
    y = room.top + (r + 0.5) * cell_size
    return x, y


def find_shortest_path_to_exit(
    layout_model: Any,
    start_xy: Tuple[float, float],
    cell_size: Optional[float] = None,
) -> Optional[List[Tuple[float, float]]]:
    exits = _get_exit_points(layout_model)
    if not exits:
        return None

    if cell_size is None:
        cell_size = _get_grid_size(layout_model)

    grid, room, cell = _build_occupancy_grid(layout_model, cell_size=float(cell_size))

    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    if w == 0:
        return None

    sx, sy = start_xy
    sr, sc = world_to_cell(sx - room.left, sy - room.top, cell)
    start = _clamp_cell((sr, sc), w, h)

    best_cells: Optional[List[Cell]] = None

    for ex, ey in exits:
        gr, gc = world_to_cell(ex - room.left, ey - room.top, cell)
        goal = _clamp_cell((gr, gc), w, h)
        path_cells = _astar_path(grid, start, goal)
        if path_cells is None:
            continue
        if best_cells is None or len(path_cells) < len(best_cells):
            best_cells = path_cells

    if best_cells is None:
        return None

    # Convert to world points
    return [_cell_center_world(room, cell, c) for c in best_cells]
