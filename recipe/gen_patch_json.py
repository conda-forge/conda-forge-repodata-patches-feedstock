# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import json
import os
import re
import sys
import tempfile
import urllib
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from os.path import isdir, join
from tqdm import tqdm
from functools import partial


import requests
import zstandard
from conda_index.index import _apply_instructions
from get_license_family import get_license_family
from packaging.version import parse as parse_version
from patch_yaml_utils import (
    CB_PIN_REGEX,
    _relax_exact,
    pad_list,
    patch_yaml_edit_index,
)
from show_diff import show_record_diffs

CHANNEL_NAME = "conda-forge"
CHANNEL_ALIAS = "https://conda.anaconda.org"
BASE_URL = os.path.join(CHANNEL_ALIAS, CHANNEL_NAME)
SUBDIRS = (
    "noarch",
    "linux-64",
    "linux-armv7l",
    "linux-aarch64",
    "linux-ppc64le",
    "osx-64",
    "osx-arm64",
    "win-32",
    "win-64",
)

REMOVALS = {
    "noarch": (
        "sendgrid-5.3.0-py_0.tar.bz2",
        # the removals starting here are failed uploads
        "boto3-stubs-lite-1.26.89-pyhd8ed1ab_0.conda",
        "ca-policy-lcg-1.119-hd8ed1ab_0.conda",
        "cfn-lint-0.74.2-pyhd8ed1ab_0.conda",
        "conda-forge-pinning-2023.06.08.10.36.51-hd8ed1ab_0.conda",
        "conda-forge-repodata-patches-20230516.19.05.39-hd8ed1ab_0.conda",
        "ffmpeg-progress-yield-0.7.6-pyhd8ed1ab_0.conda",
        "idds-doma-1.3.0-pyhd8ed1ab_0.conda",
        "pandera-core-0.14.3-pyhd8ed1ab_0.conda",
        "pandera-pyspark-0.14.3-hd8ed1ab_0.conda",
        "perl-extutils-makemaker-7.68-pl5321hd8ed1ab_0.conda",
        "pyhanko-0.17.2-pyhd8ed1ab_0.conda",
        "python-flatbuffers-23.3.3-pyhd8ed1ab_0.conda",
        "strawberry-graphql-with-asgi-0.162.0-pyhd8ed1ab_0.conda",
        # end of removals for failed uploads
    ),
    "linux-aarch64": (
        # the removals starting here are failed uploads
        "awscli-1.29.39-py38he37f277_0.conda",
        # end of removals for failed uploads
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
    "osx-arm64": (),
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
        # the removals starting here are failed uploads
        "libgz-sim8-8.1.0-h86fce40_0.conda",
        # end of removals for failed uploads
    ),
}

