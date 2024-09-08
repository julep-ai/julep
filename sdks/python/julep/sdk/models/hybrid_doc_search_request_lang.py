from enum import Enum


class HybridDocSearchRequestLang(str, Enum):
    EN_US = "en-US"

    def __str__(self) -> str:
        return str(self.value)
