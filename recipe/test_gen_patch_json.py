import copy

from gen_patch_json import REMOVALS, _gen_patch_instructions, add_python_abi


def test_gen_patch_instructions():
    index = {
        "packages": {
            "a": {"depends": ["c", "d"], "features": "d"},
            "b": {"nane": "blah"},
            "c": {},
        },
        "packages.conda": {
            "a": {"depends": ["c", "d"], "features": "d"},
            "b": {"nane": "blah"},
            "c": {},
        },
    }

    new_index = {
        "packages": {
            "a": {"depends": ["c", "d", "e"], "features": None},
            "b": {"nane": "blah"},
            "c": {"addthis": "yes"},
        },
        "packages.conda": {
            "a": {"depends": ["c", "d", "e"], "features": None},
            "b": {"nane": "blah"},
            "c": {"addthis": "yes"},
        },
    }

    inst = _gen_patch_instructions(index, new_index, "osx-64")
    assert inst["patch_instructions_version"] == 1
    assert "revoke" in inst
    assert "remove" in inst
    assert "packages" in inst
    assert "packages.conda" in inst

    assert inst["packages"] == {
        "a": {"depends": ["c", "d", "e"], "features": None},
        "c": {"addthis": "yes"},
    }

    assert inst["packages.conda"] == {
        "a": {"depends": ["c", "d", "e"], "features": None},
        "c": {"addthis": "yes"},
    }

    assert set(REMOVALS["osx-64"]) <= set(inst["remove"])


def test_add_python_abi():
    conditions = {
        "python >=2.7,<2.8.0a0": "python_abi * *_cp27mu",
        "python 3.5.*": "python_abi * *_cp35m",
        "python >=3.8.0a,<3.9.0a0": "python_abi * *_cp38",
        "python 3.5*": "python_abi * *_cp35m",
        "python 2.7*": "python_abi * *_cp27mu",
        "python >=3.6": "pypy <0a0",
        "python >=3.7,<3.8.0a0": "python_abi * *_cp37m",
        "python >=2.7,<3": "pypy <0a0",
        "python >=3.5,<3.6.0a0": "python_abi * *_cp35m",
        "python 3.7.*": "python_abi * *_cp37m",
        "python 2.6*": "python_abi * *_cp26mu",
        "python": None,
        "python 2.7.*": "python_abi * *_cp27mu",
        "python 3.6*": "python_abi * *_cp36m",
        "python >=3.8,<3.9.0a0": "python_abi * *_cp38",
        "python 3.8.*": "python_abi * *_cp38",
        "python 3.6.*": "python_abi * *_cp36m",
        "python >=3.6.1": "pypy <0a0",
        "python >=3.5": "pypy <0a0",
        "python >=3.4": "pypy <0a0",
        "python <3": "python_abi * *_cp27mu",
        "python 3.4*": "python_abi * *_cp34m",
        "python >=2.7,<3.5": "pypy <0a0",
        "python >=3.6,<3.7.0a0": "python_abi * *_cp36m",
        "python >=2.7": "pypy <0a0",
        "python >=3.3": "pypy <0a0",
    }
    for condition, tag in conditions.items():
        record_orig = {
            "name": "foo",
            "depends": [f"{condition}"],
            "build": "0",
        }
        record = copy.deepcopy(record_orig)
        add_python_abi(record, "linux-64")
        print(record, condition, tag)
        if tag is None:
            assert record["constrains"] == []
        else:
            assert record["constrains"] == [tag]

        record = copy.deepcopy(record_orig)
        add_python_abi(record, "osx-64")
        if tag is None:
            assert record["constrains"] == []
        elif tag.endswith(("cp27mu", "cp26mu")):
            assert record["constrains"] == [tag[:-1]]
        else:
            assert record["constrains"] == [tag]

    python_record = {
        "name": "python",
        "version": "3.6.8",
        "build": "0",
    }
    add_python_abi(python_record, "osx-64")
    assert python_record["constrains"] == ["python_abi * *_cp36m"]

    build_string_record = {
        "name": "h5py",
        "version": "1.20.0",
        "build": "nompi_py36h513d04c_100",
        "depends": ["python >=3.6,<3.7.0a0"],
    }
    add_python_abi(build_string_record, "osx-64")
    assert build_string_record["constrains"] == ["python_abi * *_cp36m"]

    exact_record = {
        "name": "foo",
        "depends": ["python 3.6.7 h12312"],
        "build": "0",
    }
    add_python_abi(exact_record, "osx-64")
    assert exact_record["constrains"] == []


def test_load_and_copy_repodata(tmp_path):
    import json

    import zstandard

    from repodata_io import copy_repodata, load_repodata

    data = {
        "info": {"subdir": "linux-64"},
        "packages": {
            "a-1-0.tar.bz2": {
                "name": "a",
                "depends": ["python >=3.10", "numpy"],
                "extra_depends": {"x": ["python >=3.10"]},
                "size": 1,
            },
            "b-1-0.tar.bz2": {"name": "b", "depends": ["python >=3.10"], "size": 2},
        },
        "packages.conda": {},
    }
    path = tmp_path / "repodata.json.zst"
    path.write_bytes(zstandard.compress(json.dumps(data).encode()))

    memo = {}
    repodata = load_repodata(str(path), memo)
    ref_repodata = load_repodata(str(path), memo)
    assert repodata == data
    assert ref_repodata == data

    # equal strings are shared, within and across loaded objects
    pkgs, ref_pkgs = repodata["packages"], ref_repodata["packages"]
    dep = pkgs["a-1-0.tar.bz2"]["depends"][0]
    assert dep is pkgs["b-1-0.tar.bz2"]["depends"][0]
    assert dep is pkgs["a-1-0.tar.bz2"]["extra_depends"]["x"][0]
    assert dep is ref_pkgs["a-1-0.tar.bz2"]["depends"][0]

    new_index = copy_repodata(repodata)
    assert new_index == data
    rec = new_index["packages"]["a-1-0.tar.bz2"]
    rec["depends"].append("libfoo")
    rec["extra_depends"]["x"].append("libfoo")
    rec["name"] = "c"
    new_index["packages"]["d-1-0.tar.bz2"] = {}
    # mutating the copy does not touch the original
    assert repodata == data
