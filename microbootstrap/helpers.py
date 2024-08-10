import dataclasses
import re
import typing
from dataclasses import _MISSING_TYPE

from microbootstrap import exceptions


if typing.TYPE_CHECKING:
    from dataclasses import _DataclassT

    from pydantic import BaseModel


PydanticConfigT = typing.TypeVar("PydanticConfigT", bound="BaseModel")
VALID_PATH_PATTERN: typing.Final = r"^(/[a-zA-Z0-9_-]+)+/?$"


def dataclass_to_dict_no_defaults(dataclass_to_convert: "_DataclassT") -> dict[str, typing.Any]:
    conversion_result: typing.Final = {}
    for dataclass_field in dataclasses.fields(dataclass_to_convert):
        value = getattr(dataclass_to_convert, dataclass_field.name)
        if isinstance(dataclass_field.default, _MISSING_TYPE):
            conversion_result[dataclass_field.name] = value
            continue
        if dataclass_field.default != value and isinstance(dataclass_field.default_factory, _MISSING_TYPE):
            conversion_result[dataclass_field.name] = value
            continue
        if value != dataclass_field.default and value != dataclass_field.default_factory():  # type: ignore[misc]
            conversion_result[dataclass_field.name] = value

    return conversion_result


def merge_pydantic_configs(
    config_to_merge: PydanticConfigT,
    config_with_changes: PydanticConfigT,
) -> PydanticConfigT:
    config_class: typing.Final = config_to_merge.__class__
    resulting_dict_config: typing.Final = merge_dict_configs(
        config_to_merge.model_dump(exclude_defaults=True, exclude_unset=True),
        config_with_changes.model_dump(exclude_defaults=True, exclude_unset=True),
    )
    return config_class(**resulting_dict_config)


def merge_dataclasses_configs(
    config_to_merge: "_DataclassT",
    config_with_changes: "_DataclassT",
) -> "_DataclassT":
    config_class: typing.Final = config_to_merge.__class__
    resulting_dict_config: typing.Final = merge_dict_configs(
        dataclass_to_dict_no_defaults(config_to_merge),
        dataclass_to_dict_no_defaults(config_with_changes),
    )
    return config_class(**resulting_dict_config)


def merge_dict_configs(
    config_dict: dict[str, typing.Any],
    changes_dict: dict[str, typing.Any],
) -> dict[str, typing.Any]:
    for change_key, change_value in changes_dict.items():
        config_value = config_dict.get(change_key)

        if isinstance(config_value, set):
            if not isinstance(change_value, set):
                raise exceptions.ConfigMergeError(f"Can't merge {config_value} and {change_value}")
            config_dict[change_key] = {*config_value, *change_value}
            continue

        if isinstance(config_value, tuple):
            if not isinstance(change_value, tuple):
                raise exceptions.ConfigMergeError(f"Can't merge {config_value} and {change_value}")
            config_dict[change_key] = (*config_value, *change_value)
            continue

        if isinstance(config_value, list):
            if not isinstance(change_value, list):
                raise exceptions.ConfigMergeError(f"Can't merge {config_value} and {change_value}")
            config_dict[change_key] = [*config_value, *change_value]
            continue

        if isinstance(config_value, dict):
            if not isinstance(change_value, dict):
                raise exceptions.ConfigMergeError(f"Can't merge {config_value} and {change_value}")
            config_dict[change_key] = {**config_value, **change_value}
            continue

        config_dict[change_key] = change_value

    return config_dict


def is_valid_path(maybe_path: str) -> bool:
    return bool(re.fullmatch(VALID_PATH_PATTERN, maybe_path))