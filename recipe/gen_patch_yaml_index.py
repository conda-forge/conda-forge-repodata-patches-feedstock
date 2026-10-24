#!/usr/bin/env python

import json
import os
import sys
import urllib.request
from concurrent.futures import ProcessPoolExecutor, as_completed

import zstandard
from compression import zstd
from tqdm import tqdm

CACHE_DIR = os.environ.get(
    "CACHE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
)
BASE_URL = "https://conda.anaconda.org/conda-forge"


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
    verbose=False,
    debug_package_name=None,
):
    from patch_yaml_utils import patch_yaml_gen_hashmap_for_index

    if verbose:
        tqdm.write(f"[{subdir:>13}] decompressing raw repodata", file=sys.stderr)
    with zstandard.open(raw_repodata_path) as fh:
        raw_repodata = json.load(fh)
    if debug_package_name is not None:
        raw_repodata = _cut_index_to_name(raw_repodata, debug_package_name)

    pyindex = {}
    for index_key in ["packages", "packages.conda"]:
        index = raw_repodata[index_key]
        if verbose:
            tqdm.write(f"[{subdir:>13}] processing {index_key}", file=sys.stderr)
        pyindex[index_key] = patch_yaml_gen_hashmap_for_index(
            index, subdir, verbose=verbose, debug_package_name=debug_package_name
        )

    return pyindex


def download_subdir(subdir, raw_repodata_path):
    raw_url = f"{BASE_URL}/{subdir}/repodata_from_packages.json.zst"
    urllib.request.urlretrieve(raw_url, raw_repodata_path)


def _process_subdir(
    subdir,
    use_cache,
    verbose=False,
    debug_package_name=None,
):
    subdir_dir = os.path.join(CACHE_DIR, subdir)
    if not os.path.exists(subdir_dir):
        os.makedirs(subdir_dir)
    raw_repodata_path = os.path.join(subdir_dir, "repodata_from_packages.json.zst")
    if not use_cache:
        if verbose:
            tqdm.write(f"[{subdir:>13}] downloading index", file=sys.stderr)
        download_subdir(subdir, raw_repodata_path)
    vals = do_subdir(
        subdir,
        raw_repodata_path,
        verbose=verbose,
        debug_package_name=debug_package_name,
    )
    return subdir, vals


def _show_result(subdir, vals):
    msg = (
        "=" * 80,
        "=" * 80,
        f"finished {subdir}",
    )
    tqdm.write("\n".join(msg), file=sys.stdout)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="generate patch yaml indexing files to make patching faster"
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

    # Single threaded option to help with insertering breakpoints and debugging
    if len(subdirs) <= 1:
        subdir, vals = _process_subdir(
            subdirs[0],
            args.use_cache,
            verbose=args.verbose,
            debug_package_name=args.debug_package_name,
        )
        _show_result(
            subdir,
            vals,
        )
        with zstd.open(
            f"patch_yaml_index_{subdir}.json.zst", "wt", encoding="utf-8"
        ) as fp:
            json.dump(vals, fp, sort_keys=True, indent=2)
    else:
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as exc:
            futs = [
                exc.submit(
                    _process_subdir,
                    subdir,
                    args.use_cache,
                    verbose=args.verbose,
                )
                for subdir in subdirs
            ]
            for fut in as_completed(futs):
                subdir, vals = fut.result()
                _show_result(
                    subdir,
                    vals,
                )
                with zstd.open(
                    f"patch_yaml_index_{subdir}.json.zst", "wt", encoding="utf-8"
                ) as fp:
                    json.dump(vals, fp, sort_keys=True, indent=2)
