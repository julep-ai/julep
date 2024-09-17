import json
from pathlib import Path
from typing import Any

module_directory: Path = Path(__file__).parent


with open(f"{module_directory}/entities_example_chat.json", "r") as _f:
    entities_example_chat: Any = json.load(_f)


with open(f"{module_directory}/trim_example_chat.json", "r") as _f:
    trim_example_chat: Any = json.load(_f)


with open(f"{module_directory}/trim_example_result.json", "r") as _f:
    trim_example_result: Any = json.load(_f)


with open(f"{module_directory}/summarize_example_chat.json", "r") as _f:
    summarize_example_chat: Any = json.load(_f)


with open(f"{module_directory}/summarize_example_result.json", "r") as _f:
    summarize_example_result: Any = json.load(_f)
