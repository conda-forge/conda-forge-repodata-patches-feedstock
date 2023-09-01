# repodata patch YAML specification

The files in this directory are used to construct repodata patches for conda-forge.
Typically, a single feedstock will have a single YAML file specifying the patches
for the packages produced by that feedstock. Use comments liberally to describe
why the patch exists.

## YAML Format

Patches are specified by two main blocks.

- The `if` block specifies a set of conditions under which the changes in the `then` block are applied.
- The different conditions in the `if` block are combined with a logical `AND`.
- Any condition may be prefixed by `not_` and will be negated.
- The `if` conditions can use shell glob syntax as implemented in the python `fnmatch` module in the
  standard library. The optional "?( *)" pattern from extended glob syntax is allowed to match zero or
  one sequences of spaces plus any other characters.
- The `then` section uses the Python `string.Template` system to allow the `version`, `build_number`, `name`, or
  `subdir` values to be inserted into strings via templates (e.g., `"blah <=${version}"`) at runtime.
- Multiple patches can be in the same file using separate YAML documents (i.e., separate the data by `---`
  on a new line).

```yaml
if:
  # possible conditions
  # list of subdirs or a single subdir (e.g., "linux-64")
  subdir_in: linux-64
  # any subdir but linux-64
  not_subdir_in: linux-64

  # list of artifact names or a single name (e.g., "ngmix-2.3.0-py38h50d1736_1.conda")
  artifact_in: ngmix-2.3.0-py38h50d1736_1.conda

  # any key in the repodata entry (e.g., "version" or "build_number") with an operation
  <repodata key>_<ge, gt, le, lt>: <value>
  # this means version > 1.0.0
  version_gt: 1.0.0
  # keeps any record with timestamp < value
  # you can generate the current time via
  #  python -c "import time; print(f'{time.time():.0f}000')"
  timestamp_lt: 1633470721000

  # any key in the repodata entry (e.g., "version" or "build_number") and a list of values or single value
  <repodata key>_in: <list or single item>

  # this means the build number is in the set {0, 1, 2}
  build_number_in: [0, 1, 2]

  # has specific dependencies as either a list or a single string
  has_depends: numpy*  # matches 'numpy', 'nump-blah', or 'numpy 5.6'
  has_depends: numpy?( *)  # matches 'numpy' or 'numpy 5.6' but not 'numpy-blah'
  has_depends: numpy  # matches "numpy" exactly (i.e., no pins)

  # has specific constraints as either a list or a single key
  has_constrains: numpy*  # matches 'numpy', 'nump-blah', or 'numpy 5.6'
  has_constrains: numpy?( *)  # matches 'numpy' or 'numpy 5.6' but not 'numpy-blah'
  has_constrains: numpy  # matches "numpy" exactly (i.e., no pins)

  # single value for a key that should match
  <repodata key>: <value>
  version: 1.0.0
then:
  # list of instructions to change things

  # add to the depends or constrains section of the repodata
  # this function will not add items already present in the record
  - add_<depends or constrains>: <list of str or single str>
  # you can use data from the record being patched like this
  # only name, version, build_number and subdir are supported
  - add_depends: mypackage <=${version}

  # remove from the depends or constrains sections of the repodata
  - remove_<depends or constrains>: <list of str or single str>

  # remove entries from track_features
  - remove_track_features: <list of str or str>

  # replace entries via an exact match in either the depends or constrains sections
  - replace_<depends or constrains>:
      # str of thing to be replaced
      old: matplotlib ==1.3.0
      # thing to replace `old` with
      new: matplotlib-base ==1.4.0
  # globs are allowed in the "old" field so * needs to be escaped via [*]
  - replace_<depends or constrains>:
      # str of thing to be replaced
      old: matplotlib 1.3.[*]  # matches matplotlib 1.3.* exactly
      # thing to replace `old` with
      new: matplotlib-base ==1.4.0
  - replace_<depends or constrains>:
      # str of thing to be replaced
      old: matplotlib 1.3.*  # matches matplotlib 1.3.0, matplotlib 1.3, etc.
      # thing to replace `old` with
      new: matplotlib-base ==1.4.0
  - replace_<depends or constrains>:
      # str of thing to be replaced
      old: matplotlib ==1.3.0
      # thing to replace `old` with
      new: ${old},<1.4.0  # you can refer to the "old" value as well

  # rename a dependency - this preserves the version information and simply renames the package
  - rename_depends:
      # str of thing to be renamed
      old: matplotlib
      # new name for thing
      new: matplotlib-base

  # relax an exact pin (e.g., blah ==1.0.0) to something like blah >=1.0.0 and possibly with
  # `,<2.0a0` added if max_pin='x'
  - relax_exact_depends:
      # the package name whose constraint should be relaxed
      name: matplotlib
      # optional string of 'x', 'x.x' etc. format specify an upper bound
      # if not given, no upper bound is applied
      # max_pin: 'x.x'

  # make a dependency version constraint stricter
  - tighten_depends:
      # package to pin stricter
      name: matplotlib  # this field can use the fnmatch glob syntax
      # you must give one of max_pin or upper_bound
      # optional way to specify the new maximum pin as 'x', 'x.x', etc.
      max_pin: 'x.x'
      # optional way to specify upper bound explicitly
      # do not use with `max_pin`
      upper_bound: 2.0.1

  # make a dependency version constraint looser
  - loosen_depends:
      # package to pin looser
      name: matplotlib  # this field can use the fnmatch glob syntax
      # you must give one of max_pin or upper_bound
      # optional pinning expression 'x', 'x.x', etc. to set how much looser to make the pin
      max_pin: 'x.x'
      # optional way to specify upper bound explicitly
      # do not use with `max_pin`
      upper_bound: 2.0.1
---
# more than one patch can be in the file by putting the next one here as a new YAML doc
if:
  ...
then:
  ...
---
if:
  ...
then:
  ...
```
