# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from collections import defaultdict
import copy
import json
import os
from os.path import join, isdir
import sys
import tqdm

import requests

CHANNEL_NAME = "conda-forge"
CHANNEL_ALIAS = "https://conda-web.anaconda.org"
SUBDIRS = (
    "noarch",
    "linux-64",
    "linux-armv7l",
    "linux-aarch64",
    "linux-ppc64le",
    "osx-64",
    "win-32",
    "win-64",
)

REMOVALS = {
    "noarch": (
        "sendgrid-5.3.0-py_0.tar.bz2",
    ),
    "linux-64": (
        "airflow-with-gcp_api-1.9.0-1.tar.bz2",
        "airflow-with-gcp_api-1.9.0-2.tar.bz2",
        "airflow-with-gcp_api-1.9.0-3.tar.bz2",
        "adios-1.13.1-py36hbecc8f4_0.tar.bz2",
        "cookiecutter-1.4.0-0.tar.bz2",
        "compliance-checker-2.2.0-0.tar.bz2",
        "compliance-checker-3.0.3-py27_0.tar.bz2",
        "compliance-checker-3.0.3-py35_0.tar.bz2",
        "compliance-checker-3.0.3-py36_0.tar.bz2",
        "doconce-1.0.0-py27_0.tar.bz2",
        "doconce-1.0.0-py27_1.tar.bz2",
        "doconce-1.0.0-py27_2.tar.bz2",
        "doconce-1.0.0-py27_3.tar.bz2",
        "doconce-1.0.0-py27_4.tar.bz2",
        "doconce-1.4.0-py27_0.tar.bz2",
        "doconce-1.4.0-py27_1.tar.bz2",
        "gdk-pixbuf-2.36.9-0.tar.bz2",
        "itk-4.12.0-py27_0.tar.bz2",
        "itk-4.12.0-py35_0.tar.bz2",
        "itk-4.12.0-py36_0.tar.bz2",
        "itk-4.13.0-py27_0.tar.bz2",
        "itk-4.13.0-py35_0.tar.bz2",
        "itk-4.13.0-py36_0.tar.bz2",
        "ecmwf_grib-1.14.7-np110py27_0.tar.bz2",
        "ecmwf_grib-1.14.7-np110py27_1.tar.bz2",
        "ecmwf_grib-1.14.7-np111py27_0.tar.bz2",
        "ecmwf_grib-1.14.7-np111py27_1.tar.bz2",
        "libtasn1-4.13-py36_0.tar.bz2",
        "libgsasl-1.8.0-py36_1.tar.bz2",
        "nipype-0.12.0-0.tar.bz2",
        "nipype-0.12.0-py35_0.tar.bz2",
        "postgis-2.4.3+9.6.8-0.tar.bz2",
        "pyarrow-0.1.post-0.tar.bz2",
        "pyarrow-0.1.post-1.tar.bz2",
        "pygpu-0.6.5-0.tar.bz2",
        "pytest-regressions-1.0.1-0.tar.bz2",
        "rapidpy-2.5.2-py36_0.tar.bz2",
        "smesh-8.3.0b0-1.tar.bz2",
        "statuspage-0.3.3-0.tar.bz2",
        "statuspage-0.4.0-0.tar.bz2",
        "statuspage-0.4.1-0.tar.bz2",
        "statuspage-0.5.0-0.tar.bz2",
        "statuspage-0.5.1-0.tar.bz2",
        "tokenize-rt-2.0.1-py27_0.tar.bz2",
        "vaex-core-0.4.0-py27_0.tar.bz2",
    ),
    "osx-64": (
        "adios-1.13.1-py36hbecc8f4_0.tar.bz2",
        "airflow-with-gcp_api-1.9.0-1.tar.bz2",
        "airflow-with-gcp_api-1.9.0-2.tar.bz2",
        "arpack-3.6.1-blas_openblash1f444ea_0.tar.bz2",
        "cookiecutter-1.4.0-0.tar.bz2",
        "compliance-checker-2.2.0-0.tar.bz2",
        "compliance-checker-3.0.3-py27_0.tar.bz2",
        "compliance-checker-3.0.3-py35_0.tar.bz2",
        "compliance-checker-3.0.3-py36_0.tar.bz2",
        "doconce-1.0.0-py27_0.tar.bz2",
        "doconce-1.0.0-py27_1.tar.bz2",
        "doconce-1.0.0-py27_2.tar.bz2",
        "doconce-1.0.0-py27_3.tar.bz2",
        "doconce-1.0.0-py27_4.tar.bz2",
        "doconce-1.4.0-py27_0.tar.bz2",
        "doconce-1.4.0-py27_1.tar.bz2",
        "ecmwf_grib-1.14.7-np110py27_0.tar.bz2",
        "ecmwf_grib-1.14.7-np110py27_1.tar.bz2",
        "ecmwf_grib-1.14.7-np111py27_0.tar.bz2",
        "ecmwf_grib-1.14.7-np111py27_1.tar.bz2",
        "flask-rest-orm-0.5.0-py35_0.tar.bz2",
        "flask-rest-orm-0.5.0-py36_0.tar.bz2",
        "itk-4.12.0-py27_0.tar.bz2",
        "itk-4.12.0-py35_0.tar.bz2",
        "itk-4.12.0-py36_0.tar.bz2",
        "itk-4.13.0-py27_0.tar.bz2",
        "itk-4.13.0-py35_0.tar.bz2",
        "itk-4.13.0-py36_0.tar.bz2",
        "lammps-2018.03.16-.tar.bz2",
        "libtasn1-4.13-py36_0.tar.bz2",
        "mpb-1.6.2-1.tar.bz2",
        "nipype-0.12.0-0.tar.bz2",
        "nipype-0.12.0-py35_0.tar.bz2",
        "pygpu-0.6.5-0.tar.bz2",
        "pytest-regressions-1.0.1-0.tar.bz2",
        "reentry-1.1.0-py27_0.tar.bz2",
        "resampy-0.2.0-py27_0.tar.bz2",
        "statuspage-0.3.3-0.tar.bz2",
        "statuspage-0.4.0-0.tar.bz2",
        "statuspage-0.4.1-0.tar.bz2",
        "statuspage-0.5.0-0.tar.bz2",
        "statuspage-0.5.1-0.tar.bz2",
        "sundials-3.1.0-blas_openblash0edd121_202.tar.bz2",
        "vlfeat-0.9.20-h470a237_2.tar.bz2",
        "xtensor-python-0.19.1-h3e44d54_0.tar.bz2",
    ),
    "win-32": (
        "compliance-checker-2.2.0-0.tar.bz2",
        "compliance-checker-3.0.3-py27_0.tar.bz2",
        "compliance-checker-3.0.3-py35_0.tar.bz2",
        "compliance-checker-3.0.3-py36_0.tar.bz2",
        "cookiecutter-1.4.0-0.tar.bz2",
        "doconce-1.0.0-py27_0.tar.bz2",
        "doconce-1.0.0-py27_1.tar.bz2",
        "doconce-1.0.0-py27_2.tar.bz2",
        "doconce-1.0.0-py27_3.tar.bz2",
        "doconce-1.0.0-py27_4.tar.bz2",
        "doconce-1.4.0-py27_0.tar.bz2",
        "doconce-1.4.0-py27_1.tar.bz2",
        "glpk-4.59-py27_vc9_0.tar.bz2",
        "glpk-4.59-py34_vc10_0.tar.bz2",
        "glpk-4.59-py35_vc14_0.tar.bz2",
        "glpk-4.60-py27_vc9_0.tar.bz2",
        "glpk-4.60-py34_vc10_0.tar.bz2",
        "glpk-4.60-py35_vc14_0.tar.bz2",
        "glpk-4.61-py27_vc9_0.tar.bz2",
        "glpk-4.61-py35_vc14_0.tar.bz2",
        "glpk-4.61-py36_0.tar.bz2",
        "libspatialindex-1.8.5-py27_0.tar.bz2",
        "liknorm-1.3.7-py27_1.tar.bz2",
        "liknorm-1.3.7-py35_1.tar.bz2",
        "liknorm-1.3.7-py36_1.tar.bz2",
        "nlopt-2.4.2-0.tar.bz2",
        "pygpu-0.6.5-0.tar.bz2",

    ),
    "win-64": (
        "compliance-checker-2.2.0-0.tar.bz2",
        "compliance-checker-3.0.3-py27_0.tar.bz2",
        "compliance-checker-3.0.3-py35_0.tar.bz2",
        "compliance-checker-3.0.3-py36_0.tar.bz2",
        "cookiecutter-1.4.0-0.tar.bz2",
        "doconce-1.0.0-py27_0.tar.bz2",
        "doconce-1.0.0-py27_1.tar.bz2",
        "doconce-1.0.0-py27_2.tar.bz2",
        "doconce-1.0.0-py27_3.tar.bz2",
        "doconce-1.0.0-py27_4.tar.bz2",
        "doconce-1.4.0-py27_0.tar.bz2",
        "doconce-1.4.0-py27_1.tar.bz2",
        "glpk-4.59-py27_vc9_0.tar.bz2",
        "glpk-4.59-py34_vc10_0.tar.bz2",
        "glpk-4.59-py35_vc14_0.tar.bz2",
        "glpk-4.60-py27_vc9_0.tar.bz2",
        "glpk-4.60-py34_vc10_0.tar.bz2",
        "glpk-4.60-py35_vc14_0.tar.bz2",
        "glpk-4.61-py27_vc9_0.tar.bz2",
        "glpk-4.61-py35_vc14_0.tar.bz2",
        "glpk-4.61-py36_0.tar.bz2",
        "itk-4.13.0-py35_0.tar.bz2",
        "libspatialindex-1.8.5-py27_0.tar.bz2",
        "liknorm-1.3.7-py27_1.tar.bz2",
        "liknorm-1.3.7-py35_1.tar.bz2",
        "liknorm-1.3.7-py36_1.tar.bz2",
        "nlopt-2.4.2-0.tar.bz2",
        "pygpu-0.6.5-0.tar.bz2",
        "pytest-regressions-1.0.1-0.tar.bz2",
    ),
}

