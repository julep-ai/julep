from io import StringIO
from typing import Any

import yaml


def load(string: str) -> Any:
    return yaml.load(string, Loader=yaml.CSafeLoader)


def dump(value: Any) -> str:
    return yaml.dump(value, Dumper=yaml.CSafeDumper)
