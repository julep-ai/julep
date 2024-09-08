from enum import Enum


class BaseDocSearchRequestLang(str, Enum):
    EN_US = "en-US"

    def __str__(self) -> str:
        return str(self.value)
