from enum import Enum


class TaskAdditionalPropertyItemType17Kind(str, Enum):
    MAP_REDUCE = "map_reduce"

    def __str__(self) -> str:
        return str(self.value)
