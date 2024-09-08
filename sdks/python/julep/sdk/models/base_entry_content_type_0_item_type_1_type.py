from enum import Enum


class BaseEntryContentType0ItemType1Type(str, Enum):
    IMAGE_URL = "image_url"

    def __str__(self) -> str:
        return str(self.value)
