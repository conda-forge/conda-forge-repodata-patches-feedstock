from pathlib import Path

import pytest
import yaml

from patch_yaml_utils import _test_patch_yaml, _apply_patch_yaml
from patch_yaml_model import generate_schema, PatchYaml


def test_test_patch_yaml_record_key():
    patch_yaml = {"if": {"version": "1.0.0"}}
    record = {"version": "1.0.0"}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"version": "1.0.1"}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"name": "blah"}}
    record = {"name": "blah"}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"name": "blah blah"}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"name": "blah", "version": "1.0.0"}}
    record = {"name": "blah", "version": "1.0.0"}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"name": "blah", "version": "1.0.1"}
    assert not _test_patch_yaml(patch_yaml, record, None, None)


def test_test_patch_yaml_subdir():
    record = {}

    patch_yaml = {"if": {"subdir_in": "linux-64"}}
    assert _test_patch_yaml(patch_yaml, record, "linux-64", None)
    assert not _test_patch_yaml(patch_yaml, record, "osx-64", None)

    patch_yaml = {"if": {"subdir_in": ["linux-64", "osx-64"]}}
    assert _test_patch_yaml(patch_yaml, record, "linux-64", None)
    assert _test_patch_yaml(patch_yaml, record, "osx-64", None)
    assert not _test_patch_yaml(patch_yaml, record, "win-64", None)

    patch_yaml = {"if": {"subdir_in": ["*-64", "osx-64"]}}
    assert _test_patch_yaml(patch_yaml, record, "linux-64", None)
    assert _test_patch_yaml(patch_yaml, record, "osx-64", None)
    assert not _test_patch_yaml(patch_yaml, record, "osx-arm64", None)

    patch_yaml = {"if": {"subdir_in": "*-64"}}
    assert _test_patch_yaml(patch_yaml, record, "linux-64", None)
    assert _test_patch_yaml(patch_yaml, record, "osx-64", None)
    assert not _test_patch_yaml(patch_yaml, record, "osx-arm64", None)


def test_test_patch_yaml_op():
    patch_yaml = {"if": {"version_ge": "1.0.0"}}
    record = {"version": "1.0.0"}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"version": "0.9"}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"version_gt": "1.0.0"}}
    record = {"version": "1.0.1"}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"version": "1.0.0"}
    assert not _test_patch_yaml(patch_yaml, record, None, None)
    record = {"version": "0.9"}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"version_le": "1.0.0"}}
    record = {"version": "1.0.0"}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"version": "1.0.1"}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"version_lt": "1.0.0"}}
    record = {"version": "0.9"}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"version": "1.0.0"}
    assert not _test_patch_yaml(patch_yaml, record, None, None)
    record = {"version": "1.0.1"}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"timestamp_lt": 10}}
    record = {}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"timestamp": 9}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"timestamp": 12}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"build_number_lt": 10}}
    record = {"build_number": 9}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"build_number": 12}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"build_number_eq": 10}}
    record = {"build_number": 10}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"build_number": 12}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"build_number_ne": 10}}
    record = {"build_number": 10}
    assert not _test_patch_yaml(patch_yaml, record, None, None)
    record = {"build_number": 12}
    assert _test_patch_yaml(patch_yaml, record, None, None)


def test_test_patch_yaml_in():
    patch_yaml = {"if": {"build_number_in": 10}}
    record = {"build_number": 10}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"build_number": 12}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"build_number_in": [10, 11]}}
    record = {"build_number": 10}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"build_number": 12}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"build_number_in": "10*"}}
    record = {"build_number": 10}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"build_number": 12}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"build_number_in": ["11*", "10*"]}}
    record = {"build_number": 10}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"build_number": 12}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"artifact_in": "foo"}}
    record = {"build_number": 10}
    assert _test_patch_yaml(patch_yaml, record, None, "foo")
    record = {"build_number": 12}
    assert not _test_patch_yaml(patch_yaml, record, None, "bar")

    patch_yaml = {"if": {"artifact_in": ["foo", "bar"]}}
    record = {"build_number": 10}
    assert _test_patch_yaml(patch_yaml, record, None, "foo")
    record = {"build_number": 12}
    assert _test_patch_yaml(patch_yaml, record, None, "bar")
    record = {"build_number": 12}
    assert not _test_patch_yaml(patch_yaml, record, None, "blah")


def test_test_patch_yaml_has_depends():
    patch_yaml = {"if": {"has_depends": "numpy"}}
    record = {"depends": ["numpy"]}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"depends": ["numpy 1.20"]}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"has_depends": "numpy*"}}
    record = {"depends": ["numpy", "blah"]}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"depends": ["numpy 1.20", "foo"]}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"depends": ["scipy 1.20"]}
    assert not _test_patch_yaml(patch_yaml, record, None, None)

    patch_yaml = {"if": {"has_depends": ["numpy*", "scipy"]}}
    record = {"depends": ["numpy", "blah"]}
    assert not _test_patch_yaml(patch_yaml, record, None, None)
    record = {"depends": ["numpy 1.20", "scipy"]}
    assert _test_patch_yaml(patch_yaml, record, None, None)
    record = {"depends": ["scipy 1.20", "numpy"]}
    assert not _test_patch_yaml(patch_yaml, record, None, None)


