#!/usr/bin/env python

import difflib
import json
import os
import urllib
from concurrent.futures import ProcessPoolExecutor, as_completed

import zstandard
from conda_index.index import _apply_instructions

CACHE_DIR = os.environ.get(
    "CACHE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
)
BASE_URL = "https://conda.anaconda.org/conda-forge"


def sort_lists(obj):
    """make sure the depends and constrains fields are sorted to remove
    false-positive diffs
    """
    for k in obj:
        if k in ["depends", "constrains"]:
            obj[k] = sorted(obj[k])

    return obj


def show_record_diffs(subdir, ref_repodata, new_repodata, fail_fast, group_diffs=True):
    keep_pkgs = os.environ.get("CF_PKGS", None)
    if keep_pkgs is not None:
        keep_pkgs = set(keep_pkgs.split(";"))

    if group_diffs:
        final_lines = {}
    else:
        final_lines = []

    for index_key in ["packages", "packages.conda"]:
        all_names = set(ref_repodata.get(index_key, {}).keys()) | set(
            new_repodata.get(index_key, {}).keys()
        )
        for name in all_names:
            ref_pkg = ref_repodata.get(index_key, {}).get(name, {})
            new_pkg = new_repodata.get(index_key, {}).get(name, {})

            if keep_pkgs is not None and ref_pkg and ref_pkg["name"] not in keep_pkgs:
                continue

            # license_family gets added for new packages, ignore it in the diff
            ref_pkg.pop("license_family", None)
            new_pkg.pop("license_family", None)

            # list order is not significant for depends and constrains
            ref_pkg = sort_lists(ref_pkg)
            new_pkg = sort_lists(new_pkg)

            if ref_pkg == new_pkg:
                continue

            ref_lines = json.dumps(
                ref_pkg,
                indent=2,
                sort_keys=True,
            ).splitlines()
            new_lines = json.dumps(
                new_pkg,
                indent=2,
                sort_keys=True,
            ).splitlines()

            if group_diffs:
                _key = []
                for ln in difflib.unified_diff(ref_lines, new_lines, n=0, lineterm=""):
                    if (
                        ln.startswith("+++")
                        or ln.startswith("---")
                        or ln.startswith("@@")
                    ):
                        continue
                    _key.append(ln)
                _key = tuple(_key)
                if _key not in final_lines:
                    final_lines[_key] = set()
                final_lines[_key].add(f"{subdir}::{name}")
            else:
                final_lines.append()
                for ln in difflib.unified_diff(ref_lines, new_lines, n=0, lineterm=""):
                    if (
                        ln.startswith("+++")
                        or ln.startswith("---")
                        or ln.startswith("@@")
                    ):
                        continue
                    final_lines.append(ln)

            if final_lines and fail_fast:
                return final_lines

    return final_lines


def do_subdir(
    subdir,
    raw_repodata_path,
    ref_repodata_path,
    fail_fast,
    group_diffs=True,
    package_removal_keeplist=None,
):
    from gen_patch_json import _gen_new_index, _gen_patch_instructions

    with zstandard.open(raw_repodata_path) as fh:
        raw_repodata = json.load(fh)
    with zstandard.open(ref_repodata_path) as fh:
        ref_repodata = json.load(fh)
    new_index = _gen_new_index(raw_repodata, subdir)
    instructions = _gen_patch_instructions(
        raw_repodata,
        new_index,
        subdir,
        package_removal_keeplist=package_removal_keeplist,
    )
    new_repodata = _apply_instructions(subdir, raw_repodata, instructions)
    return show_record_diffs(
        subdir, ref_repodata, new_repodata, fail_fast, group_diffs=group_diffs
    )


def download_subdir(subdir, raw_repodata_path, ref_repodata_path):
    raw_url = f"{BASE_URL}/{subdir}/repodata_from_packages.json.zst"
    urllib.request.urlretrieve(raw_url, raw_repodata_path)
    ref_url = f"{BASE_URL}/{subdir}/repodata.json.zst"
    urllib.request.urlretrieve(ref_url, ref_repodata_path)


def _process_subdir(
    subdir, use_cache, fail_fast, group_diffs=True, package_removal_keeplist=None
):
    subdir_dir = os.path.join(CACHE_DIR, subdir)
    if not os.path.exists(subdir_dir):
        os.makedirs(subdir_dir)
    raw_repodata_path = os.path.join(subdir_dir, "repodata_from_packages.json.zst")
    ref_repodata_path = os.path.join(subdir_dir, "repodata.json.zst")
    if not use_cache:
        download_subdir(subdir, raw_repodata_path, ref_repodata_path)
    vals = do_subdir(
        subdir,
        raw_repodata_path,
        ref_repodata_path,
        fail_fast,
        group_diffs=group_diffs,
        package_removal_keeplist=package_removal_keeplist,
    )
    return subdir, vals


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="show repodata changes from the current gen_patch_json"
    )
    parser.add_argument(
        "--subdirs", nargs="*", default=None, help="subdir(s) show, default is all"
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="use cached repodata files, rather than downloading them",
    )
    parser.add_argument(
        "--fail-fast", action="store_true", help="error out on the first non-zero diff"
    )
    parser.add_argument(
        "--no-group-diffs", action="store_true", help="do not group diffs by content"
    )
    parser.add_argument(
        "--package-removal-keeplist",
        type=str,
        help=(
            "comma-separated list of packages to exclude from removals - "
            "used for testing patches for broken packages before adding them "
            "back to the repodata"
        ),
    )
    args = parser.parse_args()

    from gen_patch_json import SUBDIRS

    if args.subdirs is None:
        subdirs = SUBDIRS
    else:
        subdirs = args.subdirs

    with ProcessPoolExecutor() as exc:
        futs = [
            exc.submit(
                _process_subdir,
                subdir,
                args.use_cache,
                args.fail_fast,
                group_diffs=not args.no_group_diffs,
                package_removal_keeplist=(
                    [item.strip() for item in args.package_removal_keeplist.split(",")]
                    if args.package_removal_keeplist
                    else None
                ),
            )
            for subdir in subdirs
        ]
        for fut in as_completed(futs):
            subdir, vals = fut.result()
            print("=" * 80, flush=True)
            print("=" * 80, flush=True)
            if args.fail_fast and vals:
                print(subdir + " has non-zero patch diff", flush=True)
            else:
                print(subdir, flush=True)
            if args.no_group_diffs:
                for val in vals:
                    print(val, flush=True)
            else:
                for key, val in vals.items():
                    # sort packages belonging to a given repodata diff
                    val = sorted(list(val))
                    for v in val:
                        print(v, flush=True)
                    for k in key:
                        print(k, flush=True)
