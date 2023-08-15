import yaml
import glob
import os


ALL_YAMLS = []
for fname in glob.glob(os.path.dirname(__file__) + "/patch_yamls/*.yaml"):
    with open(fname, "r") as fp:
        fname_yamls = [
            patch_yaml
            for patch_yaml in yaml.safe_load_all(fp)
            if patch_yaml is not None
        ]
        ALL_YAMLS += fname_yamls
        print(
            "Read %d patch yamls for file %s"
            % (
                len(fname_yamls),
                os.path.basename(fname),
            ),
            flush=True,
        )

print("Read %d total patch yamls" % len(ALL_YAMLS), flush=True)


def _apply_patch_yaml(patch_yaml, record, subdir, fn):
    keep = True
    for k, v in patch_yaml["where"].items():
        if k == "max_timestamp":
            keep = keep and (record.get("timestamp", 0) < v)
            if not keep:
                break
        elif k == "version_in":
            keep = keep and (record["version"] in v)
            if not keep:
                break
        elif k == "subdir":
            keep = keep and (subdir == v)
            if not keep:
                break
        elif k in record:
            keep = keep and (record[k] == v)
            if not keep:
                break
        else:
            raise KeyError("Unrecognized 'where' key '%s'!" % k)

    if keep:
        for k, v in patch_yaml["do"].items():
            if k == "add_depends":
                if isinstance(v, list):
                    record["depends"].extend(v)
                else:
                    record["depends"].append(v)
            else:
                raise KeyError("Unrecognized 'do' key '%s'!" % k)


def patch_yamls_edit_index(index, subdir):
    for fn, record in index.items():
        for patch_yaml in ALL_YAMLS:
            _apply_patch_yaml(patch_yaml, record, subdir, fn)

    return index