@pytest.mark.parametrize("key", ["depends", "constrains"])
def test_apply_patch_yaml_add(key):
    patch_yaml = {"then": [{"add_" + key: "blah"}]}
    record = {"version": 10}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"version": 10, key: ["blah"]}

    patch_yaml = {"then": [{"add_" + key: "blah"}]}
    record = {"version": 10, key: ["foo"]}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"version": 10, key: ["foo", "blah"]}


@pytest.mark.parametrize("key", ["depends", "constrains"])
def test_apply_patch_yaml_remove(key):
    patch_yaml = {"then": [{"remove_" + key: "blah"}]}
    record = {"version": 10}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"version": 10}

    patch_yaml = {"then": [{"remove_" + key: "blah"}]}
    record = {"version": 10, key: ["blah"]}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"version": 10}

    patch_yaml = {"then": [{"remove_" + key: "blah"}]}
    record = {"version": 10, key: ["foo"]}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"version": 10, key: ["foo"]}

    patch_yaml = {"then": [{"remove_" + key: "blah"}]}
    record = {"version": 10, key: ["foo", "blah", "blah 1.0"]}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"version": 10, key: ["foo", "blah 1.0"]}

    patch_yaml = {"then": [{"remove_" + key: "blah*"}]}
    record = {"version": 10, key: ["foo", "blah", "blah 1.0"]}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"version": 10, key: ["foo"]}


def test_apply_patch_yaml_remove_track_features():
    patch_yaml = {"then": [{"remove_track_features": "blah"}]}
    record = {"track_features": "blah"}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {}

    record = {"track_features": "blah foo"}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"track_features": "foo"}

    record = {"track_features": "blah foo bar"}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"track_features": "foo bar"}

    record = {"track_features": "baz blah foo"}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"track_features": "baz foo"}

    record = {"track_features": "baz blah foo bar"}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"track_features": "baz foo bar"}


@pytest.mark.parametrize("pre", [[], ["foo"]])
@pytest.mark.parametrize("post", [[], ["bar"]])
@pytest.mark.parametrize("key", ["depends", "constrains"])
def test_apply_patch_yaml_replace(key, pre, post):
    patch_yaml = {
        "then": [{"replace_" + key: {"old": "numpy 1.0", "new": "numpy 2.0"}}]
    }
    record = {key: pre + ["numpy 1.0"] + post}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {key: pre + ["numpy 2.0"] + post}


@pytest.mark.parametrize("pre", [[], ["foo"]])
@pytest.mark.parametrize("post", [[], ["bar"]])
def test_apply_patch_yaml_rename(pre, post):
    patch_yaml = {"then": [{"rename_depends": {"old": "numpy", "new": "numppy"}}]}
    record = {"depends": pre + ["numpy 1.0 blah"] + post}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"depends": pre + ["numppy 1.0 blah"] + post}


@pytest.mark.parametrize("pre", [[], ["foo"]])
@pytest.mark.parametrize("post", [[], ["bar"]])
def test_apply_patch_yaml_relax_exact(pre, post):
    patch_yaml = {"then": [{"relax_exact_depends": {"name": "numpy"}}]}
    record = {"depends": pre + ["numpy 1.0.0 blah"] + post}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"depends": pre + ["numpy >=1.0.0"] + post}

    patch_yaml = {"then": [{"relax_exact_depends": {"name": "numpy", "max_pin": "x"}}]}
    record = {"depends": pre + ["numpy 1.0.0 blah"] + post}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"depends": pre + ["numpy >=1.0.0,<2.0.0a0"] + post}


@pytest.mark.parametrize("pre", [[], ["foo"]])
@pytest.mark.parametrize("post", [[], ["bar"]])
def test_apply_patch_yaml_tighten(pre, post):
    patch_yaml = {"then": [{"tighten_depends": {"name": "numpy", "max_pin": "x.x"}}]}
    record = {"depends": pre + ["numpy >=1.0.0,<2.0.0a0"] + post}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"depends": pre + ["numpy >=1.0.0,<1.1.0a0"] + post}

    patch_yaml = {
        "then": [{"tighten_depends": {"name": "numpy", "upper_bound": "1.1.2"}}]
    }
    record = {"depends": pre + ["numpy >=1.0.0,<2.0.0a0"] + post}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"depends": pre + ["numpy >=1.0.0,<1.1.2.0a0"] + post}


@pytest.mark.parametrize("pre", [[], ["foo"]])
@pytest.mark.parametrize("post", [[], ["bar"]])
def test_apply_patch_yaml_loosen(pre, post):
    patch_yaml = {"then": [{"loosen_depends": {"name": "numpy", "max_pin": "x"}}]}
    record = {"depends": pre + ["numpy >=1.0.0,<1.1.0a0"] + post}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"depends": pre + ["numpy >=1.0.0,<2.0.0a0"] + post}

    patch_yaml = {
        "then": [{"loosen_depends": {"name": "numpy", "upper_bound": "3.1.2"}}]
    }
    record = {"depends": pre + ["numpy >=1.0.0,<2.0.0a0"] + post}
    _apply_patch_yaml(patch_yaml, record, None, None)
    assert record == {"depends": pre + ["numpy >=1.0.0,<3.1.2.0a0"] + post}


def test_schema_up_to_date():
    schema_on_disk = (Path(__file__).parent / ("patch_yaml_model.json")).read_text()
    schema_str = generate_schema(write=False)
    assert schema_str == schema_on_disk


def test_schema_validation():
    data = Path(__file__).parent / "patch_yaml"
    for document in data.glob("*.yaml"):
        for patch in yaml.safe_load_all(document.read_text()):
            PatchYaml(**patch)
