from pydantic import BaseModel, Field


class DalleImageGeneratorSetup(BaseModel):
    api_key: str = Field(str, description="The API key for DALL-E")


class DalleImageGeneratorArguments(BaseModel):
    prompt: str = Field(str, description="The image generation prompt")
