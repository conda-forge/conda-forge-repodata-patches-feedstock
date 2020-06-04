# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from collections import defaultdict
import copy
import json
import os
from os.path import join, isdir
import sys
import tqdm
import re
import requests
import pkg_resources

import requests

from get_license_family import get_license_family

CHANNEL_NAME = "conda-forge"
CHANNEL_ALIAS = "https://conda.anaconda.org"
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

OSX_SDK_FIXES = {
    'nodejs-12.8.0-hec2bf70_1': '10.10',
    'nodejs-12.1.0-h6de7cb9_1': '10.10',
    'nodejs-12.3.1-h6de7cb9_0': '10.10',
    'nodejs-12.9.0-hec2bf70_0': '10.10',
    'nodejs-12.9.1-hec2bf70_0': '10.10',
    'nodejs-12.7.0-hec2bf70_1': '10.10',
    'nodejs-12.10.0-hec2bf70_0': '10.10',
    'nodejs-12.4.0-h6de7cb9_0': '10.10',
    'nodejs-12.11.1-hec2bf70_0': '10.10',
    'nodejs-12.7.0-h6de7cb9_0': '10.10',
    'nodejs-12.3.0-h6de7cb9_0': '10.10',
    'nodejs-10.16.3-hec2bf70_0': '10.10',
    'nodejs-12.12.0-hfddbe92_0': '10.10',
    'nodejs-12.8.1-hec2bf70_0': '10.10',
    'javafx-sdk-11.0.4-h6dcaf97_1': '10.11',
    'javafx-sdk-12.0.2-h6dcaf97_1': '10.11',
    'javafx-sdk-12.0.2-h6dcaf97_0': '10.11',
    'javafx-sdk-11.0.4-h6dcaf97_0': '10.11',
    'qt-5.12.1-h1b46049_0': '10.12',
    'qt-5.9.7-h8cf7e54_3': '10.12',
    'qt-5.9.7-h93ee506_0': '10.12',
    'qt-5.9.7-h93ee506_1': '10.12',
    'qt-5.12.5-h1b46049_0': '10.12',
    'qt-5.9.7-h93ee506_2': '10.12',
    'openmpi-mpicxx-4.0.1-h6052eea_2': '10.12',
    'openmpi-mpicxx-4.0.1-h6052eea_1': '10.12',
    'openmpi-mpicxx-4.0.1-h6052eea_0': '10.12',
    'openmpi-mpicxx-4.0.1-hc9558a2_2': '10.12',
    'openmpi-mpicxx-4.0.1-hc9558a2_0': '10.12',
    'openmpi-mpicxx-4.0.1-hc9558a2_1': '10.12',
    'freecad-0.18.3-py37h4764a83_2': '10.12',
    'freecad-0.18.3-py37hc453731_1': '10.12',
    'freecad-0.18.4-py37hab2b3aa_1': '10.12',
    'freecad-0.18.4-py37hab2b3aa_0': '10.12',
    'openmpi-mpicc-4.0.1-h24e1f75_1': '10.12',
    'openmpi-mpicc-4.0.1-h24e1f75_2': '10.12',
    'openmpi-mpicc-4.0.1-h24e1f75_0': '10.12',
    'openmpi-mpicc-4.0.1-h516909a_0': '10.12',
    'openmpi-mpicc-4.0.1-h516909a_1': '10.12',
    'openmpi-mpicc-4.0.1-h516909a_2': '10.12',
    'openmpi-mpifort-4.0.1-h939af09_0': '10.12',
    'openmpi-mpifort-4.0.1-h6ad152f_2': '10.12',
    'openmpi-mpifort-4.0.1-h939af09_2': '10.12',
    'openmpi-mpifort-4.0.1-h939af09_1': '10.12',
    'openmpi-mpifort-4.0.1-he991be0_0': '10.12',
    'openmpi-mpifort-4.0.1-he991be0_1': '10.12',
    'openmpi-mpifort-4.0.1-he991be0_2': '10.12',
    'reaktoro-1.0.7-py37h99eb986_0': '10.12',
    'reaktoro-1.0.7-py37h99eb986_1': '10.12',
    'reaktoro-1.0.7-py36h99eb986_0': '10.12',
    'reaktoro-1.0.7-py36h99eb986_1': '10.12',
    'pyqt-5.12.3-py38he22c54c_1': '10.12',
    'pyqt-5.9.2-py37h2a560b1_0': '10.12',
    'pyqt-5.12.3-py36he22c54c_1': '10.12',
    'pyqt-5.9.2-py27h2a560b1_4': '10.12',
    'pyqt-5.9.2-py27h2a560b1_1': '10.12',
    'pyqt-5.9.2-py37h2a560b1_4': '10.12',
    'pyqt-5.9.2-py36h2a560b1_3': '10.12',
    'pyqt-5.9.2-py27h2a560b1_2': '10.12',
    'pyqt-5.9.2-py36h2a560b1_1': '10.12',
    'pyqt-5.12.3-py27h2a560b1_0': '10.12',
    'pyqt-5.12.3-py37h2a560b1_0': '10.12',
    'pyqt-5.12.3-py27he22c54c_0': '10.12',
    'pyqt-5.12.3-py27he22c54c_1': '10.12',
    'pyqt-5.9.2-py37h2a560b1_2': '10.12',
    'pyqt-5.9.2-py37h2a560b1_1': '10.12',
    'pyqt-5.9.2-py36h2a560b1_0': '10.12',
    'pyqt-5.9.2-py36h2a560b1_4': '10.12',
    'pyqt-5.9.2-py27h2a560b1_0': '10.12',
    'pyqt-5.9.2-py37h2a560b1_3': '10.12',
    'pyqt-5.12.3-py38he22c54c_0': '10.12',
    'pyqt-5.9.2-py27h2a560b1_3': '10.12',
    'pyqt-5.9.2-py36h2a560b1_2': '10.12',
    'pyqt-5.12.3-py37he22c54c_0': '10.12',
    'pyqt-5.12.3-py36he22c54c_0': '10.12',
    'pyqt-5.12.3-py37he22c54c_1': '10.12',
    'pyqt-5.12.3-py36h2a560b1_0': '10.12',
    'ldas-tools-al-2.6.3-hf543496_0': '10.12',
    'ldas-tools-al-2.6.3-hf543496_1': '10.12',
    'ldas-tools-al-2.6.4-h4f290e7_1': '10.12',
    'ldas-tools-al-2.6.4-h4f290e7_0': '10.12',
    'openmpi-4.0.1-ha90c164_2': '10.12',
    'openmpi-4.0.1-ha90c164_0': '10.12',
    'openmpi-4.0.1-hfcebdee_2': '10.12',
    'openmpi-4.0.1-ha90c164_1': '10.12',
    'openmpi-4.0.1-hc99cbb1_1': '10.12',
    'openmpi-4.0.1-hc99cbb1_0': '10.12',
    'openmpi-4.0.1-hc99cbb1_2': '10.12',
}


