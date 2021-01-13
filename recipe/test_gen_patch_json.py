from gen_patch_json import _gen_patch_instructions, REMOVALS, add_python_abi
import copy

def test_gen_patch_instructions():
    index = {
        'a': {'depends': ['c', 'd'],
              'features': 'd'},
        'b': {'nane': 'blah'},
        'c': {}
    }

    new_index = {
        'a': {'depends': ['c', 'd', 'e'],
              'features': None},
        'b': {'nane': 'blah'},
        'c': {'addthis': 'yes'}
    }

    inst = _gen_patch_instructions(index, new_index, 'osx-64')
    assert inst['patch_instructions_version'] == 1
    assert 'revoke' in inst
    assert 'remove' in inst
    assert 'packages' in inst

    assert inst['packages'] == {
        'a': {'depends': ['c', 'd', 'e'], 'features': None},
        'c': {'addthis': 'yes'}}

    assert set(REMOVALS['osx-64']) <= set(inst['remove'])


def test_add_python_abi():
    conditions = {
        'python >=2.7,<2.8.0a0': 'python_abi * *_cp27mu',
        'python 3.5.*': 'python_abi * *_cp35m',
        'python >=3.8.0a,<3.9.0a0': 'python_abi * *_cp38',
        'python 3.5*': 'python_abi * *_cp35m',
        'python 2.7*': 'python_abi * *_cp27mu',
        'python >=3.6': 'pypy <0a0',
        'python >=3.7,<3.8.0a0': 'python_abi * *_cp37m',
        'python >=2.7,<3': 'pypy <0a0',
        'python >=3.5,<3.6.0a0': 'python_abi * *_cp35m',
        'python 3.7.*': 'python_abi * *_cp37m',
        'python 2.6*': 'python_abi * *_cp26mu',
        'python': None,
        'python 2.7.*': 'python_abi * *_cp27mu',
        'python 3.6*': 'python_abi * *_cp36m',
        'python >=3.8,<3.9.0a0': 'python_abi * *_cp38',
        'python 3.8.*': 'python_abi * *_cp38',
        'python 3.6.*': 'python_abi * *_cp36m',
        'python >=3.6.1': 'pypy <0a0',
        'python >=3.5': 'pypy <0a0',
        'python >=3.4': 'pypy <0a0',
        'python <3': 'python_abi * *_cp27mu',
        'python 3.4*': 'python_abi * *_cp34m',
        'python >=2.7,<3.5': 'pypy <0a0',
        'python >=3.6,<3.7.0a0': 'python_abi * *_cp36m',
        'python >=2.7': 'pypy <0a0',
        'python >=3.3': 'pypy <0a0',
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
        if tag == None:
            assert record["constrains"] == []
        else:
            assert record["constrains"] == [tag]

        record = copy.deepcopy(record_orig)
        add_python_abi(record, "osx-64")
        if tag == None:
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
