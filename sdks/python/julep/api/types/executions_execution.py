# This file was auto-generated by Fern from our API Definition.

import datetime as dt
import typing

from ..core.datetime_utils import serialize_datetime
from ..core.pydantic_utilities import deep_union_pydantic_dicts, pydantic_v1
from .common_uuid import CommonUuid
from .executions_execution_status import ExecutionsExecutionStatus


class ExecutionsExecution(pydantic_v1.BaseModel):
    task_id: CommonUuid = pydantic_v1.Field()
    """
    The ID of the task that the execution is running
    """

    status: ExecutionsExecutionStatus = pydantic_v1.Field()
    """
    The status of the execution
    """

    input: typing.Dict[str, typing.Any] = pydantic_v1.Field()
    """
    The input to the execution
    """

    created_at: dt.datetime = pydantic_v1.Field()
    """
    When this resource was created as UTC date-time
    """

    updated_at: dt.datetime = pydantic_v1.Field()
    """
    When this resource was updated as UTC date-time
    """

    id: CommonUuid

    def json(self, **kwargs: typing.Any) -> str:
        kwargs_with_defaults: typing.Any = {
            "by_alias": True,
            "exclude_unset": True,
            **kwargs,
        }
        return super().json(**kwargs_with_defaults)

    def dict(self, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]:
        kwargs_with_defaults_exclude_unset: typing.Any = {
            "by_alias": True,
            "exclude_unset": True,
            **kwargs,
        }
        kwargs_with_defaults_exclude_none: typing.Any = {
            "by_alias": True,
            "exclude_none": True,
            **kwargs,
        }

        return deep_union_pydantic_dicts(
            super().dict(**kwargs_with_defaults_exclude_unset),
            super().dict(**kwargs_with_defaults_exclude_none),
        )

    class Config:
        frozen = True
        smart_union = True
        extra = pydantic_v1.Extra.allow
        json_encoders = {dt.datetime: serialize_datetime}