OSX_SDK_FIXES = {
    "nodejs-12.8.0-hec2bf70_1": "10.10",
    "nodejs-12.1.0-h6de7cb9_1": "10.10",
    "nodejs-12.3.1-h6de7cb9_0": "10.10",
    "nodejs-12.9.0-hec2bf70_0": "10.10",
    "nodejs-12.9.1-hec2bf70_0": "10.10",
    "nodejs-12.7.0-hec2bf70_1": "10.10",
    "nodejs-12.10.0-hec2bf70_0": "10.10",
    "nodejs-12.4.0-h6de7cb9_0": "10.10",
    "nodejs-12.11.1-hec2bf70_0": "10.10",
    "nodejs-12.7.0-h6de7cb9_0": "10.10",
    "nodejs-12.3.0-h6de7cb9_0": "10.10",
    "nodejs-10.16.3-hec2bf70_0": "10.10",
    "nodejs-12.12.0-hfddbe92_0": "10.10",
    "nodejs-12.8.1-hec2bf70_0": "10.10",
    "javafx-sdk-11.0.4-h6dcaf97_1": "10.11",
    "javafx-sdk-12.0.2-h6dcaf97_1": "10.11",
    "javafx-sdk-12.0.2-h6dcaf97_0": "10.11",
    "javafx-sdk-11.0.4-h6dcaf97_0": "10.11",
    "qt-5.12.1-h1b46049_0": "10.12",
    "qt-5.9.7-h8cf7e54_3": "10.12",
    "qt-5.9.7-h93ee506_0": "10.12",
    "qt-5.9.7-h93ee506_1": "10.12",
    "qt-5.12.5-h1b46049_0": "10.12",
    "qt-5.9.7-h93ee506_2": "10.12",
    "openmpi-mpicxx-4.0.1-h6052eea_2": "10.12",
    "openmpi-mpicxx-4.0.1-h6052eea_1": "10.12",
    "openmpi-mpicxx-4.0.1-h6052eea_0": "10.12",
    "openmpi-mpicxx-4.0.1-hc9558a2_2": "10.12",
    "openmpi-mpicxx-4.0.1-hc9558a2_0": "10.12",
    "openmpi-mpicxx-4.0.1-hc9558a2_1": "10.12",
    "freecad-0.18.3-py37h4764a83_2": "10.12",
    "freecad-0.18.3-py37hc453731_1": "10.12",
    "freecad-0.18.4-py37hab2b3aa_1": "10.12",
    "freecad-0.18.4-py37hab2b3aa_0": "10.12",
    "openmpi-mpicc-4.0.1-h24e1f75_1": "10.12",
    "openmpi-mpicc-4.0.1-h24e1f75_2": "10.12",
    "openmpi-mpicc-4.0.1-h24e1f75_0": "10.12",
    "openmpi-mpicc-4.0.1-h516909a_0": "10.12",
    "openmpi-mpicc-4.0.1-h516909a_1": "10.12",
    "openmpi-mpicc-4.0.1-h516909a_2": "10.12",
    "openmpi-mpifort-4.0.1-h939af09_0": "10.12",
    "openmpi-mpifort-4.0.1-h6ad152f_2": "10.12",
    "openmpi-mpifort-4.0.1-h939af09_2": "10.12",
    "openmpi-mpifort-4.0.1-h939af09_1": "10.12",
    "openmpi-mpifort-4.0.1-he991be0_0": "10.12",
    "openmpi-mpifort-4.0.1-he991be0_1": "10.12",
    "openmpi-mpifort-4.0.1-he991be0_2": "10.12",
    "reaktoro-1.0.7-py37h99eb986_0": "10.12",
    "reaktoro-1.0.7-py37h99eb986_1": "10.12",
    "reaktoro-1.0.7-py36h99eb986_0": "10.12",
    "reaktoro-1.0.7-py36h99eb986_1": "10.12",
    "pyqt-5.12.3-py38he22c54c_1": "10.12",
    "pyqt-5.9.2-py37h2a560b1_0": "10.12",
    "pyqt-5.12.3-py36he22c54c_1": "10.12",
    "pyqt-5.9.2-py27h2a560b1_4": "10.12",
    "pyqt-5.9.2-py27h2a560b1_1": "10.12",
    "pyqt-5.9.2-py37h2a560b1_4": "10.12",
    "pyqt-5.9.2-py36h2a560b1_3": "10.12",
    "pyqt-5.9.2-py27h2a560b1_2": "10.12",
    "pyqt-5.9.2-py36h2a560b1_1": "10.12",
    "pyqt-5.12.3-py27h2a560b1_0": "10.12",
    "pyqt-5.12.3-py37h2a560b1_0": "10.12",
    "pyqt-5.12.3-py27he22c54c_0": "10.12",
    "pyqt-5.12.3-py27he22c54c_1": "10.12",
    "pyqt-5.9.2-py37h2a560b1_2": "10.12",
    "pyqt-5.9.2-py37h2a560b1_1": "10.12",
    "pyqt-5.9.2-py36h2a560b1_0": "10.12",
    "pyqt-5.9.2-py36h2a560b1_4": "10.12",
    "pyqt-5.9.2-py27h2a560b1_0": "10.12",
    "pyqt-5.9.2-py37h2a560b1_3": "10.12",
    "pyqt-5.12.3-py38he22c54c_0": "10.12",
    "pyqt-5.9.2-py27h2a560b1_3": "10.12",
    "pyqt-5.9.2-py36h2a560b1_2": "10.12",
    "pyqt-5.12.3-py37he22c54c_0": "10.12",
    "pyqt-5.12.3-py36he22c54c_0": "10.12",
    "pyqt-5.12.3-py37he22c54c_1": "10.12",
    "pyqt-5.12.3-py36h2a560b1_0": "10.12",
    "ldas-tools-al-2.6.3-hf543496_0": "10.12",
    "ldas-tools-al-2.6.3-hf543496_1": "10.12",
    "ldas-tools-al-2.6.4-h4f290e7_1": "10.12",
    "ldas-tools-al-2.6.4-h4f290e7_0": "10.12",
    "openmpi-4.0.1-ha90c164_2": "10.12",
    "openmpi-4.0.1-ha90c164_0": "10.12",
    "openmpi-4.0.1-hfcebdee_2": "10.12",
    "openmpi-4.0.1-ha90c164_1": "10.12",
    "openmpi-4.0.1-hc99cbb1_1": "10.12",
    "openmpi-4.0.1-hc99cbb1_0": "10.12",
    "openmpi-4.0.1-hc99cbb1_2": "10.12",
}