OPERATORS = ["==", ">=", "<=", ">", "<", "!="]


def _gen_patch_instructions(index, new_index, subdir):
    instructions = {
        "patch_instructions_version": 1,
        "packages": defaultdict(dict),
        "revoke": [],
        "remove": [],
    }

    instructions["remove"].extend(REMOVALS.get(subdir, ()))

    # diff all items in the index and put any differences in the instructions
    for fn in index:
        assert fn in new_index
        for key in index[fn]:
            assert key in new_index[fn], (key, index[fn], new_index[fn])
            if index[fn][key] != new_index[fn][key]:
                instructions['packages'][fn][key] = new_index[fn][key]

    return instructions


def _gen_new_index(repodata, subdir):
    """Make any changes to the index by adjusting the values directly.

    This function returns the new index with the adjustments.
    Finally, the new and old indices are then diff'ed to produce the repo
    data patches.
    """
    index = copy.deepcopy(repodata["packages"])

    # deal with windows vc features
    if subdir.startswith("win-"):
        python_vc_deps = {
            '2.6': 'vc 9.*',
            '2.7': 'vc 9.*',
            '3.3': 'vc 10.*',
            '3.4': 'vc 10.*',
            '3.5': 'vc 14.*',
            '3.6': 'vc 14.*',
            '3.7': 'vc 14.*',
        }
        for fn, record in index.items():
            record_name = record['name']
            if record_name == 'python':
                # remove the track_features key
                if 'track_features' in record:
                    record['track_features'] = None
                # add a vc dependency
                if not any(d.startswith('vc') for d in record['depends']):
                    depends = record['depends']
                    depends.append(python_vc_deps[record['version'][:3]])
                    record['depends'] = depends
            elif 'vc' in record.get('features', ''):
                # remove vc from the features key
                vc_version = _extract_and_remove_vc_feature(record)
                if vc_version:
                    # add a vc dependency
                    if not any(d.startswith('vc') for d in record['depends']):
                        depends = record['depends']
                        depends.append('vc %d.*' % vc_version)
                        record['depends'] = depends

    proj4_fixes = {"cartopy", "cdo", "gdal", "libspatialite", "pynio", "qgis"}
    for fn, record in index.items():
        record_name = record["name"]

        # remove dependency from constrains for twisted
        if record_name == "twisted":
            new_constrains = [dep for dep in record.get('constrains', ())
                              if not dep.startswith("pyobjc-framework-cococa")]
            if new_constrains != record.get('constrains', ()):
                record['constrains'] = new_constrains

        # fix deps with wrong names
        if record_name in proj4_fixes:
            _rename_dependency(fn, record, "proj.4", "proj4")

        if record_name == "airflow-with-async":
            _rename_dependency(fn, record, "evenlet", "eventlet")

        if record_name == "iris":
            _rename_dependency(fn, record, "nc_time_axis", "nc-time-axis")

        if (record_name == "r-base" and
                not any(dep.startswith("_r-mutex ")
                        for dep in record["depends"])):
            depends = record["depends"]
            depends.append("_r-mutex 1.* anacondar_1")
            record["depends"] = depends

        if record_name == "gcc_impl_{}".format(subdir):
            _relax_exact(fn, record, "binutils_impl_{}".format(subdir))

        deps = record.get("depends", ())
        if "ntl" in deps and record_name != "sage":
            _rename_dependency(fn, record, "ntl", "ntl 10.3.0")

        # FIXME: disable patching-out blas_openblas feature
        # because hotfixes are not applied to gcc7 label
        # causing inconsistent behavior
        # if (record_name == "blas" and
        #         record["track_features"] == "blas_openblas"):
        #     instructions["packages"][fn]["track_features"] = None
        # if "features" in record:
            # if "blas_openblas" in record["features"]:
            #     # remove blas_openblas feature
            #     instructions["packages"][fn]["features"] = _extract_feature(
            #         record, "blas_openblas")
            #     if not any(d.startswith("blas ") for d in record["depends"]):
            #         depends = record['depends']
            #         depends.append("blas 1.* openblas")
            #         instructions["packages"][fn]["depends"] = depends

        # remove features for openjdk and rb2
        if ("track_features" in record and
                record['track_features'] is not None):
            for feat in record["track_features"].split():
                if feat.startswith(("rb2", "openjdk")):
                    record["track_features"] = _extract_track_feature(
                        record, feat)

        llvm_pkgs = ["libclang", "clang", "clang-tools", "llvm", "llvm-tools", "llvmdev"]
        for llvm in ["libllvm8", "libllvm9"]:
            if any(dep.startswith(llvm) for dep in deps):
                if record_name not in llvm_pkgs:
                    _relax_exact(fn, record, llvm, max_pin="x.x")
                else:
                    _relax_exact(fn, record, llvm, max_pin="x.x.x")
        # make sure the libgfortran version is bound from 3 to 4 for osx
        if subdir == "osx-64":
            _fix_libgfortran(fn, record)
            _fix_libcxx(fn, record)
            _add_osx_virt(fn, record)

    return index


