from __future__ import annotations

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


def _is_door(obj: Any) -> bool:
    t = getattr(obj, "type", None)
    if t == ObjectType.DOOR:
        return True
    return _ui_type(obj) == "Door"


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
                f = tentative + abs(goal[0] - r) + abs(goal[1] - c)  # Manhattan
                heappush(open_heap, (f, nb))

    return None


def _build_occupancy_grid(layout_model: Any, cell_size: float) -> Tuple[List[List[int]], Rect, float]:
    room = _room_rect(layout_model)
    w = max(1, int(ceil(room.width / cell_size)))
    h = max(1, int(ceil(room.height / cell_size)))
    grid: List[List[int]] = [[0 for _ in range(w)] for _ in range(h)]

    def _to_local(rr: Rect) -> Rect:
        r = rr.normalized()
        return Rect(r.left - room.left, r.top - room.top, r.width, r.height).normalized()

    def _mark_rect(value: int, r: Rect, *, inflate: float = 0.0) -> None:
        rr = r.normalized()
        local = _to_local(rr)

        if inflate > 0.0:
            local = Rect(
                local.left - inflate,
                local.top - inflate,
                local.width + 2 * inflate,
                local.height + 2 * inflate,
            ).normalized()

        cells = rect_to_covered_cells(local, grid=cell_size, max_rows=h, max_cols=w)
        for r0, c0 in cells:
            if 0 <= r0 < h and 0 <= c0 < w:
                grid[r0][c0] = value

    objects = _iter_objects(layout_model)

    # 1) obstacles (inflate slightly so thin walls are "caught" by the grid)
    obstacle_inflate = max(cell_size * 0.25, 3.0)
    for obj in objects:
        if _is_door(obj):
            continue

        ot = getattr(obj, "type", None)
        if isinstance(ot, ObjectType) and is_walkable(ot):
            continue

        _mark_rect(1, _obj_rect(obj), inflate=obstacle_inflate)

    # 2) open doors: carve a narrow opening through the wall (anisotropic)
    # Clear mostly across the wall thickness, not along the wall.
    door_across = max(obstacle_inflate + cell_size * 0.15, 0.5)  # perpendicular
    door_along = max(cell_size * 0.05, 0.5)                      # parallel (small)

    for obj in objects:
        if not _is_door(obj):
            continue

        dr = _obj_rect(obj).normalized()

        # heuristic: vertical door if taller than wide
        if dr.height >= dr.width:
            opened = Rect(
                dr.left - door_across,
                dr.top - door_along,
                dr.width + 2 * door_across,
                dr.height + 2 * door_along,
            ).normalized()
        else:
            opened = Rect(
                dr.left - door_along,
                dr.top - door_across,
                dr.width + 2 * door_along,
                dr.height + 2 * door_across,
            ).normalized()

        _mark_rect(0, opened, inflate=0.0)

    # 3) ensure exit cells are not blocked by rounding (small neighborhood helps)
    for ex, ey in _get_exit_points(layout_model):
        rr, cc = world_to_cell(ex - room.left, ey - room.top, cell_size)
        if 0 <= rr < h and 0 <= cc < w:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    r2, c2 = rr + dr, cc + dc
                    if 0 <= r2 < h and 0 <= c2 < w:
                        grid[r2][c2] = 0

    return grid, room, cell_size


def _cell_center_world(room: Rect, cell_size: float, cell: Cell) -> Tuple[float, float]:
    r, c = cell
    x = room.left + (c + 0.5) * cell_size
    y = room.top + (r + 0.5) * cell_size
    return x, y


def _nearest_free_cell(grid: List[List[int]], start: Cell, max_radius: int = 10) -> Optional[Cell]:
    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    if w == 0:
        return None

    sr, sc = start
    if 0 <= sr < h and 0 <= sc < w and grid[sr][sc] == 0:
        return start

    for radius in range(1, max_radius + 1):
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                r2 = sr + dr
                c2 = sc + dc
                if 0 <= r2 < h and 0 <= c2 < w and grid[r2][c2] == 0:
                    return (r2, c2)
    return None


def find_shortest_path_to_exit(
    layout_model: Any,
    start_xy: Tuple[float, float],
    cell_size: Optional[float] = None,
) -> Optional[List[Tuple[float, float]]]:
    exits = _get_exit_points(layout_model)
    if not exits:
        return None

    if cell_size is None:
        cell_size = min(_get_grid_size(layout_model), 12.0)

    grid, room, cell = _build_occupancy_grid(layout_model, cell_size=float(cell_size))

    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    if w == 0:
        return None

    sx, sy = start_xy
    sr, sc = world_to_cell(sx - room.left, sy - room.top, cell)
    start = _clamp_cell((sr, sc), w, h)

    if grid[start[0]][start[1]] == 1:
        ns = _nearest_free_cell(grid, start, max_radius=12)
        if ns is None:
            return None
        start = ns

    best_cells: Optional[List[Cell]] = None
    best_exit_xy: Optional[Tuple[float, float]] = None

    for ex, ey in exits:
        gr, gc = world_to_cell(ex - room.left, ey - room.top, cell)
        goal = _clamp_cell((gr, gc), w, h)

        if grid[goal[0]][goal[1]] == 1:
            ng = _nearest_free_cell(grid, goal, max_radius=12)
            if ng is None:
                continue
            goal = ng

        path_cells = _astar_path(grid, start, goal)
        if path_cells is None:
            continue
        if best_cells is None or len(path_cells) < len(best_cells):
            best_cells = path_cells
            best_exit_xy = (ex, ey)

    if best_cells is None or best_exit_xy is None:
        return None

    pts = [_cell_center_world(room, cell, c) for c in best_cells]

    ex, ey = best_exit_xy
    if not pts or (abs(pts[-1][0] - ex) > 1e-6 or abs(pts[-1][1] - ey) > 1e-6):
        pts.append((ex, ey))

    return pts