def _add_pybind11_abi_constraint(fn, record):
    """the pybind11-abi package uses the internals version

    here are the ranges

    v2.2.0 1
    v2.2.1 1
    v2.2.2 1
    v2.2.3 1
    v2.2.4 2
    v2.3.0 3
    v2.4.0 3
    v2.4.1 3
    v2.4.2 3
    v2.4.3 3
    v2.5.0 4
    v2.6.0 4
    v2.6.0b1 4
    v2.6.0rc1 4
    v2.6.0rc2 4
    v2.6.0rc3 4
    v2.6.1 4

    prior to 2.2.0 we set it to 0
    """
    ver = parse_version(record["version"])

    if ver < parse_version("2.2.0"):
        abi_ver = "0"
    elif ver < parse_version("2.2.4"):
        abi_ver = "1"
    elif ver < parse_version("2.3.0"):
        abi_ver = "2"
    elif ver < parse_version("2.5.0"):
        abi_ver = "3"
    elif ver <= parse_version("2.6.1"):
        abi_ver = "4"
    else:
        # past this we should have a constrains there already
        raise RuntimeError(
            "pybind11 version %s out of range for abi" % record["version"]
        )

    constrains = record.get("constrains", [])
    found_idx = None
    for idx in range(len(constrains)):
        if constrains[idx].startswith("pybind11-abi "):
            found_idx = idx

    if found_idx is None:
        constrains.append("pybind11-abi ==" + abi_ver)
    else:
        constrains[found_idx] = "pybind11-abi ==" + abi_ver

    record["constrains"] = constrains


def _fix_libgfortran(fn, record):
    depends = record.get("depends", ())
    dep_idx = next(
        (q for q, dep in enumerate(depends) if dep.split(" ")[0] == "libgfortran"), None
    )
    if (
        dep_idx is not None
        # timestamp corresponds to 2025-06-21, just ahead of
        # https://github.com/conda-forge/gfortran_osx-64-feedstock/commit/7764b8460e37355492aa058d69cf620f0aebeeec
        and record.get("timestamp", 0) < 1655769600000
    ):
        # make sure respect minimum versions still there
        # 'libgfortran'         -> >=3.0.1,<4.0.0.a0
        # 'libgfortran ==3.0.1' -> ==3.0.1
        # 'libgfortran >=3.0'   -> >=3.0,<4.0.0.a0
        # 'libgfortran >=3.0.1' -> >=3.0.1,<4.0.0.a0
        if ("==" in depends[dep_idx]) or ("<" in depends[dep_idx]):
            pass
        elif depends[dep_idx] == "libgfortran":
            depends[dep_idx] = "libgfortran >=3.0.1,<4.0.0.a0"
            record["depends"] = depends
        elif ">=3.0.1" in depends[dep_idx]:
            depends[dep_idx] = "libgfortran >=3.0.1,<4.0.0.a0"
            record["depends"] = depends
        elif ">=3.0" in depends[dep_idx]:
            depends[dep_idx] = "libgfortran >=3.0,<4.0.0.a0"
            record["depends"] = depends
        elif ">=4" in depends[dep_idx]:
            # catches all of 4.*
            depends[dep_idx] = "libgfortran >=4.0.0,<5.0.0.a0"
            record["depends"] = depends


def _set_osx_virt_min(fn, record, min_vers):
    rconst = record.get("constrains", ())
    dep_idx = next(
        (q for q, dep in enumerate(rconst) if dep.split(" ")[0] == "__osx"), None
    )
    run_constrained = list(rconst)
    if dep_idx is None:
        run_constrained.append("__osx >=%s" % min_vers)
    if run_constrained:
        record["constrains"] = run_constrained


