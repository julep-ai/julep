from pydantic import BaseModel, Field


class DalleImageGeneratorParams(BaseModel):
    prompt: str = Field(str, description="The image generation prompt")
