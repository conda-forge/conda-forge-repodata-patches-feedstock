#!/usr/bin/env python

import bz2
import difflib
import json
import os
import sys
import urllib
from concurrent.futures import ProcessPoolExecutor


from gen_patch_json import _gen_new_index, _gen_patch_instructions, SUBDIRS

from conda_build.index import _apply_instructions

CACHE_DIR = os.environ.get(
    "CACHE_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
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


def show_record_diffs(subdir, ref_repodata, new_repodata):
    final_lines = []
    for index_key in ['packages', 'packages.conda']:
        for name, ref_pkg in ref_repodata[index_key].items():
            if name in new_repodata[index_key]:
                new_pkg = new_repodata[index_key][name]
            else:
                new_pkg = {}

            # license_family gets added for new packages, ignore it in the diff
            ref_pkg.pop("license_family", None)
            new_pkg.pop("license_family", None)

            # list order is not significant for depends and constrains
            ref_pkg = sort_lists(ref_pkg)
            new_pkg = sort_lists(new_pkg)

            if ref_pkg == new_pkg:
                continue

            print(f"{subdir}::{name}")
            ref_lines = json.dumps(
                ref_pkg, indent=2, sort_keys=True,
            ).splitlines()
            new_lines = json.dumps(
                new_pkg, indent=2, sort_keys=True,
            ).splitlines()
            for ln in difflib.unified_diff(ref_lines, new_lines, n=0, lineterm=''):
                if ln.startswith('+++') or ln.startswith('---') or ln.startswith('@@'):
                    continue
                final_lines.append(ln)

    return final_lines


def do_subdir(subdir, raw_repodata_path, ref_repodata_path):
    with bz2.open(raw_repodata_path) as fh:
        raw_repodata = json.load(fh)
    with bz2.open(ref_repodata_path) as fh:
        ref_repodata = json.load(fh)
    new_index = _gen_new_index(raw_repodata, subdir)
    instructions = _gen_patch_instructions(raw_repodata, new_index, subdir)
    new_repodata = _apply_instructions(subdir, raw_repodata, instructions)
    return show_record_diffs(subdir, ref_repodata, new_repodata)


def download_subdir(subdir, raw_repodata_path, ref_repodata_path):
    raw_url = f"{BASE_URL}/{subdir}/repodata_from_packages.json.bz2"
    urllib.request.urlretrieve(raw_url, raw_repodata_path)
    ref_url = f"{BASE_URL}/{subdir}/repodata.json.bz2"
    urllib.request.urlretrieve(ref_url, ref_repodata_path)


def _process_subdir(subdir, use_cache):
    subdir_dir = os.path.join(CACHE_DIR, subdir)
    if not os.path.exists(subdir_dir):
        os.makedirs(subdir_dir)
    raw_repodata_path = os.path.join(subdir_dir, "repodata_from_packages.json.bz2")
    ref_repodata_path = os.path.join(subdir_dir, "repodata.json.bz2")
    if not use_cache:
        download_subdir(subdir, raw_repodata_path, ref_repodata_path)
    vals = do_subdir(subdir, raw_repodata_path, ref_repodata_path)
    return subdir, vals


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="show repodata changes from the current gen_patch_json")
    parser.add_argument(
        '--subdirs', nargs='*', default=None,
        help='subdir(s) show, default is all')
    parser.add_argument(
        '--use-cache', action='store_true',
        help='use cached repodata files, rather than downloading them')
    args = parser.parse_args()

    if args.subdirs is None:
        subdirs = SUBDIRS
    else:
        subdirs = args.subdirs

    with ProcessPoolExecutor() as exc:
        futs = [
            exc.submit(_process_subdir, subdir, args.use_cache)
            for subdir in subdirs
        ]
        for fut in futs:
            subdir, vals = fut.result()
            print("=" * 80, flush=True)
            print("=" * 80, flush=True)
            print(subdir, flush=True)
            for val in vals:
                print(val, flush=True)