def _fix_libcxx(fn, record):
    record_name = record["name"]
    if record_name not in ["cctools", "ld64", "llvm-lto-tapi"]:
        return
    depends = record.get("depends", ())
    dep_idx = next(
        (q for q, dep in enumerate(depends) if dep.split(" ")[0] == "libcxx"), None
    )
    if dep_idx is not None:
        dep_parts = depends[dep_idx].split(" ")
        if len(dep_parts) >= 2 and dep_parts[1] == "4.0.1":
            # catches all of 4.*
            depends[dep_idx] = "libcxx >=4.0.1"
            record["depends"] = depends


def _extract_and_remove_vc_feature(record):
    features = record.get("features", "").split()
    vc_features = tuple(f for f in features if f.startswith("vc"))
    if not vc_features:
        return None
    non_vc_features = tuple(f for f in features if f not in vc_features)
    vc_version = int(vc_features[0][2:])  # throw away all but the first
    if non_vc_features:
        record["features"] = " ".join(non_vc_features)
    else:
        record["features"] = None
    return vc_version


def has_dep(record, name):
    return any(dep.split(" ")[0] == name for dep in record.get("depends", ()))


def get_python_abi(version, subdir, build=None):
    if build is not None:
        m = re.match(r".*py\d\d", build)
        if m:
            version = f"{m.group()[-2]}.{m.group()[-1]}"
    if version.startswith("2.7"):
        if subdir.startswith("linux"):
            return "cp27mu"
        return "cp27m"
    elif version.startswith("2.6"):
        if subdir.startswith("linux"):
            return "cp26mu"
        return "cp26m"
    elif version.startswith("3.4"):
        return "cp34m"
    elif version.startswith("3.5"):
        return "cp35m"
    elif version.startswith("3.6"):
        return "cp36m"
    elif version.startswith("3.7"):
        return "cp37m"
    elif version.startswith("3.8"):
        return "cp38"
    elif version.startswith("3.9"):
        return "cp39"
    return None


# Workaround for https://github.com/conda/conda-build/pull/3868
def remove_python_abi(record):
    if record["name"] in ["python", "python_abi", "pypy"]:
        return
    if not has_dep(record, "python_abi"):
        return
    depends = record.get("depends", [])
    record["depends"] = [dep for dep in depends if dep.split(" ")[0] != "python_abi"]


changes = set([])


def add_python_abi(record, subdir):
    record_name = record["name"]
    # Make existing python and python-dependent packages conflict with pypy
    if record_name == "python" and not record["build"].endswith("pypy"):
        version = record["version"]
        new_constrains = record.get("constrains", [])
        python_abi = get_python_abi(version, subdir)
        new_constrains.append(f"python_abi * *_{python_abi}")
        record["constrains"] = new_constrains
        return

    if (
        has_dep(record, "python")
        and not has_dep(record, "pypy")
        and not has_dep(record, "python_abi")
    ):
        python_abi = None
        new_constrains = record.get("constrains", [])
        build = record["build"]
        ver_strict_found = False
        ver_relax_found = False

        for dep in record.get("depends", []):
            dep_split = dep.split(" ")
            if dep_split[0] == "python":
                if len(dep_split) == 3:
                    continue
                if len(dep_split) == 1:
                    continue
                elif dep_split[1] == "<3":
                    python_abi = get_python_abi("2.7", subdir, build)
                elif dep_split[1].startswith(">="):
                    m = CB_PIN_REGEX.match(dep_split[1])
                    if m is None:
                        python_abi = get_python_abi("", subdir, build)
                    else:
                        lower = pad_list(m.group("lower").split("."), 2)[:2]
                        upper = pad_list(m.group("upper").split("."), 2)[:2]
                        if lower[0] == upper[0] and int(lower[1]) + 1 == int(upper[1]):
                            python_abi = get_python_abi(m.group("lower"), subdir, build)
                        else:
                            python_abi = get_python_abi("", subdir, build)
                else:
                    python_abi = get_python_abi(dep_split[1], subdir, build)
                if python_abi:
                    new_constrains.append(f"python_abi * *_{python_abi}")
                    changes.add((dep, f"python_abi * *_{python_abi}"))
                    ver_strict_found = True
                else:
                    ver_relax_found = True
        if not ver_strict_found and ver_relax_found:
            new_constrains.append("pypy <0a0")
        record["constrains"] = new_constrains


