import yaml
import glob
import os
from packaging.version import parse as parse_version
import fnmatch


ALL_YAMLS = []
for fname in glob.glob(os.path.dirname(__file__) + "/patch_yaml/*.yaml"):
    with open(fname, "r") as fp:
        fname_yamls = [
            patch_yaml
            for patch_yaml in yaml.safe_load_all(fp)
            if patch_yaml is not None
        ]
        ALL_YAMLS += fname_yamls
        print(
            "Read %d patch yaml docs for file %s"
            % (
                len(fname_yamls),
                os.path.basename(fname),
            ),
            flush=True,
        )

print("Read %d total patch yaml docs" % len(ALL_YAMLS), flush=True)


def _apply_patch_yaml(patch_yaml, record, subdir, fn):
    keep = True
    for k, v in patch_yaml["where"].items():
        if k == "subdir_in":
            keep = keep and (subdir in v)
            if not keep:
                break
        elif k.endswith("_ge") and k[:-3] in record:
            subk = k[:-3]
            rv = record[subk]
            if subk == "version":
                rv = parse_version(rv)
                v = parse_version(v)

            keep = keep and (rv >= v)
            if not keep:
                break
        elif k.endswith("_gt") and k[:-3] in record:
            subk = k[:-3]
            rv = record[subk]
            if subk == "version":
                rv = parse_version(rv)
                v = parse_version(v)

            keep = keep and (rv > v)
            if not keep:
                break
        elif k.endswith("_le") and k[:-3] in record:
            subk = k[:-3]
            rv = record[subk]
            if subk == "version":
                rv = parse_version(rv)
                v = parse_version(v)

            keep = keep and (rv <= v)
            if not keep:
                break
        elif k.endswith("_lt") and k[:-3] in record:
            subk = k[:-3]
            rv = record[subk]
            if subk == "version":
                rv = parse_version(rv)
                v = parse_version(v)

            keep = keep and (rv < v)
            if not keep:
                break
        elif k.endswith("_in") and k[:-3] in record:
            subk = k[:-3]
            keep = keep and (record[subk] in v)
            if not keep:
                break
        elif k == "has_depends":
            if isinstance(v, list):
                keep = keep and all(
                    any(fnmatch.fnmatch(dep, _v) for dep in record.get("depends", []))
                    for _v in v
                )
            else:
                keep = keep and any(
                    fnmatch.fnmatch(dep, v) for dep in record.get("depends", [])
                )
            if not keep:
                break
        elif k in record:
            if k == "version":
                keep = keep and parse_version(record[k]) == parse_version(v)
            else:
                keep = keep and fnmatch.fnmatch(str(record[k]), str(v))
            if not keep:
                break
        else:
            raise KeyError("Unrecognized 'where' key '%s'!" % k)

    if keep:
        for k, v in patch_yaml["do"].items():
            if k.startswith("add_") and k[len("add_") :] in ["depends", "constrains"]:
                subk = k[len("add_") :]
                if not isinstance(v, list):
                    v = [v]
                depends = record.get(subk, [])

                depends.extend(v)

                record[subk] = depends
            elif k.startswith("remove_") and k[len("remove_") :] in [
                "depends",
                "constrains",
            ]:
                subk = k[len("remove_") :]
                if not isinstance(v, list):
                    v = [v]
                depends = record.get(subk, [])

                deps_to_remove = set()
                for _v in v:
                    for dep in depends:
                        if fnmatch.fnmatch(dep, _v):
                            deps_to_remove.add(dep)

                for dep in deps_to_remove:
                    depends.remove(dep)

                record[subk] = depends
            else:
                raise KeyError("Unrecognized 'do' key '%s'!" % k)


def patch_yaml_edit_index(index, subdir):
    for fn, record in index.items():
        for patch_yaml in ALL_YAMLS:
            _apply_patch_yaml(patch_yaml, record, subdir, fn)

    return index
