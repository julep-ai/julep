from pydantic import BaseModel


class Model(BaseModel):
    model_name: str
    max_length: int
    updated_at: int
    default_settings: dict


class ModelRequest(BaseModel):
    model_name: str