def _gen_new_index_per_key(index, subdir, index_key="", verbose=False):
    """Mutates the index by adjusting the values directly."""
    # deal with windows vc features
    if subdir.startswith("win-"):
        python_vc_deps = {
            "2.6": "vc 9.*",
            "2.7": "vc 9.*",
            "3.3": "vc 10.*",
            "3.4": "vc 10.*",
            "3.5": "vc 14.*",
            "3.6": "vc 14.*",
            "3.7": "vc 14.*",
        }
        for fn, record in index.items():
            record_name = record["name"]
            if record_name == "python" and "pypy" not in record["build"]:
                # remove the track_features key
                if "track_features" in record:
                    record["track_features"] = None
                # add a vc dependency
                if not any(d.startswith("vc") for d in record["depends"]):
                    depends = record["depends"]
                    depends.append(python_vc_deps[record["version"][:3]])
                    record["depends"] = depends
            elif "vc" in record.get("features", ""):
                # remove vc from the features key
                vc_version = _extract_and_remove_vc_feature(record)
                if vc_version:
                    # add a vc dependency
                    if not any(d.startswith("vc") for d in record["depends"]):
                        depends = record["depends"]
                        depends.append("vc %d.*" % vc_version)
                        record["depends"] = depends

    if verbose:
        print(f"Processing {index_key}", file=sys.stderr, flush=True)

    for fn, record in index.items():
        record_name = record["name"]
        deps = record.get("depends", ())

        ########################################
        # Ecosystem-wide patches for changes in
        # metapackages, etc.
        # Generally managed by conda-forge/core
        ########################################

        if "license" in record and "license_family" not in record and record["license"]:
            family = get_license_family(record["license"])
            if family:
                record["license_family"] = family

        if record.get("timestamp", 0) < 1604417730000:
            if subdir == "noarch":
                remove_python_abi(record)
            else:
                add_python_abi(record, subdir)

        # add track_features to old python_abi pypy packages
        if (
            record_name == "python_abi"
            and "pypy" in record["build"]
            and "track_features" not in record
        ):
            record["track_features"] = "pypy"

        # replace =2.7 with ==2.7.* for compatibility with older conda
        new_deps = []
        changed = False
        for dep in record.get("depends", []):
            dep_split = dep.split(" ")
            if (
                len(dep_split) == 2
                and dep_split[1].startswith("=")
                and not dep_split[1].startswith("==")
            ):
                split_or = dep_split[1].split("|")
                split_or[0] = "=" + split_or[0] + ".*"
                new_dep = dep_split[0] + " " + "|".join(split_or)
                changed = True
            else:
                new_dep = dep
            new_deps.append(new_dep)
        if changed:
            record["depends"] = new_deps
        del new_deps
        del changed

        # make sure pybind11 and pybind11-global have run constraints on
        # the abi metapackage
        # see https://github.com/conda-forge/conda-forge-repodata-patches-feedstock/issues/104  # noqa
        if (
            record_name in ["pybind11", "pybind11-global"]
            # this version has a constraint sometimes
            and (parse_version(record["version"]) <= parse_version("2.6.1"))
            and not any(
                c.startswith("pybind11-abi ") for c in record.get("constrains", [])
            )
        ):
            _add_pybind11_abi_constraint(fn, record)

        ############################################
        # Compilers, Runtimes and Related Patches
        ############################################

        if (
            record_name == "vs2015_runtime"
            and record.get("timestamp", 0) < 1633470721000
        ):
            pversion = parse_version(record["version"])
            vs2019_version = parse_version("14.29.30037")
            if pversion < vs2019_version:
                # make these conflict with ucrt
                new_constrains = record.get("constrains", [])
                new_constrains.append("ucrt <0a0")
                record["constrains"] = new_constrains

        # fix only packages built before the run_exports was corrected.
        if (
            any(dep == "libflang" or dep.startswith("libflang >=5.0.0") for dep in deps)
            and record.get("timestamp", 0) < 1611789153000
        ):
            record["depends"].append("libflang <6.0.0.a0")

        llvm_pkgs = ["clang", "clang-tools", "llvm", "llvm-tools", "llvmdev"]
        if record_name in llvm_pkgs:
            new_constrains = record.get("constrains", [])
            version = record["version"]
            if parse_version(version) < parse_version("17.0.0.a0"):
                for pkg in llvm_pkgs:
                    if record_name == pkg:
                        continue
                    if pkg in new_constrains:
                        del new_constrains[pkg]
                    if any(
                        constraint.startswith(f"{pkg} ")
                        for constraint in new_constrains
                    ):
                        continue
                    new_constrains.append(f"{pkg} {version}.*")
                record["constrains"] = new_constrains

        if record_name == "gcc_impl_{}".format(subdir):
            _relax_exact(fn, record, "binutils_impl_{}".format(subdir))

        # some symlinks changed in gfortran, so we need to adjust things
        # plus we missed a key version constraint
        if subdir in ["osx-64", "osx-arm64"] and record_name == "gfortran":
            for i, dep in enumerate(record["depends"]):
                if dep == f"gfortran_{subdir}":
                    record["depends"][i] = dep + " ==" + record["version"]

        # make sure the libgfortran version is bound from 3 to 4 for osx
        if subdir == "osx-64":
            _fix_libgfortran(fn, record)
            _fix_libcxx(fn, record)

            full_pkg_name = fn.replace(".tar.bz2", "")
            if full_pkg_name in OSX_SDK_FIXES:
                _set_osx_virt_min(fn, record, OSX_SDK_FIXES[full_pkg_name])

        # when making the glibc 2.28 sysroots, we found we needed to go back
        # and add the current repodata hack packages to the cos7 sysroots
        # for aarch64, ppc64le and s390x
        for __subdir in ["linux-s390x", "linux-aarch64", "linux-ppc64le"]:
            if (
                record_name in ["kernel-headers_" + __subdir, "sysroot_" + __subdir]
                and record.get("timestamp", 0) < 1682273081000  # 2023-04-23
                and record["version"] == "2.17"
            ):
                new_depends = record.get("depends", [])
                new_depends.append("_sysroot_" + __subdir + "_curr_repodata_hack 4.*")
                record["depends"] = new_depends

        # make old binutils packages conflict with the new sysroot packages
        # that have renamed the sysroot from conda_cos6 or conda_cos7 to just
        # conda
        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name
            in ["binutils", "binutils_impl_" + subdir, "ld_impl_" + subdir]
            and record.get("timestamp", 0) < 1589953178153  # 2020-05-20
        ):
            new_constrains = record.get("constrains", [])
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        # make sure the old compilers conflict with the new sysroot packages
        # and they only use libraries from the old compilers
        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name
            in ["gcc_impl_" + subdir, "gxx_impl_" + subdir, "gfortran_impl_" + subdir]
            and record["version"] in ["5.4.0", "7.2.0", "7.3.0", "8.2.0"]
        ):
            new_constrains = record.get("constrains", [])
            for pkg in ["libgcc-ng", "libstdcxx-ng", "libgfortran", "libgomp"]:
                new_constrains.append(
                    "{} 5.4.*|7.2.*|7.3.*|8.2.*|9.1.*|9.2.*".format(pkg)
                )
            new_constrains.append("binutils_impl_" + subdir + " <2.34")
            new_constrains.append("ld_impl_" + subdir + " <2.34")
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        # we pushed a few builds of the compilers past the list of versions
        # above which do not use the sysroot packages - this block catches those
        # it will also break some test builds of the new compilers but we should
        # not be using those anyways and they are marked as broken.
        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name
            in ["gcc_impl_" + subdir, "gxx_impl_" + subdir, "gfortran_impl_" + subdir]
            and record["version"] not in ["5.4.0", "7.2.0", "7.3.0", "8.2.0"]
            and not any(__r.startswith("sysroot_") for __r in record.get("depends", []))
            and record.get("timestamp", 0) < 1626220800000  # 2020-07-14
        ):
            new_constrains = record.get("constrains", [])
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        # all ctng activation packages that don't depend on the sysroot_*
        # packages are not compatible with the new sysroot_*-based compilers
        # root and cling must also be included as they have a builtin C++ interpreter
        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name
            in [
                "gcc_" + subdir,
                "gxx_" + subdir,
                "gfortran_" + subdir,
                "binutils_" + subdir,
                "gcc_bootstrap_" + subdir,
                "root_base",
                "cling",
            ]
            and not any(__r.startswith("sysroot_") for __r in record.get("depends", []))
            and record.get("timestamp", 0) < 1626220800000  # 2020-07-14
        ):
            new_constrains = record.get("constrains", [])
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        if (
            record_name == "gcc_impl_{}".format(subdir)
            and record["version"]
            in ["5.4.0", "7.2.0", "7.3.0", "8.2.0", "8.4.0", "9.3.0"]
            and record.get("timestamp", 0) < 1627530043000  # 2021-07-29
        ):
            new_depends = record.get("depends", [])
            new_depends.append("libgcc-ng <=9.3.0")
            record["depends"] = new_depends

        # old CDTs with the conda_cos6 or conda_cos7 name in the sysroot need to
        # conflict with the new CDT and compiler packages
        # all of the new CDTs and compilers depend on the sysroot_{subdir} packages
        # so we use a constraint on those
        if (
            subdir == "noarch"
            and (
                record_name.endswith("-cos6-x86_64")
                or record_name.endswith("-cos7-x86_64")
                or record_name.endswith("-cos7-aarch64")
                or record_name.endswith("-cos7-ppc64le")
            )
            and not record_name.startswith("sysroot-")
            and not any(__r.startswith("sysroot_") for __r in record.get("depends", []))
        ):
            if record_name.endswith("x86_64"):
                sys_subdir = "linux-64"
            elif record_name.endswith("aarch64"):
                sys_subdir = "linux-aarch64"
            elif record_name.endswith("ppc64le"):
                sys_subdir = "linux-ppc64le"

            new_constrains = record.get("constrains", [])
            if not any(__r.startswith("sysroot_") for __r in new_constrains):
                new_constrains.append("sysroot_" + sys_subdir + " ==99999999999")
                record["constrains"] = new_constrains

        llvm_pkgs = [
            "libclang",
            "clang",
            "clang-tools",
            "llvm",
            "llvm-tools",
            "llvmdev",
        ]
        for llvm in ["libllvm8", "libllvm9"]:
            if any(dep.startswith(llvm) for dep in deps):
                if record_name not in llvm_pkgs:
                    _relax_exact(fn, record, llvm, max_pin="x.x")
                else:
                    _relax_exact(fn, record, llvm, max_pin="x.x.x")

        # Properly depend on clangdev 5.0.0 flang* for flang 5.0
        if record_name == "flang":
            deps = record["depends"]
            if record["version"] == "5.0.0":
                deps += ["clangdev"]
                deps += ["flang"]

        # add as run_constrained for cling
        if (
            record_name == "cling"
            and record["version"] >= "0.8"
            and record.get("timestamp", 0) < 1667260800000  # 2022-11-01
        ):
            record.setdefault("constrains", []).extend(("gxx_linux-64 !=9.5.0",))

        ############################################
        # Custom Patches that cannot be YAML-ized
        ############################################

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