def _rename_dependency(fn, record, old_name, new_name):
    depends = record["depends"]
    dep_idx = next(
        (q for q, dep in enumerate(depends)
         if dep.split(' ')[0] == old_name),
        None
    )
    if dep_idx is not None:
        parts = depends[dep_idx].split(" ")
        remainder = (" " + " ".join(parts[1:])) if len(parts) > 1 else ""
        depends[dep_idx] = new_name + remainder
        record['depends'] = depends


def _fix_libgfortran(fn, record):
    depends = record.get("depends", ())
    dep_idx = next(
        (q for q, dep in enumerate(depends)
         if dep.split(' ')[0] == "libgfortran"),
        None
    )
    if dep_idx is not None:
        # make sure respect minimum versions still there
        # 'libgfortran'         -> >=3.0.1,<4.0.0.a0
        # 'libgfortran ==3.0.1' -> ==3.0.1
        # 'libgfortran >=3.0'   -> >=3.0,<4.0.0.a0
        # 'libgfortran >=3.0.1' -> >=3.0.1,<4.0.0.a0
        if ("==" in depends[dep_idx]) or ("<" in depends[dep_idx]):
            pass
        elif depends[dep_idx] == "libgfortran":
            depends[dep_idx] = "libgfortran >=3.0.1,<4.0.0.a0"
            record['depends'] = depends
        elif ">=3.0.1" in depends[dep_idx]:
            depends[dep_idx] = "libgfortran >=3.0.1,<4.0.0.a0"
            record['depends'] = depends
        elif ">=3.0" in depends[dep_idx]:
            depends[dep_idx] = "libgfortran >=3.0,<4.0.0.a0"
            record['depends'] = depends
        elif ">=4" in depends[dep_idx]:
            # catches all of 4.*
            depends[dep_idx] = "libgfortran >=4.0.0,<5.0.0.a0"
            record['depends'] = depends


