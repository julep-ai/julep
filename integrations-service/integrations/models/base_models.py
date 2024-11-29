from typing import Annotated, Optional

from pydantic import BaseModel, Field
from pydantic_core import Url

IdentifierName = Annotated[str, Field(max_length=40, pattern="^[^\\W0-9]\\w*$")]


class BaseOutput(BaseModel): ...


class ProviderInfo(BaseModel):
    url: Optional[Url] = None
    docs: Optional[Url] = None
    icon: Optional[Url] = None
    friendly_name: str


class BaseProviderMethod(BaseModel):
    method: IdentifierName
    description: str
    arguments: type[BaseModel]
    output: type[BaseOutput]


class BaseProvider(BaseModel):
    provider: IdentifierName
    setup: type[BaseModel] | None
    methods: list[BaseProviderMethod]
    info: ProviderInfo
