from gen_patch_json import _gen_patch_instructions, REMOVALS


def test_gen_patch_instructions():
    index = {
        'a': {'depends': ['c', 'd'],
              'features': 'd'},
        'b': {'nane': 'blah'},
    }

    new_index = {
        'a': {'depends': ['c', 'd', 'e'],
              'features': None},
        'b': {'nane': 'blah'},
    }

    inst = _gen_patch_instructions(index, new_index, 'osx-64')
    assert inst['patch_instructions_version'] == 1
    assert 'revoke' in inst
    assert 'remove' in inst
    assert 'packages' in inst

    assert inst['packages'] == {
        'a': {'depends': ['c', 'd', 'e'], 'features': None}}

    assert inst['remove'] == list(REMOVALS['osx-64'])
