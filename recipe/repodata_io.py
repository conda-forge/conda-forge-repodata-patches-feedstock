"""Memory-efficient helpers to load and copy repodata.

A parsed ``repodata.json`` for a large subdir like linux-64 contains ~14M
string objects of which only ~2M are unique (dependency specs, licenses,
versions, subdir names, ...). The stdlib JSON parser creates a new ``str``
object for each one of them. Deduplicating them while parsing roughly halves
the memory of each parsed copy, and allows several copies of the same
repodata (raw, patched and reference) to share their strings.
"""

import json

import zstandard


def load_repodata(path, memo=None):
    """Load a ``.json.zst`` repodata file, deduplicating its string values.

    Pass the same ``memo`` dict to several calls to share strings between
    the loaded objects. The memo can be dropped once loading is done.
    """
    if memo is None:
        memo = {}
    setdefault = memo.setdefault

    def _dedup_strings(obj):
        # Called bottom-up for every JSON object, so nested dicts have
        # already been processed by the time we see their parent.
        for key, val in obj.items():
            typ = type(val)
            if typ is str:
                obj[key] = setdefault(val, val)
            elif typ is list:
                obj[key] = [setdefault(v, v) if type(v) is str else v for v in val]
        return obj

    with zstandard.open(path) as fh:
        # decode explicitly so that the raw bytes are freed before parsing
        text = fh.read().decode("utf-8")
    return json.loads(text, object_hook=_dedup_strings)


def _copy_containers(obj):
    typ = type(obj)
    if typ is dict:
        return {k: _copy_containers(v) for k, v in obj.items()}
    if typ is list:
        return [_copy_containers(v) for v in obj]
    # str/int/float/bool/None are immutable and can be shared
    return obj


def copy_repodata(repodata):
    """Return a copy of ``repodata`` whose records can be mutated safely.

    Only dicts and lists are copied; the (immutable) strings and numbers are
    shared with the original. This is much faster and lighter than
    ``copy.deepcopy`` or parsing the file a second time.
    """
    return _copy_containers(repodata)
