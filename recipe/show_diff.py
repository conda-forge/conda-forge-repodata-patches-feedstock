#!/usr/bin/env python

import difflib
import json
import os
import sys
import urllib.request
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import freeze_support

import zstandard
from conda_index.index import _apply_instructions
from tqdm import tqdm

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
            if obj[k] is not None:
                obj[k] = sorted(obj[k])
            else:
                obj[k] = []

    return obj


def show_record_diffs(subdir, ref_repodata, new_repodata, fail_fast, group_diffs=True):
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

            # license_family gets added for new packages, ignore it in the diff
            ref_pkg.pop("license_family", None)
            new_pkg.pop("license_family", None)

            if ref_pkg == new_pkg:
                continue

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
                    if ln.startswith(("+++", "---", "@@")):
                        continue
                    _key.append(ln)
                _key = tuple(_key)
                if _key not in final_lines:
                    final_lines[_key] = set()
                final_lines[_key].add(f"{subdir}::{name}")
            else:
                final_lines.append()
                for ln in difflib.unified_diff(ref_lines, new_lines, n=0, lineterm=""):
                    if ln.startswith(("+++", "---", "@@")):
                        continue
                    final_lines.append(ln)

            if final_lines and fail_fast:
                return final_lines

    return final_lines


def _cut_index_to_name(repodata, name):
    namedash = name + "-"
    for index_key in ["packages", "packages.conda"]:
        for fn in list(repodata[index_key]):
            if not fn.startswith(namedash):
                del repodata[index_key][fn]
    return repodata


def do_subdir(
    subdir,
    raw_repodata_path,
    ref_repodata_path,
    fail_fast,
    group_diffs=True,
    package_removal_keeplist=None,
    verbose=False,
    debug_package_name=None,
):
    from gen_patch_json import _gen_patch_instructions, _patch_indexes

    if verbose:
        tqdm.write(f"[{subdir:>13}] decompressing raw repodata", file=sys.stderr)
    with zstandard.open(raw_repodata_path) as fh:
        raw_repodata = json.load(fh)
    if debug_package_name is not None:
        raw_repodata = _cut_index_to_name(raw_repodata, debug_package_name)

    if verbose:
        tqdm.write(f"[{subdir:>13}] decompressing new repodata", file=sys.stderr)
    # The repodata is so large, that copying a giant pyton dictionary
    # is like way too slow, it is faster to read the repodata twice..
    with zstandard.open(raw_repodata_path) as fh:
        new_index = json.load(fh)
    if debug_package_name is not None:
        new_index = _cut_index_to_name(new_index, debug_package_name)

    _patch_indexes(
        new_index, subdir, verbose=verbose, debug_package_name=debug_package_name
    )
    instructions = _gen_patch_instructions(
        raw_repodata,
        new_index,
        subdir,
        package_removal_keeplist=package_removal_keeplist,
    )
    # Free new_index before ref_repodata is loaded so that at most two parsed
    # copies of the repodata are held in memory at once.
    del new_index
    new_repodata = _apply_instructions(subdir, raw_repodata, instructions)

    if verbose:
        tqdm.write(f"[{subdir:>13}] decompressing ref repodata", file=sys.stderr)
    with zstandard.open(ref_repodata_path) as fh:
        ref_repodata = json.load(fh)
    if debug_package_name is not None:
        ref_repodata = _cut_index_to_name(ref_repodata, debug_package_name)

    return show_record_diffs(
        subdir, ref_repodata, new_repodata, fail_fast, group_diffs=group_diffs
    )


def download_subdir(subdir, raw_repodata_path, ref_repodata_path):
    raw_url = f"{BASE_URL}/{subdir}/repodata_from_packages.json.zst"
    urllib.request.urlretrieve(raw_url, raw_repodata_path)
    ref_url = f"{BASE_URL}/{subdir}/repodata.json.zst"
    urllib.request.urlretrieve(ref_url, ref_repodata_path)


def _process_subdir(
    subdir,
    use_cache,
    fail_fast,
    group_diffs=True,
    package_removal_keeplist=None,
    verbose=False,
    debug_package_name=None,
):
    subdir_dir = os.path.join(CACHE_DIR, subdir)
    if not os.path.exists(subdir_dir):
        os.makedirs(subdir_dir)
    raw_repodata_path = os.path.join(subdir_dir, "repodata_from_packages.json.zst")
    ref_repodata_path = os.path.join(subdir_dir, "repodata.json.zst")
    if not use_cache:
        if verbose:
            tqdm.write(f"[{subdir:>13}] downloading index", file=sys.stderr)
        download_subdir(subdir, raw_repodata_path, ref_repodata_path)
    vals = do_subdir(
        subdir,
        raw_repodata_path,
        ref_repodata_path,
        fail_fast,
        group_diffs=group_diffs,
        package_removal_keeplist=package_removal_keeplist,
        verbose=verbose,
        debug_package_name=debug_package_name,
    )
    return subdir, vals


def _show_result(subdir, vals, fail_fast, no_group_diffs):
    msg = [
        "=" * 80,
        "=" * 80,
    ]
    if fail_fast and vals:
        msg.append(subdir + " has non-zero patch diff")
    else:
        msg.append(subdir)
    if no_group_diffs:
        msg += vals
    else:
        for key, val in vals.items():
            # sort packages belonging to a given repodata diff
            val = sorted(val)
            msg += val
            msg += key

    tqdm.write("\n".join(msg), file=sys.stdout)


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
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print out more verbose progress messages as the patches get generated",
    )
    parser.add_argument(
        "--debug-package-name",
        type=str,
        help=(
            "Limit the repodata to only packages with this "
            "name to enable faster debugging."
        ),
    )
    args = parser.parse_args()

    from gen_patch_json import SUBDIRS

    if args.subdirs is None:
        subdirs = SUBDIRS
    else:
        subdirs = args.subdirs

    package_removal_keeplist = (
        [item.strip() for item in args.package_removal_keeplist.split(",")]
        if args.package_removal_keeplist
        else None
    )
    # Single threaded option to help with insertering breakpoints and debugging
    if len(subdirs) <= 1:
        subdir, vals = _process_subdir(
            subdirs[0],
            args.use_cache,
            args.fail_fast,
            group_diffs=not args.no_group_diffs,
            package_removal_keeplist=package_removal_keeplist,
            verbose=args.verbose,
            debug_package_name=args.debug_package_name,
        )
        _show_result(
            subdir,
            vals,
            fail_fast=args.fail_fast,
            no_group_diffs=args.no_group_diffs,
        )
    else:
        from gen_patch_json import FlushingRLock

        freeze_support()
        tqdm.set_lock(FlushingRLock())

        with ProcessPoolExecutor(
            max_workers=os.cpu_count(),
            initializer=tqdm.set_lock,
            initargs=(tqdm.get_lock(),),
        ) as exc:
            futs = [
                exc.submit(
                    _process_subdir,
                    subdir,
                    args.use_cache,
                    args.fail_fast,
                    group_diffs=not args.no_group_diffs,
                    package_removal_keeplist=package_removal_keeplist,
                    verbose=args.verbose,
                )
                for subdir in subdirs
            ]
            for fut in as_completed(futs):
                subdir, vals = fut.result()
                _show_result(
                    subdir,
                    vals,
                    fail_fast=args.fail_fast,
                    no_group_diffs=args.no_group_diffs,
                )
