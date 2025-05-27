import json
from pathlib import Path
from typing import Any

module_directory: Path = Path(__file__).parent


# AIDEV-NOTE: Use Path.open for compatibility with pathlib
with (module_directory / "entities_example_chat.json").open() as _f:
    entities_example_chat: Any = json.load(_f)


with (module_directory / "trim_example_chat.json").open() as _f:
    trim_example_chat: Any = json.load(_f)


with (module_directory / "trim_example_result.json").open() as _f:
    trim_example_result: Any = json.load(_f)


with (module_directory / "summarize_example_chat.json").open() as _f:
    summarize_example_chat: Any = json.load(_f)


with (module_directory / "summarize_example_result.json").open() as _f:
    summarize_example_result: Any = json.load(_f)
