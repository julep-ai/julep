from pydantic import BaseModel, Field


class DalleImageGeneratorParams(BaseModel):
    prompt: str = Field(..., description="The image generation prompt")
