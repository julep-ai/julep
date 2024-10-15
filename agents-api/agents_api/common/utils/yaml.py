from io import StringIO
from typing import Any

from ruamel.yaml import YAML

yaml = YAML(typ="safe", pure=True)  # pure is needed for yaml 1.2 support
yaml.version = (1, 2)


def dump(value: Any) -> str:
    stream = StringIO()
    yaml.dump(value, stream)

    return stream.getvalue()


def load(string: str) -> Any:
    return yaml.load(string)