def _add_osx_virt(fn, record):
    rconst = record.get("run_constrained", ())
    dep_idx = next(
        (q for q, dep in enumerate(rconst)
         if dep.split(' ')[0] == "__osx"),
        None
    )
    run_constrained = list(rconst)
    if dep_idx is None:
        run_constrained.append("__osx >=10.9")
    if run_constrained:
        record['run_constrained'] = run_constrained


def _fix_libcxx(fn, record):
    record_name = record["name"]
    if not record_name in ["cctools", "ld64", "llvm-lto-tapi"]:
        return
    depends = record.get("depends", ())
    dep_idx = next(
        (q for q, dep in enumerate(depends)
         if dep.split(' ')[0] == "libcxx"),
        None
    )
    if dep_idx is not None:
        dep_parts = depends[dep_idx].split(" ")
        if len(dep_parts) >= 2 and dep_parts[1] == "4.0.1":
            # catches all of 4.*
            depends[dep_idx] = "libcxx >=4.0.1"
            record['depends'] = depends


def _relax_exact(fn, record, fix_dep, max_pin=None):
    depends = record.get("depends", ())
    dep_idx = next(
        (q for q, dep in enumerate(depends)
         if dep.split(' ')[0] == fix_dep),
        None
    )
    if dep_idx is not None:
        dep_parts = depends[dep_idx].split(" ")
        if (len(dep_parts) == 3 and \
                not any(dep_parts[1].startswith(op) for op in OPERATORS)):
            if max_pin is not None:
                ver = dep_parts[1].split(".")
                num_x = max_pin.count("x")
                ver[num_x:] = ["0"]*(len(ver)-num_x)
                ver[num_x-1] = str(int(ver[num_x-1])+1)
                upper_bound="{}a0".format(".".join(ver))
                depends[dep_idx] = "{} >={},<{}".format(*dep_parts[:2], upper_bound)
            else:
                depends[dep_idx] = "{} >={}".format(*dep_parts[:2])
            record['depends'] = depends


