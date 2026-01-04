from enum import Enum
from dataclasses import dataclass
from typing import Dict, Tuple


class ObjectType(Enum):
    DESK = "desk"
    CHAIR = "chair"
    ARMCHAIR = "armchair"
    PLANT = "plant"
    WALL = "wall"
    DOOR = "door"
    PRINTER = "printer"
    MEETING_TABLE = "meeting_table"
    SINK = "sink"
    TOILET = "toilet"
    WASHBASIN = "washbasin"


@dataclass
class ObjectTypeInfo:
    type: ObjectType
    default_width: float
    default_height: float
    min_distance_to_same_type: float
    min_distance_to_other: float
    category: str
    walkable: bool


OBJECT_TYPES: Dict[ObjectType, ObjectTypeInfo] = {
    ObjectType.DESK: ObjectTypeInfo(
        type=ObjectType.DESK,
        default_width=120,
        default_height=60,
        min_distance_to_same_type=50,
        min_distance_to_other=30,
        category="furniture",
        walkable=False,
    ),

    ObjectType.CHAIR: ObjectTypeInfo(
        type=ObjectType.CHAIR,
        default_width=40,
        default_height=40,
        min_distance_to_same_type=20,
        min_distance_to_other=20,
        category="furniture",
        walkable=False,
    ),

    ObjectType.ARMCHAIR: ObjectTypeInfo(
        type=ObjectType.ARMCHAIR,
        default_width=60,
        default_height=60,
        min_distance_to_same_type=20,
        min_distance_to_other=20,
        category="furniture",
        walkable=False,
    ),

    ObjectType.PLANT: ObjectTypeInfo(
        type=ObjectType.PLANT,
        default_width=40,
        default_height=40,
        min_distance_to_same_type=10,
        min_distance_to_other=10,
        category="decoration",
        walkable=False,
    ),

    ObjectType.WALL: ObjectTypeInfo(
        type=ObjectType.WALL,
        default_width=100,
        default_height=10,
        min_distance_to_same_type=0,
        min_distance_to_other=0,
        category="infrastructure",
        walkable=False,
    ),

    ObjectType.DOOR: ObjectTypeInfo(
        type=ObjectType.DOOR,
        default_width=80,
        default_height=10,
        min_distance_to_same_type=0,
        min_distance_to_other=0,
        category="infrastructure",
        walkable=True,
    ),

    ObjectType.PRINTER: ObjectTypeInfo(
        type=ObjectType.PRINTER,
        default_width=50,
        default_height=50,
        min_distance_to_same_type=20,
        min_distance_to_other=20,
        category="infrastructure",
        walkable=False,
    ),

    ObjectType.MEETING_TABLE: ObjectTypeInfo(
        type=ObjectType.MEETING_TABLE,
        default_width=200,
        default_height=100,
        min_distance_to_same_type=50,
        min_distance_to_other=40,
        category="furniture",
        walkable=False,
    ),

    ObjectType.SINK: ObjectTypeInfo(
        type=ObjectType.SINK,
        default_width=60,
        default_height=40,
        min_distance_to_same_type=10,
        min_distance_to_other=10,
        category="infrastructure",
        walkable=False,
    ),

    ObjectType.TOILET: ObjectTypeInfo(
        type=ObjectType.TOILET,
        default_width=60,
        default_height=60,
        min_distance_to_same_type=10,
        min_distance_to_other=10,
        category="infrastructure",
        walkable=False,
    ),

    ObjectType.WASHBASIN: ObjectTypeInfo(
        type=ObjectType.WASHBASIN,
        default_width=50,
        default_height=40,
        min_distance_to_same_type=10,
        min_distance_to_other=10,
        category="infrastructure",
        walkable=False,
    ),
}


def get_type_info(object_type: ObjectType) -> ObjectTypeInfo:
    return OBJECT_TYPES[object_type]


def get_default_size(object_type: ObjectType) -> Tuple[float, float]:
    info = OBJECT_TYPES[object_type]
    return info.default_width, info.default_height


def is_walkable(object_type: ObjectType) -> bool:
    return OBJECT_TYPES[object_type].walkable
