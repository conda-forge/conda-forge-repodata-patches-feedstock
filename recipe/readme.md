This scheme generates one file per subdir, ``patch_instructions.json``.  This file has entries

```
instructions = {
        "patch_instructions_version": 1,
        "packages": defaultdict(dict),
        "revoke": [],
        "remove": [],
    }
```

``remove`` are lists of filenames that will not show up in the index but may still be downloadable with a direct URL to the file.

``packages`` is a dictionary, where keys are package filenames.  Values are dictionaries similar to the contents of each package in repodata.json.  Any values in provided in ``packages`` here overwrite the values in repodata.json.  Any value set to None is removed.

A tool downloads this package when it sees updates to it, and apples the ``patch_instructions.json``
to the repodata of the conda-forge channel on anaconda.org

The ``show_diff.py`` script in this directory can be used to test out
modifications to ``gen_patch_json.py``.  This scripts shows the difference
between the package records currently available on anaconda.org/conda-forge and those
produced from the patch instructions produced by ``gen_patch_json.py``.

Usage is:

```
usage: show_diff.py [-h] [--subdirs [SUBDIRS [SUBDIRS ...]]] [--use-cache]

show repodata changes from the current gen_patch_json

optional arguments:
  -h, --help            show this help message and exit
  --subdirs [SUBDIRS [SUBDIRS ...]]
                        subdir(s) show, default is all
  --use-cache           use cached repodata files, rather than downloading
                        them

```

Repodata is cached in a ``cache`` directory in the current directory or in the
path specified by the ``CACHE_DIR`` environment variable.

Typically ``show_diff.py`` is run without any argument to download the
necessary repodata followed by repeated calls to ``show_diff.py --use-cache``
to test out changes to the ``gen_patch_json.py`` script.
