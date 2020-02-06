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

    assert inst['remove'] == list(REMOVALS['osx-64'])


def test_add_python_abi():
    conditions = {
        'python >=2.7,<2.8.0a0': 'cp27mu',
        'python 3.5.*': 'cp35m',
        'python >=3.8.0a,<3.9.0a0': 'cp38',
        'python 3.5*': 'cp35m',
        'python 2.7*': 'cp27mu',
        'python >=3.6': 'cp*',
        'python >=3.7,<3.8.0a0': 'cp37m',
        'python >=2.7,<3': 'cp*',
        'python >=3.5,<3.6.0a0': 'cp35m',
        'python 3.7.*': 'cp37m',
        'python 2.6*': 'cp26mu',
        'python': 'cp*',
        'python 2.7.*': 'cp27mu',
        'python 3.6*': 'cp36m',
        'python >=3.8,<3.9.0a0': 'cp38',
        'python 3.8.*': 'cp38',
        'python 3.6.*': 'cp36m',
        'python >=3.6.1': 'cp*',
        'python >=3.5': 'cp*',
        'python >=3.4': 'cp*',
        'python <3': 'cp27mu',
        'python 3.4*': 'cp34m',
        'python >=2.7,<3.5': 'cp*',
        'python >=3.6,<3.7.0a0': 'cp36m',
        'python >=2.7': 'cp*',
        'python >=3.3': 'cp*',
    }
    for condition, tag in conditions.items():
        record_orig = {
            "name": "foo",
            "depends": [f"{condition}"],
        }
        record = copy.deepcopy(record_orig)
        add_python_abi(record, "linux-64")
        print(record, condition, tag)
        assert record["constrains"] == [f"python_abi * {tag}"]

        record = copy.deepcopy(record_orig)
        add_python_abi(record, "osx-64")
        if tag == "cp27mu" or tag == "cp26mu":
            assert record["constrains"] == [f"python_abi * {tag[:-1]}"]
        else:
            assert record["constrains"] == [f"python_abi * {tag}"]

    python_record = {
        "name": "python",
        "version": "3.6.8",
    }
    add_python_abi(python_record, "osx-64")
    assert python_record["constrains"] == [f"python_abi * cp36m"]

    exact_record = {
        "name": "foo",
        "depends": ["python 3.6.7 h12312"],
    }
    add_python_abi(exact_record, "osx-64")
    assert exact_record["constrains"] == []