def _add_removals(instructions, subdir):
    r = requests.get(
        "https://conda.anaconda.org/conda-forge/"
        "label/broken/%s/repodata.json" % subdir
    )

    if r.status_code != 200:
        r.raise_for_status()

    data = r.json()
    currvals = list(REMOVALS.get(subdir, []))
    for pkg_name in data["packages"]:
        currvals.append(pkg_name)

    instructions["remove"].extend(tuple(set(currvals)))


def _gen_patch_instructions(index, new_index, subdir):
    instructions = {
        "patch_instructions_version": 1,
        "packages": defaultdict(dict),
        "revoke": [],
        "remove": [],
    }

    _add_removals(instructions, subdir)

    # diff all items in the index and put any differences in the instructions
    for fn in index:
        assert fn in new_index

        # replace any old keys
        for key in index[fn]:
            assert key in new_index[fn], (key, index[fn], new_index[fn])
            if index[fn][key] != new_index[fn][key]:
                instructions['packages'][fn][key] = new_index[fn][key]

        # add any new keys
        for key in new_index[fn]:
            if key not in index[fn]:
                instructions['packages'][fn][key] = new_index[fn][key]

    return instructions


def has_dep(record, name):
    return any(dep.split(' ')[0] == name for dep in record.get('depends', ()))


def get_python_abi(version, subdir, build=None):
    if build is not None:
        if re.match(".*py\d\d", build):
            version = f"{build[2]}.{build[3]}"
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
    return None


# Workaround for https://github.com/conda/conda-build/pull/3868
def remove_python_abi(record):
    if record['name'] in ['python', 'python_abi', 'pypy']:
        return
    if not has_dep(record, 'python_abi'):
        return
    depends = record.get('depends', [])
    record['depends'] = [dep for dep in depends if dep.split(" ")[0] != "python_abi"]


changes = set([])

