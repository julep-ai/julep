from enum import Enum


class TasksCreateOrUpdateRouteCreateOrUpdateAccept(str, Enum):
    APPLICATIONJSON = "application/json"
    APPLICATIONYAML = "application/yaml"
    TEXTX_YAML = "text/x-yaml"
    TEXTYAML = "text/yaml"

    def __str__(self) -> str:
        return str(self.value)
