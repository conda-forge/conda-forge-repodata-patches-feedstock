import yaml
import glob
import os
from packaging.version import parse as parse_version
import fnmatch
import re

OPERATORS = ["==", ">=", "<=", ">", "<", "!="]

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


def _fnmatch_str_or_list(item, v):
    if not isinstance(v, list):
        v = [v]
    return any(fnmatch.fnmatch(item, _v) for _v in v)


def _test_patch_yaml(patch_yaml, record, subdir, fn):
    keep = True
    for k, v in patch_yaml["if"].items():
        if k == "subdir_in":
            keep = keep and _fnmatch_str_or_list(subdir, v)
            if not keep:
                break
        elif k == "artifact_in":
            keep = keep and _fnmatch_str_or_list(fn, v)
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
            keep = keep and _fnmatch_str_or_list(record[subk], v)
            if not keep:
                break
        elif k == "has_depends":
            if not isinstance(v, list):
                v = [v]
            keep = keep and all(
                any(fnmatch.fnmatch(dep, _v) for dep in record.get("depends", []))
                for _v in v
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

    return keep


def _extract_track_feature(record, feature_name):
    features = record.get("track_features", "").split()
    features.remove(feature_name)
    return " ".join(features) or None


def _replace_pin(old_pin, new_pin, deps, record, target="depends"):
    """Replace an exact pin with a new one. deps and target must match."""
    if target not in ("depends", "constrains"):
        raise ValueError
    if old_pin in deps:
        i = record[target].index(old_pin)
        record[target][i] = new_pin


def _rename_dependency(fn, record, old_name, new_name):
    depends = record["depends"]
    dep_idx = next(
        (q for q, dep in enumerate(depends) if dep.split(" ")[0] == old_name), None
    )
    if dep_idx is not None:
        parts = depends[dep_idx].split(" ")
        remainder = (" " + " ".join(parts[1:])) if len(parts) > 1 else ""
        depends[dep_idx] = new_name + remainder
        record["depends"] = depends


def pad_list(lst, num):
    if len(lst) >= num:
        return lst
    return lst + ["0"] * (num - len(lst))


def get_upper_bound(version, max_pin):
    num_x = max_pin.count("x")
    ver = pad_list(version.split("."), num_x)
    ver[num_x:] = ["0"] * (len(ver) - num_x)
    ver[num_x - 1] = str(int(ver[num_x - 1]) + 1)
    return ".".join(ver)


def _relax_exact(fn, record, fix_dep, max_pin=None):
    depends = record.get("depends", ())
    dep_idx = next(
        (q for q, dep in enumerate(depends) if dep.split(" ")[0] == fix_dep), None
    )
    if dep_idx is not None:
        dep_parts = depends[dep_idx].split(" ")
        if len(dep_parts) == 3 and not any(
            dep_parts[1].startswith(op) for op in OPERATORS
        ):
            if max_pin is not None:
                upper_bound = get_upper_bound(dep_parts[1], max_pin) + "a0"
                depends[dep_idx] = "{} >={},<{}".format(*dep_parts[:2], upper_bound)
            else:
                depends[dep_idx] = "{} >={}".format(*dep_parts[:2])
            record["depends"] = depends


CB_PIN_REGEX = re.compile(r"^>=(?P<lower>\d(\.\d+)*a?),<(?P<upper>\d(\.\d+)*)a0$")


def _pin_stricter(fn, record, fix_dep, max_pin, upper_bound=None):
    depends = record.get("depends", ())
    dep_indices = [q for q, dep in enumerate(depends) if dep.split(" ")[0] == fix_dep]
    for dep_idx in dep_indices:
        dep_parts = depends[dep_idx].split(" ")
        if len(dep_parts) not in [2, 3]:
            continue
        m = CB_PIN_REGEX.match(dep_parts[1])
        if m is None:
            continue
        lower = m.group("lower")
        upper = m.group("upper").split(".")
        if upper_bound is None:
            new_upper = get_upper_bound(lower, max_pin).split(".")
        else:
            new_upper = upper_bound.split(".")
        upper = pad_list(upper, len(new_upper))
        new_upper = pad_list(new_upper, len(upper))
        if tuple(upper) > tuple(new_upper):
            if str(new_upper[-1]) != "0":
                new_upper += ["0"]
            depends[dep_idx] = "{} >={},<{}a0".format(
                dep_parts[0], lower, ".".join(new_upper)
            )
            if len(dep_parts) == 3:
                depends[dep_idx] = "{} {}".format(depends[dep_idx], dep_parts[2])
            record["depends"] = depends


def _pin_looser(fn, record, fix_dep, max_pin=None, upper_bound=None):
    depends = record.get("depends", ())
    dep_indices = [q for q, dep in enumerate(depends) if dep.split(" ")[0] == fix_dep]
    for dep_idx in dep_indices:
        dep_parts = depends[dep_idx].split(" ")
        if len(dep_parts) not in [2, 3]:
            continue
        m = CB_PIN_REGEX.match(dep_parts[1])
        if m is None:
            continue
        lower = m.group("lower")
        upper = m.group("upper").split(".")

        if upper_bound is None:
            new_upper = get_upper_bound(lower, max_pin).split(".")
        else:
            new_upper = upper_bound.split(".")

        upper = pad_list(upper, len(new_upper))
        new_upper = pad_list(new_upper, len(upper))

        if tuple(upper) < tuple(new_upper):
            if str(new_upper[-1]) != "0":
                new_upper += ["0"]
            depends[dep_idx] = "{} >={},<{}a0".format(
                dep_parts[0], lower, ".".join(new_upper)
            )
            if len(dep_parts) == 3:
                depends[dep_idx] = "{} {}".format(depends[dep_idx], dep_parts[2])
            record["depends"] = depends


def _apply_patch_yaml(patch_yaml, record, subdir, fn):
    for inst in patch_yaml["then"].items():
        for k, v in inst.items():
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
            elif k == "remove_track_feature":
                if not isinstance(v, list):
                    v = [v]
                for _v in v:
                    _extract_track_feature(record, _v)
            elif k.startswith("replace_") and k[len("replace_") :] in [
                "depends",
                "constrains",
            ]:
                subk = k[len("replace_") :]
                _replace_pin(
                    v["old"], v["new"], record.get(subk, []), record, target=subk
                )
            elif k == "rename_depends":
                _rename_dependency(fn, record, v["old"], v["new"])
            elif k == "relax_exact_depends":
                fix_dep = v["old"]
                max_pin = v.get("max_pin", None)
                _relax_exact(fn, record, fix_dep, max_pin=max_pin)
            elif k == "stricter_depends":
                fix_dep = v["old"]
                max_pin = v["max_pin"]
                upper_bound = v.get("upper_bound", None)
                _pin_stricter(fn, record, fix_dep, max_pin, upper_bound=upper_bound)
            elif k == "looser_depends":
                fix_dep = v["old"]
                max_pin = v.get("max_pin", None)
                upper_bound = v.get("upper_bound", None)
                _pin_looser(
                    fn, record, fix_dep, max_pin=max_pin, upper_bound=upper_bound
                )
            else:
                raise KeyError("Unrecognized 'do' key '%s'!" % k)


def patch_yaml_edit_index(index, subdir):
    for fn, record in index.items():
        for patch_yaml in ALL_YAMLS:
            if _test_patch_yaml(patch_yaml, record, subdir, fn):
                _apply_patch_yaml(patch_yaml, record, subdir, fn)

    return index
