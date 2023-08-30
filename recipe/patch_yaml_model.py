"""
Pydantic model for patch_yaml documents
"""
from __future__ import annotations
import itertools
import json
from pathlib import Path
from typing import Annotated

from annotated_types import MinLen, Ge
from pydantic import BaseModel, Field, ConfigDict


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
        description="Maximum version pin expression to apply to the package (e.g. `x.x`).",
    )
    upper_bound: _NonEmptyStr = Field(
        None,
        description="Explicit upper bound version to apply to the package (e.g. `2.0`).",
    )


class _IfClause(_ForbidExtra):
    """
    Condition(s) that a PackageRecord must satisfy to be patched.
    If more than one condition is specified, they are combined with a logical AND.
    """

    # Dynamically create fields for each repodata key and operator
    for negate, (key, type_hint), op in itertools.product((True, False), scalar_repodata_keys, operators):
        not_ = ("not_",) if negate else ()
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
            descr = f"List of '{key}' values to match against. A single scalar value is also allowed."
            type_hint = f"{type_hint} | list[{type_hint}]"
        else:
            descr = f"'{key}' value to compare against with `{op or 'eq'}` operator"
        if negate:
            descr = f"Negated condition: {descr}"
        exec(f'{key_name}: {type_hint} = Field(None, description="{descr}")')
    del key_name, key, type_hint, op, descr

    has_depends: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Spec or list of specs that should be present in the 'depends' list.",
    )
    has_constrains: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Spec or list of specs that should be present in the 'constrains' list.",
    )
    subdir_in: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="List of platforms to match against; e.g. `linux-64`",
    )
    artifact_in: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="List of full artifact filenames to match against; e.g. `ngmix-2.3.0-py38h50d1736_1.conda`",
    )
    not_has_depends: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Negated condition: Spec or list of specs that should be present in the 'depends' list.",
    )
    not_has_constrains: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Negated condition: Spec or list of specs that should be present in the 'constrains' list.",
    )
    not_subdir_in: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Negated condition: List of platforms to match against; e.g. `linux-64`",
    )
    not_artifact_in: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Negated condition: List of full artifact filenames to match against; e.g. `ngmix-2.3.0-py38h50d1736_1.conda`",
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
    remove_track_features: _NonEmptyStr | list[_NonEmptyStr] = Field(
        None,
        description="Remove item(s) from track_features to matched packages",
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
        description="Rename 'old' dependency as 'new', leaving version and build string fields untouched.",
    )
    rename_constrains: _Old2New = Field(
        None,
        description="Rename 'old' constraint as 'new', leaving version and build string fields untouched.",
    )
    relax_exact_depends: _Name_MaxPin_UpperBound = Field(
        None,
        description="Relax an exact pin (e.g., `blah ==1.0.0`) to something like blah `>=1.0.0` and possibly with `,<2.0a0` added if max_pin='x'",
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