def _patch_indexes(repodata, subdir, verbose=False):
    for index_key in ["packages", "packages.conda"]:
        index = repodata[index_key]
        _gen_new_index_per_key(index, subdir, index_key=index_key, verbose=verbose)
        patch_yaml_edit_index(index, subdir, verbose=verbose)


def _add_removals(instructions, subdir, package_removal_keeplist=None):
    r = requests.get(
        "https://conda.anaconda.org/conda-forge/"
        "label/broken/%s/repodata.json" % subdir
    )

    if r.status_code != 200:
        r.raise_for_status()

    package_removal_keeplist = package_removal_keeplist or {}

    data = r.json()
    currvals = list(REMOVALS.get(subdir, []))
    for pkgs_section_key in ["packages", "packages.conda"]:
        for pkg_name in data.get(pkgs_section_key, []):
            if package_removal_keeplist:
                nm = data.get(pkgs_section_key, {}).get(pkg_name, {}).get("name", None)
                if nm in package_removal_keeplist:
                    continue
            currvals.append(pkg_name)

    instructions["remove"].extend(tuple(set(currvals)))


def _gen_patch_instructions(
    index,
    new_index,
    subdir,
    package_removal_keeplist=None,
    verbose=False,
):
    instructions = {
        "patch_instructions_version": 1,
        "packages": defaultdict(dict),
        "packages.conda": defaultdict(dict),
        "revoke": [],
        "remove": [],
    }

    _add_removals(
        instructions, subdir, package_removal_keeplist=package_removal_keeplist
    )

    # diff all items in the index and put any differences in the instructions
    for pkgs_section_key in ["packages", "packages.conda"]:
        if verbose:
            tqdm_progress = partial(
                tqdm,
                desc=f"Generating patch instructions {pkgs_section_key}",
                file=sys.stderr,
            )
        else:
            tqdm_progress = iter

        for fn in tqdm_progress(index.get(pkgs_section_key, {})):
            assert fn in new_index[pkgs_section_key]

            # replace any old keys
            for key in index[pkgs_section_key][fn]:
                assert key in new_index[pkgs_section_key][fn], (
                    key,
                    index[pkgs_section_key][fn],
                    new_index[pkgs_section_key][fn],
                )
                if (
                    index[pkgs_section_key][fn][key]
                    != new_index[pkgs_section_key][fn][key]
                ):
                    instructions[pkgs_section_key][fn][key] = new_index[
                        pkgs_section_key
                    ][fn][key]

            # add any new keys
            for key in new_index[pkgs_section_key][fn]:
                if key not in index[pkgs_section_key][fn]:
                    instructions[pkgs_section_key][fn][key] = new_index[
                        pkgs_section_key
                    ][fn][key]

    return instructions


