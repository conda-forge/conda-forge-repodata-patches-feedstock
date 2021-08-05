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
    "osx-arm64",
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
    "osx-arm64": (
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
        m = re.match(".*py\d\d", build)
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

        if record_name == "great-expectations" and record.get("timestamp", 0) < 1616454000000:
            old_constrains = record.get("constrains", [])
            new_constrains = [f"{constraint},<1.4" if constraint == "sqlalchemy >=1.2" else constraint for constraint in old_constrains]
            new_constrains = new_constrains if new_constrains != old_constrains else new_constrains + ["sqlalchemy <1.4"]
            record["constrains"] = new_constrains

        if record.get('timestamp', 0) < 1604417730000:
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

        if record_name == "starlette-base":
            if not any(dep.split(' ')[0] == "starlette" for dep in record.get('constrains', ())):
                if 'constrains' in record:
                    record['constrains'].append(f"starlette {record['version']}")
                else:
                    record['constrains'] = [f"starlette {record['version']}"]

        if record_name == "pytorch" and record.get('timestamp', 0) < 1610297816658:
            # https://github.com/conda-forge/pytorch-cpu-feedstock/issues/29
            if not any(dep.split(' ')[0] == 'typing_extensions'
                       for dep in record.get('depends', ())):
                if 'depends' in record:
                    record['depends'].append("typing_extensions")
                else:
                    record['depends'] = ["typing_extensions"]

        if record_name == "ipython" and record.get('timestamp', 0) < 1609621539000:
            # https://github.com/conda-forge/ipython-feedstock/issues/127
            if any(dep.split(' ')[0] == "jedi" for dep in record.get('depends', ())):
                record['depends'].append('jedi <0.18')

        if record_name == "kartothek" and record.get('timestamp', 0) < 1611565264000:
            # https://github.com/conda-forge/kartothek-feedstock/issues/36
            if "zstandard" in record['depends']:
                i = record['depends'].index('zstandard')
                record['depends'][i] = 'zstandard <0.15'

        if record_name == "gitdb" and record['version'].startswith('4.0.') and 'smmap >=3.0.1' in record['depends']:
            i = record['depends'].index('smmap >=3.0.1')
            record['depends'][i] = 'smmap >=3.0.1,<4'

        if record_name == "arrow-cpp":
            if not any(dep.split(' ')[0] == "arrow-cpp-proc" for dep in record.get('constrains', ())):
                if 'constrains' in record:
                    record['constrains'].append("arrow-cpp-proc * cpu")
                else:
                    record['constrains'] = ["arrow-cpp-proc * cpu"]

            if "aws-sdk-cpp" in record['depends']:
                i = record['depends'].index('aws-sdk-cpp')
                record['depends'][i] = 'aws-sdk-cpp 1.7.164'

            # arrow-cpp builds done with numpy<1.16.6 are incompatible with numpy 1.20
            # We have been building with numpy 1.16.6 since 1612266172867
            # The underlying issue is https://github.com/numpy/numpy/issues/17913
            if record.get('timestamp', 0) < 1607959235411 and any(dep.split(' ')[0] == 'numpy' for dep in record.get('depends', ())):
                _pin_stricter(fn, record, "numpy", "x", "1.20")

        if record_name == "pyarrow":
            if not any(dep.split(' ')[0] == "arrow-cpp-proc" for dep in record.get('constrains', ())):
                if 'constrains' in record:
                    record['constrains'].append("arrow-cpp-proc * cpu")
                else:
                    record['constrains'] = ["arrow-cpp-proc * cpu"]

            # pyarrow builds done with numpy<1.16.6 are incompatible with numpy 1.20
            # We have been building with numpy 1.16.6 since 1612266172867
            # The underlying issue is https://github.com/numpy/numpy/issues/17913
            if record.get('timestamp', 0) < 1607959235411 and any(dep.split(' ')[0] == 'numpy' for dep in record.get('depends', ())):
                _pin_stricter(fn, record, "numpy", "x", "1.20")

        if record_name == "kartothek":
            if record["version"] in ["3.15.0", "3.15.1", "3.16.0"] \
                    and "pyarrow >=0.13.0,!=0.14.0,<2" in record["depends"]:
                i = record["depends"].index("pyarrow >=0.13.0,!=0.14.0,<2")
                record["depends"][i] = "pyarrow >=0.17.1,<2"

        if record_name == 'distributed':
            # distributed <2.11.0 does not work with msgpack-python >=1.0
            # newer versions of distributed require at least msgpack-python >=0.6.0
            # so we can fix cases where msgpack-python is unbounded
            # https://github.com/conda-forge/distributed-feedstock/pull/114
            if 'msgpack-python' in record['depends']:
                i = record['depends'].index('msgpack-python')
                record['depends'][i] = 'msgpack-python <1.0.0'

            # click 8 broke distributed prior to 2021.5.0.
            # This has been corrected in PR:
            # https://github.com/conda-forge/distributed-feedstock/pull/165
            pversion = pkg_resources.parse_version(record['version'])
            v2021_5_0 = pkg_resources.parse_version('2021.5.0')
            if pversion < v2021_5_0 and 'click >=6.6' in record['depends']:
                i = record['depends'].index('click >=6.6')
                record['depends'][i] = 'click >=6.6,<8.0.0'

        if record_name == 'fastparquet':
            # fastparquet >= 0.7.0 requires pandas >= 1.0.0
            # This was taken care of by rebuilding the fastparquet=0.7.0 release
            # https://github.com/conda-forge/fastparquet-feedstock/pull/47
            # We patch the pandas requirement here to prevent the original
            # fastparquet build from being installed
            pversion = pkg_resources.parse_version(record['version'])
            v0_7_0 = pkg_resources.parse_version('0.7.0')
            if pversion == v0_7_0 and 'pandas >=0.19' in record['depends']:
                i = record['depends'].index('pandas >=0.19')
                record['depends'][i] = 'pandas >=1.0.0'

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

        # aioftp >=0.17.0 requires python >=3.7
        # aioftp 0.17.x was incorrectly built with 3.6 support
        # https://github.com/conda-forge/aioftp-feedstock/pull/12
        version = record['version']
        if record_name == 'aioftp':
            pversion = pkg_resources.parse_version(version)
            base_version = pkg_resources.parse_version('0.17.0')
            max_version = pkg_resources.parse_version('0.17.2')
            if base_version <= pversion <= max_version and 'python >=3.6' in record['depends']:
                i = record['depends'].index('python >=3.6')
                record['depends'][i] = 'python >=3.7'

        # numpydoc >=1.0.0 requires python >=3.5
        # https://github.com/conda-forge/numpydoc-feedstock/pull/14
        version = record['version']
        if record_name == 'numpydoc':
            pversion = pkg_resources.parse_version(version)
            v1_0_0 = pkg_resources.parse_version('1.0.0')
            v1_1_0 = pkg_resources.parse_version('1.1.0')
            if v1_0_0 <= pversion <= v1_1_0 and 'python' in record['depends']:
                i = record['depends'].index('python')
                record['depends'][i] = 'python >=3.5'

        # pip >=21 requires python >=3.6 but the first build has >=3
        # https://github.com/conda-forge/pip-feedstock/pull/68
        if record_name == 'pip':
            if record['version'] == "21.0" and record['build'] == "pyhd8ed1ab_0":
                i = record['depends'].index('python >=3')
                record['depends'][i] = 'python >=3.6'

        # some versions mpi4py-fft are not compatible with MKL
        # https://github.com/conda-forge/mpi4py-fft-feedstock/issues/20
        if record_name == "mpi4py-fft" and record.get('timestamp', 0) < 1619448232206:
            if "nomkl" not in record["depends"]:
                record["depends"].append("nomkl")

        # nc-time-axis 1.3.0 and 1.3.1 require a minimum pin of cftime >=1.5
        version = record["version"]
        if record_name == "nc-time-axis":
            pversion = pkg_resources.parse_version(version)
            v1_3_0 = pkg_resources.parse_version("1.3.0")
            v1_3_1 = pkg_resources.parse_version("1.3.1")
            pdependency = "cftime"
            if pversion in [v1_3_0, v1_3_1] and pdependency in record["depends"]:
                i = record["depends"].index(pdependency)
                record["depends"][i] = "cftime >=1.5"

        # chemfiles-python 0.10.1 require chemfiles-lib 0.10.1 but build 0
        # asks for 0.10.*
        # https://github.com/conda-forge/chemfiles-python-feedstock/pull/18
        if record_name == "chemfiles-python":
            if record["version"] == "0.10.1" and record["build"].endswith("_0"):
                i = record['depends'].index('chemfiles-lib 0.10.*')
                record['depends'][i] = 'chemfiles-lib >=0.10.1,<0.11'

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

        if "libiconv >=1.15,<1.16.0a0" in deps:
            _pin_looser(fn, record, "libiconv", upper_bound="1.17.0")

        if any(dep.startswith("expat >=2.2.") for dep in deps) or \
                any(dep.startswith("expat >=2.3.") for dep in deps):
            _pin_looser(fn, record, "expat", max_pin="x")

        if any(dep.startswith("mysql-libs >=8.0.") for dep in deps):
            _pin_looser(fn, record, "mysql-libs", max_pin="x.x")

        if 're2' in deps and record.get('timestamp', 0) < 1588349339243:
            _rename_dependency(fn, record, "re2", "re2 <2020.05.01")

        if 'libffi' in deps and record.get('timestamp', 0) < 1605980936031:
            _rename_dependency(fn, record, "libffi", "libffi <3.3.0.a0")

        if ('libthrift >=0.14.0,<0.15.0a0' in deps or 'libthrift >=0.14.1,<0.15.0a0' in deps) and record.get('timestamp', 0) < 1624268394471:
            _pin_stricter(fn, record, "libthrift", "x.x.x")

        if any(dep.startswith('spdlog >=1.8') for dep in deps) and record.get('timestamp', 0) < 1626942511225:
            _pin_stricter(fn, record, "spdlog", "x.x")

        if 'libffi >=3.2.1,<4.0a0' in deps and record.get('timestamp', 0) < 1605980936031:
            _pin_stricter(fn, record, "libffi", "x.x")

        _relax_libssh2_1_x_pinning(fn, record)

        if any(dep.startswith("gf2x") for dep in deps):
            _pin_stricter(fn, record, "gf2x", "x.x")

        if any(dep.startswith("libnetcdf >=4.7.3") for dep in deps):
            _pin_stricter(fn, record, "libnetcdf", "x.x.x.x")

        if any(dep.startswith("libarchive >=3.3") for dep in deps):
            _pin_looser(fn, record, "libarchive", upper_bound="3.6.0")

        # fix only packages built before the run_exports was corrected.
        if any(dep == "libflang" or dep.startswith("libflang >=5.0.0") for dep in deps) and record.get('timestamp', 0) < 1611789153000:
            record["depends"].append("libflang <6.0.0.a0")

        if any(dep.startswith("libignition-") or dep == 'libsdformat' for dep in deps):
            for dep_idx, _ in enumerate(deps):
                dep = record['depends'][dep_idx]
                if dep.startswith('libignition-'):
                    _pin_looser(fn, record, dep.split(" ")[0], max_pin="x")
                if dep.startswith('libsdformat '):
                    _pin_looser(fn, record, dep.split(" ")[0], max_pin="x")

        # this doesn't seem to match the _pin_looser or _pin_stricter patterns
        # nor _replace_pin
        if record_name == "jedi" and record.get("timestamp", 0) < 1592619891258:
            for i, dep in enumerate(record["depends"]):
                if dep.startswith("parso") and "<" not in dep:
                    _dep_parts = dep.split(" ")
                    _dep_parts[1] = _dep_parts[1] + ",<0.8.0"
                    record["depends"][i] = " ".join(_dep_parts)

        # Integration between mdtraj and astunparse 1.6.3 on python 3.8 is
        # broken, which was pinned for new builds in
        # https://github.com/conda-forge/mdtraj-feedstock/pull/30 but should
        # also be corrected on older builds
        if (record_name == "mdtraj" and
            record["version"] == "1.9.5" and
            "py38" in record['build'] and
            "astunparse" in record['depends'] and
            "astunparse <=1.6.2" not in record['depends']):
            i = record['depends'].index('astunparse')
            record['depends'][i] = 'astunparse <=1.6.2'

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

        if any(dep.startswith("zstd >=1.4") for dep in deps):
            _pin_looser(fn, record, "zstd", max_pin="x.x")

        # We pin MPI packages loosely so as to rely on their ABI compatibility
        if any(dep.startswith("openmpi >=4.0") for dep in deps):
            _pin_looser(fn, record, "openmpi", upper_bound="5.0")
        if any(dep.startswith("mpich >=3.3") for dep in deps):
            _pin_looser(fn, record, "mpich", upper_bound="4.0")
        if any(dep.startswith("mpich >=3.4,") for dep in deps):
            _pin_looser(fn, record, "mpich", upper_bound="4.0")
        if any(dep.startswith("mpich >=3.4.1,") for dep in deps):
            _pin_looser(fn, record, "mpich", upper_bound="4.0")

        # TBB 2021 (oneTBB 2021) is incompatible with previous releases.
        if has_dep(record, "tbb") and record.get('timestamp', 0) < 1614809400000:
            for i, dep in enumerate(deps):
                if dep == "tbb" or any(dep.startswith(f"tbb >={i}") for i in range(2017, 2021)) or dep.startswith("tbb >=4.4"):
                    deps.append("tbb <2021.0.0a0")
                    break

        # cuTENSOR 1.3.x is binary incompatible with 1.2.x. Let's just pin exactly since
        # it appears semantic versioning is not guaranteed.
        _replace_pin("cutensor >=1.2.2.5,<2.0a0", "cutensor =1.2.2.5", deps, record)
        _replace_pin("cutensor >=1.2.2.5,<2.0a0", "cutensor =1.2.2.5", record.get("constrains", []), record, target='constrains')

        # ROOT 6.22.6 contained an ABI break, we'll always pin on patch releases from now on
        if has_dep(record, "root_base"):
            for i, dep in enumerate(deps):
                if not ("root_base" in dep and "<6.23.0a0" in dep):
                    continue
                if ">=6.22.0," in dep or ">=6.22.2," in dep or ">=6.22.4," in dep:
                    deps.append("root_base <6.22.5a0")
                elif ">=6.22.6," in dep:
                    deps.append("root_base <6.22.7a0")

        if record_name == "root_base":
            # ROOT requires vector-classes to be the exact same version as the one used for the build
            _replace_pin('vector-classes >=1.4.1,<1.5.0a0', 'vector-classes >=1.4.1,<1.4.2a0', deps, record)

        _replace_pin('libunwind >=1.2.1,<1.3.0a0', 'libunwind >=1.2.1,<2.0.0a0', deps, record)
        _replace_pin('snappy >=1.1.7,<1.1.8.0a0', 'snappy >=1.1.7,<2.0.0.0a0', deps, record)
        _replace_pin('ncurses >=6.1,<6.2.0a0', 'ncurses >=6.1,<6.3.0a0', deps, record)
        _replace_pin('abseil-cpp', 'abseil-cpp =20190808', deps, record)

        if record_name not in ["blas", "libblas", "libcblas", "liblapack",
                               "liblapacke", "lapack", "blas-devel"]:
            _replace_pin('liblapack >=3.8.0,<3.9.0a0', 'liblapack >=3.8.0,<4.0.0a0', deps, record)
            _replace_pin('liblapacke >=3.8.0,<3.9.0a0', 'liblapacke >=3.8.0,<4.0.0a0', deps, record)
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

        # add track_features to old python_abi pypy packages
        if (record_name == 'python_abi' and 'pypy' in record['build'] and
                "track_features" not in record):
            record["track_features"] = "pypy"

        llvm_pkgs = ["libclang", "clang", "clang-tools", "llvm", "llvm-tools", "llvmdev"]
        for llvm in ["libllvm8", "libllvm9"]:
            if any(dep.startswith(llvm) for dep in deps):
                if record_name not in llvm_pkgs:
                    _relax_exact(fn, record, llvm, max_pin="x.x")
                else:
                    _relax_exact(fn, record, llvm, max_pin="x.x.x")

        if any(dep.startswith("pari >=2.13.2") for dep in deps) and record.get('timestamp', 0) < 1625642169000:
            record["depends"].append("pari * *_single")

        if record_name in llvm_pkgs:
            new_constrains = record.get('constrains', [])
            version = record["version"]
            for pkg in llvm_pkgs:
                if record_name == pkg:
                    continue
                if pkg in new_constrains:
                    del new_constrains[pkg]
                if any(constraint.startswith(f"{pkg} ") for constraint in new_constrains):
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

        # make sure the old compilers conflict with the new sysroot packages
        # and they only use libraries from the old compilers
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
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        # we pushed a few builds of the compilers past the list of versions
        # above which do not use the sysroot packages - this block catches those
        # it will also break some test builds of the new compilers but we should
        # not be using those anyways and they are marked as broken.
        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name in [
                "gcc_impl_" + subdir, "gxx_impl_" + subdir, "gfortran_impl_" + subdir]
            and record['version'] not in ['5.4.0', '7.2.0', '7.3.0', '8.2.0']
            and not any(__r.startswith("sysroot_") for __r in record.get("depends", []))
            and record.get('timestamp', 0) < 1626220800000  # 2020-07-14
        ):
            new_constrains = record.get('constrains', [])
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        # all ctng activation packages that don't depend on the sysroot_*
        # packages are not compatible with the new sysroot_*-based compilers
        # root and cling must also be included as they have a builtin C++ interpreter
        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name in [
                "gcc_" + subdir, "gxx_" + subdir, "gfortran_" + subdir,
                "binutils_" + subdir, "gcc_bootstrap_" + subdir, "root_base", "cling"]
            and not any(__r.startswith("sysroot_") for __r in record.get("depends", []))
            and record.get('timestamp', 0) < 1626220800000  # 2020-07-14
        ):
            new_constrains = record.get('constrains', [])
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        if (record_name == "gcc_impl_{}".format(subdir)
            and record['version'] in ['5.4.0', '7.2.0', '7.3.0', '8.2.0', '8.4.0', '9.3.0']
            and record.get('timestamp', 0) < 1627530043000  # 2021-07-29
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
                record_name.endswith("-cos6-x86_64") or
                record_name.endswith("-cos7-x86_64") or
                record_name.endswith("-cos7-aarch64") or
                record_name.endswith("-cos7-ppc64le")
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

            new_constrains = record.get('constrains', [])
            if not any(__r.startswith("sysroot_") for __r in new_constrains):
                new_constrains.append("sysroot_" + sys_subdir + " ==99999999999")
                record["constrains"] = new_constrains

        # make sure pybind11 and pybind11-global have run constraints on
        # the abi metapackage
        # see https://github.com/conda-forge/conda-forge-repodata-patches-feedstock/issues/104  # noqa
        if (
            record_name in ["pybind11", "pybind11-global"]
            # this version has a constraint sometimes
            and (
                pkg_resources.parse_version(record["version"])
                <= pkg_resources.parse_version("2.6.1")
            )
            and not any(
                c.startswith("pybind11-abi ")
                for c in record.get("constrains", [])
            )
        ):
            _add_pybind11_abi_constraint(fn, record)

        # add *lal>=7.1.1 as run_constrained for liblal-7.1.1
        if (
            record_name == "liblal"
            and record['version'] == "7.1.1"
            and record['build_number'] in (0, 1, 2, 100, 101, 102)
        ):
            record.setdefault('constrains', []).extend((
                "lal >=7.1.1",
                "python-lal >=7.1.1",
            ))

        # Version constraints for azure-storage-common in azure-storage-file
        # 2.1.0 build 0 were incorrect.  These have been corrected in
        # https://github.com/conda-forge/azure-storage-file-feedstock/pull/8
        if (record_name == "azure-storage-file" and
                record["version"] == "2.1.0" and
                "azure-storage-common >=1.3.0,<1.4.0" in record['depends']):
            i = record['depends'].index('azure-storage-common >=1.3.0,<1.4.0')
            record['depends'][i] = 'azure-storage-common >=2.1,<3.0'

        # Version constraints for fsspec in gcsfs 0.8.0 build 0 were incorrect.
        # These have been corrected in PR
        # https://github.com/conda-forge/gcsfs-feedstock/pull/32
        if (record_name == "gcsfs" and
                record["version"] == "0.8.0" and
                "fsspec >=0.8.0" in record["depends"]):
            i = record["depends"].index("fsspec >=0.8.0")
            record["depends"][i] = "fsspec >=0.9.0,<0.10.0"

        # Old versions of Gazebo depend on boost-cpp >= 1.71,
        # but they are actually incompatible with any boost-cpp >= 1.72
        # https://github.com/conda-forge/gazebo-feedstock/issues/52
        if (record_name == "gazebo" and
                record.get('timestamp', 0) < 1583200976700):
            _replace_pin('boost-cpp >=1.71', 'boost-cpp >=1.71.0,<1.71.1.0a0', deps, record)

        # Version constraints for jupyterlab in jupyterlab-git<=0.22.0 were incorrect.
        # These have been corrected in PR
        # https://github.com/conda-forge/jupyterlab-git-feedstock/pull/27
        if record_name == "jupyterlab-git":
            if "jupyterlab >=2.0.0" in record["depends"]:
                i = record["depends"].index("jupyterlab >=2.0.0")
                record["depends"][i] = "jupyterlab >=2.0.0,<3.0.0"
            if "jupyterlab >=1.1.0" in record["depends"]:
                i = record["depends"].index("jupyterlab >=1.1.0")
                record["depends"][i] = "jupyterlab >=1.1.0,<2.0.0"
            if "jupyterlab >=1.0.0" in record["depends"]:
                i = record["depends"].index("jupyterlab >=1.0.0")
                record["depends"][i] = "jupyterlab >=1.0.0,<2.0.0"
            if "jupyterlab" in record["depends"]:
                i = record["depends"].index("jupyterlab")
                record["depends"][i] = "jupyterlab <1.0.0"

        # librmm 0.19 missed spdlog 1.7.0 in build 1
        # due to spdlog 1.7.0 not having run_exports.
        # This hotfixes those packages
        # https://github.com/conda-forge/librmm-feedstock/pull/5
        if (record_name == "librmm" and
                record["version"] == "0.19.0" and
                "spdlog =1.7.0" not in record["depends"]):
            record["depends"].append("spdlog =1.7.0")

        # Old versions of arosics do not work with py-tools-ds>=0.16.0 due to the an import of the
        # py-tools-ds.similarity module which was removed in py-tools-ds 0.16.0. In arosics>=1.2.0,
        # this import does not exist anymore, i.e., newer versions of arosics work together with all
        # py-tools-ds>=0.14.28 /0.15.8 / 0.15.10 versions as defined below.
        # No additional PR in the arosics feedstock is needed.
        if record_name == "arosics":
            if (record["version"] in ["0.9.22", "0.9.23", "0.9.24", "0.9.25", "0.9.26",
                                      "1.0.0", "1.0.1", "1.0.2", "1.0.3", "1.0.4", "1.0.5"]
                    and "py-tools-ds >=0.14.28" in record["depends"]):
                i = record["depends"].index("py-tools-ds >=0.14.28")
                record["depends"][i] = "py-tools-ds >=0.14.28,<=0.15.11"

            if (record["version"] == "1.0.6" and
                    "py-tools-ds >=0.15.8" in record["depends"]):
                i = record["depends"].index("py-tools-ds >=0.15.8")
                record["depends"][i] = "py-tools-ds >=0.15.8,<=0.15.11"

            if (record["version"] in ["1.1.0", "1.1.1"] and
                    "py-tools-ds >=0.15.10" in record["depends"]):
                i = record["depends"].index("py-tools-ds >=0.15.10")
                record["depends"][i] = "py-tools-ds >=0.15.10,<=0.15.11"

        # https://github.com/conda-forge/conda-forge-repodata-patches-feedstock/issues/159
        if record_name == "snowflake-sqlalchemy" and record["version"] in ("1.3.1", "1.2.5") and record["build_number"] == 0:
            depends = record["depends"]
            depends[depends.index("snowflake-connector-python <3")] = "snowflake-connector-python <3.0.0"
            depends[depends.index("sqlalchemy <2")] = "sqlalchemy >=1.4.0,<2.0.0"

    return index


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
    ver = pkg_resources.parse_version(record["version"])

    if ver < pkg_resources.parse_version("2.2.0"):
        abi_ver = "0"
    elif ver < pkg_resources.parse_version("2.2.4"):
        abi_ver = "1"
    elif ver < pkg_resources.parse_version("2.3.0"):
        abi_ver = "2"
    elif ver < pkg_resources.parse_version("2.5.0"):
        abi_ver = "3"
    elif ver <= pkg_resources.parse_version("2.6.1"):
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


def _replace_pin(old_pin, new_pin, deps, record, target='depends'):
    """Replace an exact pin with a new one. deps and target must match."""
    if target not in ('depends', 'constrains'):
        raise ValueError
    if old_pin in deps:
        i = record[target].index(old_pin)
        record[target][i] = new_pin

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
    return l + ["0"]*(num - len(l))


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

def _pin_stricter(fn, record, fix_dep, max_pin, upper_bound=None):
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
        if upper_bound is None:
            new_upper = get_upper_bound(lower, max_pin).split(".")
        else:
            new_upper = upper_bound.split(".")
        upper = pad_list(upper, len(new_upper))
        new_upper = pad_list(new_upper, len(upper))
        if tuple(upper) > tuple(new_upper):
            if str(new_upper[-1]) != "0":
                new_upper += ["0"]
            depends[dep_idx] = "{} >={},<{}a0".format(dep_parts[0], lower, ".".join(new_upper))
            if len(dep_parts) == 3:
                depends[dep_idx] = "{} {}".format(depends[dep_idx], dep_parts[2])
            record['depends'] = depends


def _pin_looser(fn, record, fix_dep, max_pin=None, upper_bound=None):
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

        if upper_bound is None:
            new_upper = get_upper_bound(lower, max_pin).split(".")
        else:
            new_upper = upper_bound.split(".")

        upper = pad_list(upper, len(new_upper))
        new_upper = pad_list(new_upper, len(upper))

        if tuple(upper) < tuple(new_upper):
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
