from office_layout.models.object_types import (
    ObjectType,
    get_default_size,
    get_type_info,
    is_walkable,
)


def test_get_type_info_contains_expected_fields():
    info = get_type_info(ObjectType.DESK)
    assert info.type == ObjectType.DESK
    assert info.default_width > 0
    assert info.default_height > 0


def test_get_default_size_matches_type_info():
    w, h = get_default_size(ObjectType.CHAIR)
    info = get_type_info(ObjectType.CHAIR)
    assert (w, h) == (info.default_width, info.default_height)


def test_is_walkable_door_true_desk_false():
    assert is_walkable(ObjectType.DOOR) is True
    assert is_walkable(ObjectType.DESK) is False