def _do_subdir(subdir, verbose=False):
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_repodata_path = os.path.join(tmpdir, "repodata_from_packages.json.zst")
        ref_repodata_path = os.path.join(tmpdir, "repodata.json.zst")
        raw_url = f"{BASE_URL}/{subdir}/repodata_from_packages.json.zst"
        urllib.request.urlretrieve(raw_url, raw_repodata_path)
        ref_url = f"{BASE_URL}/{subdir}/repodata.json.zst"
        urllib.request.urlretrieve(ref_url, ref_repodata_path)

        with zstandard.open(raw_repodata_path) as fh:
            repodata = json.load(fh)
        with zstandard.open(ref_repodata_path) as fh:
            ref_repodata = json.load(fh)

        # Copying large python dictionaries is slow, just reload the repodata
        with zstandard.open(raw_repodata_path) as fh:
            new_index = json.load(fh)

        prefix_dir = os.getenv("PREFIX", "tmp")
        prefix_subdir = join(prefix_dir, subdir)
        if not isdir(prefix_subdir):
            os.makedirs(prefix_subdir)

        # Step 2a. Generate a new index -- in place operation
        _patch_indexes(new_index, subdir, verbose=verbose)

        # Step 2b. Generate the instructions by diff'ing the indices.
        instructions = _gen_patch_instructions(
            repodata, new_index, subdir, verbose=verbose
        )

        # Step 2c. Output this to $PREFIX so that we bundle the JSON files.
        patch_instructions_path = join(prefix_subdir, "patch_instructions.json")
        with open(patch_instructions_path, "w") as fh:
            json.dump(
                instructions, fh, indent=2, sort_keys=True, separators=(",", ": ")
            )

        # Step 3. Show the diff
        new_repodata = _apply_instructions(subdir, repodata, instructions)
        return subdir, show_record_diffs(
            subdir, ref_repodata, new_repodata, False, group_diffs=True
        )


def main():
    if "CF_SUBDIR" in os.environ:
        # For local debugging
        subdirs = os.environ["CF_SUBDIR"].split(";")
    else:
        subdirs = SUBDIRS

    with ProcessPoolExecutor(
        max_workers=int(os.environ["CPU_COUNT"]) if "CPU_COUNT" in os.environ else None
    ) as exc:
        futs = [exc.submit(_do_subdir, subdir) for subdir in subdirs]
        for fut in tqdm(
            as_completed(futs), desc="patching repodata", total=len(subdirs)
        ):
            subdir, vals = fut.result()
            print("\n", flush=True, end="")
            print("=" * 80, flush=True)
            print("=" * 80, flush=True)
            print(subdir, flush=True)
            for key, val in vals.items():
                for v in val:
                    print(v, flush=True)
                for k in key:
                    print(k, flush=True)
            print("\n", flush=True, end="")


if __name__ == "__main__":
    sys.exit(main())
