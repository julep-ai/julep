from pydantic import BaseModel, Field


class DalleImageGeneratorArguments(BaseModel):
    prompt: str = Field(str, description="The image generation prompt")
