"""
Pydantic model for patch_yaml documents
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Annotated

from annotated_types import Ge, MinLen
from pydantic import BaseModel, ConfigDict, Field


class _ForbidExtra(BaseModel):
    model_config = ConfigDict(extra="forbid")


_NonEmptyStr = Annotated[str, MinLen(1)]
_PosInt = Annotated[int, Ge(0)]
scalar_repodata_keys = (
    ("arch", "_NonEmptyStr"),
    ("build", "_NonEmptyStr"),
    ("build_number", "_PosInt"),
    # ("constrains", "list[_NonEmptyStr]"),
    # ("depends", "list[_NonEmptyStr]"),
    # ("features", "list[_NonEmptyStr]"),
    ("legacy_bz2_md5", "_NonEmptyStr"),
    ("legacy_bz2_size", "_NonEmptyStr"),
    ("license", "_NonEmptyStr"),
    ("license_family", "_NonEmptyStr"),
    ("md5", "_NonEmptyStr"),
    ("name", "_NonEmptyStr"),
    ("noarch", "_NonEmptyStr"),
    ("platform", "_NonEmptyStr"),
    ("sha256", "_NonEmptyStr"),
    ("size", "_PosInt"),
    ("subdir", "_NonEmptyStr"),
    ("timestamp", "_PosInt"),
    # ("track_features", "list[_NonEmptyStr]"),
    ("version", "_NonEmptyStr"),
)
operators = (
    "",  # alias for eq
    "lt",
    "le",
    "gt",
    "ge",
    "eq",
    "ne",
    "in",
)


class _Old2New(_ForbidExtra):
    old: _NonEmptyStr = ...
    new: _NonEmptyStr = ...


class _Name_MaxPin_UpperBound(_ForbidExtra):
    name: _NonEmptyStr = ...
    max_pin: Annotated[str, Field(pattern=r"^[x.]+$")] = Field(
        None,
        description="Maximum version pin expression to apply to the package (e.g. `x.x`).",  # noqa: E501
    )
    upper_bound: str | None = Field(
        None,
        description="Explicit upper bound version to apply to the package (e.g. `2.0`).",  # noqa: E501
    )


class _IfClause(_ForbidExtra):
    """
    Condition(s) that a PackageRecord must satisfy to be patched.
    If more than one condition is specified, they are combined with a logical AND.
    """

    # Dynamically create fields for each repodata key and operator
    for negate, (key, type_hint), op in itertools.product(
        (True, False), scalar_repodata_keys, operators
    ):
        not_ = ("not",) if negate else ()
        _op = (op,) if op else ()
        key_name = "_".join((*not_, key, *_op))
        if (
            op in ("gt", "ge", "lt", "le")
            and "_NonEmptyStr" in type_hint
            and key != "version"
        ):
            continue  # no point in comparing non-version strings with gt, ge, lt, le
        if op in ("", "eq", "ne", "in") and type_hint == "_PosInt":  # accept globs too
            type_hint += " | _NonEmptyStr"
        if op == "in":
            descr = f"List of '{key}' values to match against. A single scalar value is also allowed."  # noqa: E501
            type_hint = f"{type_hint} | list[{type_hint}]"
        else:
            descr = f"'{key}' value to compare against with `{op or 'eq'}` operator"
        if negate:
            descr = f"Negated condition: {descr}"
        exec(f'{key_name}: {type_hint} = Field(None, description="{descr}")')
    del negate, key_name, key, type_hint, op, descr, not_, _op

    has_depends: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Spec or list of specs that should be present in the 'depends' list.",  # noqa: E501
    )
    has_constrains: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Spec or list of specs that should be present in the 'constrains' list.",  # noqa: E501
    )
    has_track_features: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Feature or list of features that should be present in the 'track_features' field.",  # noqa: E501
    )
    subdir_in: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="List of platforms to match against; e.g. `linux-64`",
    )
    artifact_in: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="List of full artifact filenames to match against; e.g. `ngmix-2.3.0-py38h50d1736_1.conda`",  # noqa: E501
    )
    not_has_depends: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Negated condition: Spec or list of specs that should be present in the 'depends' list.",  # noqa: E501
    )
    not_has_constrains: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Negated condition: Spec or list of specs that should be present in the 'constrains' list.",  # noqa: E501
    )
    not_has_track_features: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Negated condition: feature or list of features that should be present in the 'track_features' field.",  # noqa: E501
    )
    not_subdir_in: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Negated condition: List of platforms to match against; e.g. `linux-64`",  # noqa: E501
    )
    not_artifact_in: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Negated condition: List of full artifact filenames to match against; e.g. `ngmix-2.3.0-py38h50d1736_1.conda`",  # noqa: E501
    )


class _ThenClauseItem(_ForbidExtra):
    add_depends: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Add dependencies to matched packages",
    )
    add_constrains: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Add constraints to matched packages",
    )
    remove_depends: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Remove dependencies to matched packages",
    )
    remove_constrains: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Remove constraints to matched packages",
    )
    reset_depends: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Reset the dependencies to the specified value(s)",
    )
    reset_constrains: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Reset the constraints to the specified value(s)",
    )
    remove_track_features: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Remove item(s) from track_features to matched packages",
    )
    add_track_features: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Add item(s) to track_features for matched packages",
    )
    replace_depends: _Old2New = Field(
        None,
        description="Replace 'old' dependency with 'new'.",
    )
    replace_constrains: _Old2New = Field(
        None,
        description="Replace 'old' constraint with 'new'.",
    )
    rename_depends: _Old2New = Field(
        None,
        description="Rename 'old' dependency as 'new', leaving version and build string fields untouched.",  # noqa: E501
    )
    rename_constrains: _Old2New = Field(
        None,
        description="Rename 'old' constraint as 'new', leaving version and build string fields untouched.",  # noqa: E501
    )
    relax_exact_depends: _Name_MaxPin_UpperBound = Field(
        None,
        description="Relax an exact pin (e.g., `blah ==1.0.0`) to something like blah `>=1.0.0` and possibly with `,<2.0a0` added if max_pin='x'",  # noqa: E501
    )
    tighten_depends: _Name_MaxPin_UpperBound = Field(
        None,
        description="Make a dependency version constraint stricter",
    )
    loosen_depends: _Name_MaxPin_UpperBound = Field(
        None,
        description="Make a dependency version constraint looser",
    )


class PatchYaml(_ForbidExtra):
    if_: _IfClause = Field(..., alias="if")
    then: Annotated[list[_ThenClauseItem], MinLen(1)] = Field(
        ...,
        description="List of operations to apply to matched records",
    )


def generate_schema(write=False):
    schema_str = json.dumps(PatchYaml.model_json_schema(), indent=2)
    if write:
        (Path(__file__).parent / ("patch_yaml_model.json")).write_text(schema_str)
    return schema_str


if __name__ == "__main__":
    generate_schema(write=True)
