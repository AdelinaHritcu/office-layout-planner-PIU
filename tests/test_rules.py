from office_layout.models.object_types import ObjectType
from office_layout.models.rules import (
    MIN_CHAIR_TO_CHAIR_DISTANCE,
    MIN_CORRIDOR_WIDTH,
    MIN_DESK_TO_DESK_DISTANCE,
    MIN_DESK_TO_WALL_DISTANCE,
    get_max_capacity_for_area,
    get_min_corridor_width,
    get_min_distance_for_type,
    get_min_distance_to_wall,
)


def test_get_min_distance_for_type_matches_constants():
    assert get_min_distance_for_type(ObjectType.DESK) == MIN_DESK_TO_DESK_DISTANCE
    assert get_min_distance_for_type(ObjectType.CHAIR) == MIN_CHAIR_TO_CHAIR_DISTANCE
    assert get_min_distance_for_type(ObjectType.PLANT) == 0.0


def test_get_min_distance_to_wall_matches_constants():
    assert get_min_distance_to_wall(ObjectType.DESK) == MIN_DESK_TO_WALL_DISTANCE
    assert get_min_distance_to_wall(ObjectType.PLANT) == 0.0


def test_get_min_corridor_width_matches_constant():
    assert get_min_corridor_width() == MIN_CORRIDOR_WIDTH


def test_get_max_capacity_for_area_basic():
    assert get_max_capacity_for_area(0) == 0
    assert get_max_capacity_for_area(-10) == 0
    assert get_max_capacity_for_area(400_000) >= 0
