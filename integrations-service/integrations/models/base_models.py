from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, RootModel
from pydantic_core import Url

IdentifierName = Annotated[str, Field(max_length=40, pattern="^[^\\W0-9]\\w*$")]


class BaseSetup(BaseModel): ...


class BaseArguments(BaseModel): ...


class BaseOutput(BaseModel): ...


class ProviderInfo(BaseModel):
    url: Optional[Url]
    docs: Optional[Url]
    icon: Optional[Url]
    friendly_name: str


class BaseProviderMethod(BaseModel):
    method: IdentifierName
    description: str
    arguments: type[BaseArguments]
    output: type[BaseOutput]


class BaseProvider(BaseModel):
    provider: IdentifierName
    setup: type[BaseSetup] | None
    methods: list[BaseProviderMethod]
    info: ProviderInfo
