import yaml
import glob
import os
import sys
import string
from packaging.version import parse as parse_version
import fnmatch as _fnmatch
import re
from functools import lru_cache

ALLOWED_TEMPLATE_KEYS = ["name", "version", "build_number", "subdir"]

OPERATORS = ["==", ">=", "<=", ">", "<", "!="]

ALL_YAMLS = []
for fname in sorted(glob.glob(os.path.dirname(__file__) + "/patch_yaml/*.yaml")):
    with open(fname, "r") as fp:
        fname_yamls = [
            patch_yaml
            for patch_yaml in yaml.safe_load_all(fp)
            if patch_yaml is not None
        ]
        ALL_YAMLS += fname_yamls

print("Read %d total patch yaml docs" % len(ALL_YAMLS), flush=True, file=sys.stderr)


@lru_cache(maxsize=10000)
def _fnmatch_build_re(pat):
    repat = (
        "(?s:\\ .*)?".join([_fnmatch.translate(p)[:-2] for p in pat.split("?( *)")])
        + "\\Z"
    )
    return re.compile(repat).match


def fnmatch(name, pat):
    """Test whether FILENAME matches PATTERN with custom
    allowed optional space via '?( *)'.

    This is useful to match single names with or without a version
    but not other packages.

    Here are various cases to illustrate how this works:

      - 'numpy*' will match 'numpy', 'numpy >=1', and 'numpy-blah >=10'.
      - 'numpy?( *)' will match only 'numpy', 'numpy >=1'.
      - 'numpy' only matches 'numpy'

    **doc string below is from python stdlib**

    Patterns are Unix shell style:

    *       matches everything
    ?       matches any single character
    [seq]   matches any character in seq
    [!seq]  matches any char not in seq

    An initial period in FILENAME is not special.
    Both FILENAME and PATTERN are first case-normalized
    if the operating system requires it.
    If you don't want this, use fnmatchcase(FILENAME, PATTERN).
    """
    name = os.path.normcase(name)
    pat = os.path.normcase(pat)
    match = _fnmatch_build_re(pat)
    return match(name) is not None


def _fnmatch_str_or_list(item, v):
    if not isinstance(v, list):
        v = [v]
    return any(fnmatch(str(item), str(_v)) for _v in v)


@lru_cache(maxsize=10000)
def _get_vars_for_template(value):
    if value is None:
        return []

    if "$" not in value:
        return []

    vars = []
    for key in ALLOWED_TEMPLATE_KEYS:
        if f"${key}" in value or f"${{{key}}}" in value:
            vars.append(key)
    return vars


def _maybe_process_template(value, record, subdir):
    vars = _get_vars_for_template(value)
    if vars:
        data = {key: record[key] for key in vars if key in record}
        if "subdir" in vars:
            data["subdir"] = subdir
        return string.Template(value).substitute(**data)
    else:
        return value


def _test_patch_yaml(patch_yaml, record, subdir, fn):
    keep = True
    for k, v in patch_yaml["if"].items():
        if k.startswith("not_"):
            k = k[4:]
            neg = True
        else:
            neg = False

        if k in record:
            if k == "version":
                _keep = parse_version(record[k]) == parse_version(v)
            else:
                _keep = fnmatch(str(record[k]), str(v))

        elif k == "subdir_in":
            _keep = _fnmatch_str_or_list(subdir, v)

        elif k[-3:] in ["_lt", "_le", "_gt", "_ge", "_eq", "_ne"] and (
            k[:-3] in record
            or k[:-3] in ["timestamp"]  # some records do not have a timestamp
        ):
            subk = k[:-3]

            # some records do not have some keys, so we can
            # special case that here
            if subk == "timestamp":
                rv = record.get(subk, 0)
            else:
                rv = record[subk]

            if subk == "version":
                rv = parse_version(rv)
                v = parse_version(v)
            elif subk in ["build_number", "timestamp"]:
                rv = int(rv)
                v = int(v)

            op = k[-2:]
            if op == "lt":
                _keep = rv < v
            elif op == "le":
                _keep = rv <= v
            elif op == "gt":
                _keep = rv > v
            elif op == "ge":
                _keep = rv >= v
            elif op == "eq":
                _keep = rv == v
            elif op == "ne":
                _keep = rv != v

        elif k.endswith("_in") and k[:-3] in record:
            subk = k[:-3]
            _keep = _fnmatch_str_or_list(record[subk], v)

        elif k.startswith("has_") and k[len("has_") :] in ["depends", "constrains"]:
            subk = k[len("has_") :]
            if not isinstance(v, list):
                v = [v]
            _keep = all(
                any(fnmatch(dep, _v) for dep in record.get(subk, [])) for _v in v
            )

        elif k == "artifact_in":
            _keep = _fnmatch_str_or_list(fn, v)

        else:
            raise KeyError("Unrecognized 'if' key '%s'!" % k)

        if neg:
            keep = keep and (not _keep)
        else:
            keep = keep and _keep

        if not keep:
            break

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


CB_PIN_REGEX = re.compile(r"^>=(?P<lower>\d+(\.\d+)*a?),<(?P<upper>\d+(\.\d+)*)a0$")
CB_GT_REGEX = re.compile(r"^>=(?P<lower>\d+(\.\d+)*a?)[^<*]*$")


