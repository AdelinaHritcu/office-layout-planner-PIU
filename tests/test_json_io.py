import json
import pytest

from office_layout.models.layout_model import LayoutModel
from office_layout.models.object_types import ObjectType
from office_layout.storage.json_io import load_layout, save_layout


def test_save_and_load_roundtrip(tmp_path):
    model = LayoutModel(room_width=300, room_height=200, grid_size=25)
    model.add_object(ObjectType.DESK, x=10, y=20, width=120, height=60, metadata={"ui_type": "Desk"})
    model.add_object(ObjectType.CHAIR, x=200, y=100, width=40, height=40)
    model.exit_points = [{"x": 290.0, "y": 100.0}]

    p = tmp_path / "layout.json"
    save_layout(p, model)
    loaded = load_layout(p)
    assert loaded.to_dict() == model.to_dict()


def test_save_rejects_non_json_extension(tmp_path):
    model = LayoutModel(100, 100)
    with pytest.raises(ValueError):
        save_layout(tmp_path / "layout.txt", model)


def test_load_rejects_non_json_extension(tmp_path):
    p = tmp_path / "layout.txt"
    p.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        load_layout(p)


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_layout(tmp_path / "missing.json")


def test_load_invalid_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_layout(p)


def test_load_non_dict_root_raises(tmp_path):
    p = tmp_path / "list.json"
    p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_layout(p)


def test_save_requires_layout_model(tmp_path):
    with pytest.raises(ValueError):
        save_layout(tmp_path / "layout.json", None)


def test_save_requires_to_dict(tmp_path):
    class NoToDict:
        pass

    with pytest.raises(TypeError):
        save_layout(tmp_path / "layout.json", NoToDict())


def test_save_requires_mapping_return(tmp_path):
    class BadToDict:
        def to_dict(self):
            return [1, 2, 3]

    with pytest.raises(TypeError):
        save_layout(tmp_path / "layout.json", BadToDict())


def test_save_is_atomic_tmp_removed_on_error(tmp_path):
    class NotJsonSerializable:
        def to_dict(self):
            return {"bad": set([1, 2, 3])}

    p = tmp_path / "layout.json"
    tmp = tmp_path / "layout.json.tmp"

    with pytest.raises(TypeError):
        save_layout(p, NotJsonSerializable())

    assert not tmp.exists()
    assert not p.exists()