def add_python_abi(record, subdir):
    record_name = record['name']
    # Make existing python and python-dependent packages conflict with pypy
    if record_name == "python" and not record['build'].endswith("pypy"):
        version = record['version']
        new_constrains = record.get('constrains', [])
        python_abi = get_python_abi(version, subdir)
        new_constrains.append(f"python_abi * *_{python_abi}")
        record['constrains'] = new_constrains
        return

    if has_dep(record, 'python') and not has_dep(record, 'pypy') and not has_dep(record, 'python_abi'):
        python_abi = None
        new_constrains = record.get('constrains', [])
        build = record["build"]
        ver_strict_found = False
        ver_relax_found = False

        for dep in record.get('depends', []):
            dep_split = dep.split(' ')
            if dep_split[0] == 'python':
                if len(dep_split) == 3:
                    continue
                if len(dep_split) == 1:
                    continue
                elif dep_split[1] == "<3":
                    python_abi = get_python_abi("2.7", subdir, build)
                elif dep_split[1].startswith(">="):
                    m = cb_pin_regex.match(dep_split[1])
                    if m == None:
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
        record['constrains'] = new_constrains


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

        if subdir == 'noarch':
            remove_python_abi(record)
        else:
            add_python_abi(record, subdir)

        if "license" in record and "license_family" not in record and record["license"]:
            family = get_license_family(record["license"])
            if family:
                record['license_family'] = family

        # remove dependency from constrains for twisted
        if record_name == "twisted":
            new_constrains = [dep for dep in record.get('constrains', ())
                              if not dep.startswith("pyobjc-framework-cococa")]
            if new_constrains != record.get('constrains', ()):
                record['constrains'] = new_constrains

        if record_name == "arrow-cpp":
            if not any(dep.split(' ')[0] == "arrow-cpp-proc" for dep in record.get('constrains', ())):
                if 'constrains' in record:
                    record['constrains'].append("arrow-cpp-proc * cpu")
                else:
                    record['constrains'] = ["arrow-cpp-proc * cpu"]

        if record_name == "pyarrow":
            if not any(dep.split(' ')[0] == "arrow-cpp-proc" for dep in record.get('constrains', ())):
                if 'constrains' in record:
                    record['constrains'].append("arrow-cpp-proc * cpu")
                else:
                    record['constrains'] = ["arrow-cpp-proc * cpu"]

        # distributed <2.11.0 does not work with msgpack-python >=1.0
        # newer versions of distributed require at least msgpack-python >=0.6.0
        # so we can fix cases where msgpack-python is unbounded
        # https://github.com/conda-forge/distributed-feedstock/pull/114
        if record_name == 'distributed':
            if 'msgpack-python' in record['depends']:
                i = record['depends'].index('msgpack-python')
                record['depends'][i] = 'msgpack-python <1.0.0'

        # python-language-server <=0.31.9 requires pyflakes <2.2.2
        # included explicitly in 0.31.10+
        # https://github.com/conda-forge/python-language-server-feedstock/pull/50
        version = record['version']
        if record_name == 'python-language-server':
            pversion = pkg_resources.parse_version(version)
            v0_31_9 = pkg_resources.parse_version('0.31.9')
            if pversion <= v0_31_9 and 'pyflakes >=1.6.0' in record['depends']:
                i = record['depends'].index('pyflakes >=1.6.0')
                record['depends'][i] = 'pyflakes >=1.6.0,<2.2.0'

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

        if 're2' in deps and record.get('timestamp', 0) < 1588349339243:
            _rename_dependency(fn, record, "re2", "re2 <2020.05.01")

        _relax_libssh2_1_x_pinning(fn, record)

        if any(dep.startswith("gf2x") for dep in deps):
            _pin_stricter(fn, record, "gf2x", "x.x")

        if any(dep.startswith("libnetcdf >=4.7.3") for dep in deps):
            _pin_stricter(fn, record, "libnetcdf", "x.x.x.x")

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

        if 'snappy >=1.1.7,<1.1.8.0a0' in deps:
            i = record['depends'].index('snappy >=1.1.7,<1.1.8.0a0')
            record['depends'][i] = 'snappy >=1.1.7,<2.0.0.0a0'

        if 'abseil-cpp' in deps:
            i = record['depends'].index('abseil-cpp')
            record['depends'][i] = 'abseil-cpp =20190808'

        # Filter by timestamp as pythia8 also contains python bindings that shouldn't be pinned
        if 'pythia8' in deps and record.get('timestamp', 0) < 1584264455759:
            i = record['depends'].index('pythia8')
            record['depends'][i] = 'pythia8 >=8.240,<8.300.0a0'

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

        if record_name in llvm_pkgs:
            new_constrains = record.get('constrains', [])
            version = record["version"]
            for pkg in llvm_pkgs:
                if record_name == pkg:
                    continue
                new_constrains.append(f'{pkg} {version}.*')
            record['constrains'] = new_constrains

        # make sure the libgfortran version is bound from 3 to 4 for osx
        if subdir == "osx-64":
            _fix_libgfortran(fn, record)
            _fix_libcxx(fn, record)

            full_pkg_name = fn.replace('.tar.bz2', '')
            if full_pkg_name in OSX_SDK_FIXES:
                _set_osx_virt_min(fn, record, OSX_SDK_FIXES[full_pkg_name])

        # make old binutils packages conflict with the new sysroot packages
        # that have renamed the sysroot from conda_cos6 or conda_cos7 to just
        # conda
        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name in [
                "binutils", "binutils_impl_" + subdir, "ld_impl_" + subdir]
            and record.get('timestamp', 0) < 1589953178153  # 2020-05-20
        ):
            new_constrains = record.get('constrains', [])
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name in [
                "gcc_impl_" + subdir, "gxx_impl_" + subdir, "gfortran_impl_" + subdir]
            and record['version'] in ['5.4.0', '7.2.0', '7.3.0', '8.2.0']
        ):
            new_constrains = record.get('constrains', [])
            for pkg in ["libgcc-ng", "libstdcxx-ng", "libgfortran", "libgomp"]:
                new_constrains.append("{} 5.4.*|7.2.*|7.3.*|8.2.*|9.1.*|9.2.*".format(pkg))
            new_constrains.append("binutils_impl_" + subdir + " <2.34")
            new_constrains.append("ld_impl_" + subdir + " <2.34")
            record["constrains"] = new_constrains

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