def _extract_and_remove_vc_feature(record):
    features = record.get('features', '').split()
    vc_features = tuple(f for f in features if f.startswith('vc'))
    if not vc_features:
        return None
    non_vc_features = tuple(f for f in features if f not in vc_features)
    vc_version = int(vc_features[0][2:])  # throw away all but the first
    if non_vc_features:
        record['features'] = ' '.join(non_vc_features)
    else:
        record['features'] = None
    return vc_version


def _extract_feature(record, feature_name):
    features = record.get('features', '').split()
    features.remove(feature_name)
    return " ".join(features) or None


def _extract_track_feature(record, feature_name):
    features = record.get('track_features', '').split()
    features.remove(feature_name)
    return " ".join(features) or None


def main():
    # Step 1. Collect initial repodata for all subdirs.
    repodatas = {}
    for subdir in tqdm.tqdm(SUBDIRS, desc="Downloading repodata"):
        repodata_url = "/".join(
            (CHANNEL_ALIAS, CHANNEL_NAME, subdir, "repodata.json"))
        response = requests.get(repodata_url)
        response.raise_for_status()
        repodatas[subdir] = response.json()

    # Step 2. Create all patch instructions.
    prefix_dir = os.getenv("PREFIX")
    for subdir in SUBDIRS:
        prefix_subdir = join(prefix_dir, subdir)
        if not isdir(prefix_subdir):
            os.makedirs(prefix_subdir)

        # Step 2a. Generate a new index.
        new_index = _gen_new_index(repodatas[subdir], subdir)

        # Step 2b. Generate the instructions by diff'ing the indices.
        instructions = _gen_patch_instructions(
            repodatas[subdir]['packages'], new_index, subdir)

        # Step 2c. Output this to $PREFIX so that we bundle the JSON files.
        patch_instructions_path = join(
            prefix_subdir, "patch_instructions.json")
        with open(patch_instructions_path, 'w') as fh:
            json.dump(
                instructions, fh, indent=2,
                sort_keys=True, separators=(',', ': '))


if __name__ == "__main__":
    sys.exit(main())
