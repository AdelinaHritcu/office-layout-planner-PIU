from office_layout.models.layout_model import LayoutModel
from office_layout.models.object_types import ObjectType


def test_add_get_remove_object():
    model = LayoutModel(room_width=100, room_height=80, grid_size=20)
    obj = model.add_object(ObjectType.DESK, x=10, y=10, width=120, height=60)
    assert model.get_object(obj.id) is obj
    model.remove_object(obj.id)
    assert model.get_object(obj.id) is None


def test_remove_missing_object_is_safe():
    model = LayoutModel(100, 80)
    model.remove_object(12345)


def test_objects_by_type():
    model = LayoutModel(200, 200)
    model.add_object(ObjectType.DESK, 0, 0, 120, 60)
    model.add_object(ObjectType.CHAIR, 10, 10, 40, 40)
    model.add_object(ObjectType.DESK, 50, 50, 120, 60)
    desks = model.objects_by_type(ObjectType.DESK)
    assert len(desks) == 2
    assert all(o.type == ObjectType.DESK for o in desks)


def test_forced_id_updates_next_id():
    model = LayoutModel(200, 200)
    obj = model.add_object(ObjectType.DESK, 0, 0, 120, 60, forced_id=50)
    assert obj.id == 50
    obj2 = model.add_object(ObjectType.CHAIR, 0, 0, 40, 40)
    assert obj2.id == 51


def test_to_dict_from_dict_roundtrip_preserves_exit_points_and_objects():
    model = LayoutModel(room_width=300, room_height=200, grid_size=25)
    model.add_object(ObjectType.DESK, x=10, y=20, width=120, height=60, metadata={"foo": "bar"}, forced_id=7)
    model.add_object(ObjectType.CHAIR, x=200, y=100, width=40, height=40)
    model.exit_points = [{"x": 290.0, "y": 100.0}]
    data = model.to_dict()
    loaded = LayoutModel.from_dict(data)
    assert loaded.to_dict() == model.to_dict()
