from typing import Type

from beartype.vale import Is
from beartype.vale._core._valecore import BeartypeValidator
from pydantic import BaseModel


def dict_like(pydantic_model_class: Type[BaseModel]) -> BeartypeValidator:
    required_fields_set: set[str] = set(
        [
            field
            for field, info in pydantic_model_class.model_fields.items()
            if info.is_required()
        ]
    )

    validator = Is[
        lambda x: isinstance(x, pydantic_model_class)
        or required_fields_set.issubset(set(x.keys()))
    ]

    return validator