def _set_osx_virt_min(fn, record, min_vers):
    rconst = record.get("constrains", ())
    dep_idx = next(
        (q for q, dep in enumerate(rconst)
         if dep.split(' ')[0] == "__osx"),
        None
    )
    run_constrained = list(rconst)
    if dep_idx is None:
        run_constrained.append("__osx >=%s" % min_vers)
    if run_constrained:
        record['constrains'] = run_constrained


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


def pad_list(l, num):
    if len(l) >= num:
        return l
    return l + [0]*(num - len(l))


def get_upper_bound(version, max_pin):
    num_x = max_pin.count("x")
    ver = pad_list(version.split("."), num_x)
    ver[num_x:] = ["0"]*(len(ver)-num_x)
    ver[num_x-1] = str(int(ver[num_x-1])+1)
    return ".".join(ver)


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
                upper_bound = get_upper_bound(dep_parts[1], max_pin) + "a0"
                depends[dep_idx] = "{} >={},<{}".format(*dep_parts[:2], upper_bound)
            else:
                depends[dep_idx] = "{} >={}".format(*dep_parts[:2])
            record['depends'] = depends


def _match_strict_libssh2_1_x_pin(dep):
    if dep.startswith("libssh2 >=1.8.0,<1.9.0a0"):
        return True
    if dep.startswith("libssh2 >=1.8.1,<1.9.0a0"):
        return True
    if dep.startswith("libssh2 >=1.8.2,<1.9.0a0"):
        return True
    if dep.startswith("libssh2 1.8.*"):
        return True

    return False


def _relax_libssh2_1_x_pinning(fn, record):
    depends = record.get("depends", ())
    dep_idx = next(
        (q for q, dep in enumerate(depends)
         if _match_strict_libssh2_1_x_pin(dep)),
        None
    )

    if dep_idx is not None:
        depends[dep_idx] = "libssh2 >=1.8.0,<2.0.0a0"


cb_pin_regex = re.compile(r"^>=(?P<lower>\d(\.\d+)*a?),<(?P<upper>\d(\.\d+)*)a0$")

def _pin_stricter(fn, record, fix_dep, max_pin):
    depends = record.get("depends", ())
    dep_indices = [q for q, dep in enumerate(depends) if dep.split(' ')[0] == fix_dep]
    for dep_idx in dep_indices:
        dep_parts = depends[dep_idx].split(" ")
        if len(dep_parts) not in [2, 3]:
            continue
        m = cb_pin_regex.match(dep_parts[1])
        if m is None:
            continue
        lower = m.group("lower")
        upper = m.group("upper").split(".")
        new_upper = get_upper_bound(lower, max_pin).split(".")
        upper = pad_list(upper, len(new_upper))
        new_upper = pad_list(new_upper, len(upper))
        if tuple(upper) > tuple(new_upper):
            if str(new_upper[-1]) != "0":
                new_upper += ["0"]
            depends[dep_idx] = "{} >={},<{}a0".format(dep_parts[0], lower, ".".join(new_upper))
            if len(dep_parts) == 3:
                depends[dep_idx] = "{} {}".format(depends[dep_idx], dep_parts[2])
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
    if "CF_SUBDIR" in os.environ:
        # For local debugging
        subdirs = os.environ["CF_SUBDIR"].split(";")
    else:
        subdirs = SUBDIRS
    for subdir in tqdm.tqdm(subdirs, desc="Downloading repodata"):
        repodata_url = "/".join(
            (CHANNEL_ALIAS, CHANNEL_NAME, subdir, "repodata_from_packages.json"))
        response = requests.get(repodata_url)
        response.raise_for_status()
        repodatas[subdir] = response.json()

    # Step 2. Create all patch instructions.
    prefix_dir = os.getenv("PREFIX", "tmp")
    for subdir in subdirs:
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