def _pin_stricter(fn, record, fix_dep, max_pin, upper_bound=None):
    depends = record.get("depends", ())
    dep_indices = [q for q, dep in enumerate(depends) if dep.split(" ")[0] == fix_dep]
    for dep_idx in dep_indices:
        dep_parts = depends[dep_idx].split(" ")

        if len(dep_parts) == 1 and upper_bound is not None:
            upper_bound = upper_bound.split(".")
            if str(upper_bound[-1]) != "0":
                upper_bound += ["0"]
            upper_bound = ".".join(upper_bound)

            depends[dep_idx] = "{} <{}a0".format(
                dep_parts[0], upper_bound,
            )
            record["depends"] = depends
            continue

        if len(dep_parts) not in [2, 3]:
            continue

        m_gt = CB_GT_REGEX.match(dep_parts[1])
        if m_gt is not None:
            lower = m_gt.group("lower")
            if upper_bound is None:
                new_upper = get_upper_bound(lower, max_pin).split(".")
            else:
                new_upper = upper_bound.split(".")
            _lower = lower.split(".")
            _lower = pad_list(_lower, len(new_upper))
            new_upper = pad_list(new_upper, len(_lower))

            if tuple(_lower) < tuple(new_upper):
                if str(new_upper[-1]) != "0":
                    new_upper += ["0"]
                new_upper = ".".join(new_upper)

                if len(dep_parts) == 2:
                    depends[dep_idx] = "{} {},<{}a0".format(
                        dep_parts[0], dep_parts[1], new_upper
                    )
                elif len(dep_parts) == 3:
                    depends[dep_idx] = "{} {},<{}a0 {}".format(
                        dep_parts[0], dep_parts[1], new_upper, dep_parts[2]
                    )
                else:
                    raise RuntimeError("Weird dep length!")

                record["depends"] = depends

            continue

        m_pin = CB_PIN_REGEX.match(dep_parts[1])
        if m_pin is not None:
            lower = m_pin.group("lower")
            upper = m_pin.group("upper").split(".")
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

            continue


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
    for inst in patch_yaml["then"]:
        for k, v in inst.items():
            if k.startswith("add_") and k[len("add_") :] in ["depends", "constrains"]:
                subk = k[len("add_") :]
                if not isinstance(v, list):
                    v = [v]
                depends = record.get(subk, [])

                v = [_maybe_process_template(_v, record, subdir) for _v in v]

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
                        if fnmatch(dep, _v):
                            deps_to_remove.add(dep)

                for dep in deps_to_remove:
                    depends.remove(dep)

                if depends:
                    record[subk] = depends
                elif not depends and subk in record:
                    del record[subk]

            elif k == "remove_track_feature":
                if not isinstance(v, list):
                    v = [v]
                for _v in v:
                    record["track_features"] = _extract_track_feature(record, _v)
                    if record["track_features"] is None:
                        del record["track_features"]
                        break

            elif k.startswith("replace_") and k[len("replace_") :] in [
                "depends",
                "constrains",
            ]:
                subk = k[len("replace_") :]
                pat = _maybe_process_template(v["old"], record, subdir)
                new_dep = _maybe_process_template(v["new"], record, subdir)
                for dep in record.get(subk, []):
                    if fnmatch(dep, pat):
                        _replace_pin(
                            dep,
                            new_dep,
                            record.get(subk, []),
                            record,
                            target=subk,
                        )

            elif k == "rename_depends":
                _rename_dependency(
                    fn,
                    record,
                    _maybe_process_template(v["old"], record, subdir),
                    _maybe_process_template(v["new"], record, subdir),
                )

            elif k == "relax_exact_depends":
                fix_dep = _maybe_process_template(v["name"], record, subdir)
                max_pin = v.get("max_pin", None)
                _relax_exact(fn, record, fix_dep, max_pin=max_pin)

            elif k == "tighten_depends":
                fix_dep = _maybe_process_template(v["name"], record, subdir)
                max_pin = v.get("max_pin", None)
                upper_bound = v.get("upper_bound", None)
                if upper_bound is not None:
                    upper_bound = _maybe_process_template(
                        str(upper_bound), record, subdir
                    )
                _pin_stricter(fn, record, fix_dep, max_pin, upper_bound=upper_bound)

            elif k == "loosen_depends":
                fix_dep = _maybe_process_template(v["name"], record, subdir)
                max_pin = v.get("max_pin", None)
                upper_bound = v.get("upper_bound", None)
                if upper_bound is not None:
                    upper_bound = _maybe_process_template(
                        str(upper_bound), record, subdir
                    )
                _pin_looser(
                    fn, record, fix_dep, max_pin=max_pin, upper_bound=upper_bound
                )

            else:
                raise KeyError("Unrecognized 'then' key '%s'!" % k)


def patch_yaml_edit_index(index, subdir):
    for fn, record in index.items():
        for patch_yaml in ALL_YAMLS:
            if _test_patch_yaml(patch_yaml, record, subdir, fn):
                _apply_patch_yaml(patch_yaml, record, subdir, fn)

    return index
