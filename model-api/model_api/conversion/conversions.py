from io import StringIO
import json
import re
from typing import Optional

from .datatypes import ChatML, ChatMLMessage
from .exceptions import InvalidPromptException, InvalidFunctionName


me_regex = re.compile(r"(?P<tag>me)(\s+\((?P<name>.+)\)|$)")
person_regex = re.compile(r"(?P<tag>person)(\s+\((?P<name>.+)\)|$)")


def parse_message(message: str) -> ChatMLMessage:
    parts = message.split("\n", 1)

    tag = ""
    content = message
    if len(parts) > 1:
        tag = parts[0].strip()
        content = parts[1].lstrip()

    if tag in ("situation", "information", "thought"):
        return ChatMLMessage(role="system", name=tag, content=content)

    if tag == "function_call":
        return ChatMLMessage(role=tag, content=content)

    assistant = me_regex.match(tag)
    if assistant:
        return ChatMLMessage(role="assistant", name=assistant["name"], content=content)

    person = person_regex.match(tag)
    if person:
        return ChatMLMessage(role="user", name=person["name"], content=content)

    return ChatMLMessage(content=message)


def message_role_to_prefix(message: ChatMLMessage) -> str:
    match message:
        # If empty <system> tag, then assume role="situation"
        case {"role": "system", "name": None, **rest}:
            return "situation"
        case {"role": "system", **rest} if "name" not in message:
            return "situation"

        case {"role": "system", "name": name, **rest}:
            return name
        case {"role": "user", **rest}:
            name = rest.get("name", None)
            return f"person ({name})" if name else "person"
        case {"role": "assistant", "name": name, **rest}:
            return f"me ({name})" if name else "me"
        case {"role": "assistant", **rest}:
            return "me"
        case {"role": "function_call", **rest}:
            return "function_call"


def _check_last_message(message: ChatMLMessage):
    match message:
        case (
            {"role": "system", "name": "thought", **_rest}
            | {"role": "assistant", **_rest}
            | {"role": "system", "name": "functions", **_rest}
            | {"role": "function_call", **_rest}
        ):
            return True

    return False


def _validate_message(message, continue_, is_last):
    msg_role = message.get("role")
    if not msg_role:
        raise InvalidPromptException("'role' can not be null")

    if not message.get("content") and not (is_last and continue_):
        raise InvalidPromptException("'content' can not be null")

    #### "functions" is only valid as a system name
    allowed_roles = {"system", "user", "assistant", "function_call"}
    if msg_role not in allowed_roles:
        raise InvalidPromptException(f"role must be one of {allowed_roles}")

    allowed_system_names = {
        "situation",
        "thought",
        "information",
        "functions",
        "instruction",
    }
    if msg_role == "system" and message.get("name") not in allowed_system_names:
        raise InvalidPromptException(
            f"name for role 'system' must be one of {allowed_system_names}"
        )

    if is_last and continue_ and not _check_last_message(message):
        raise InvalidPromptException(
            "last message with continue=True can not have this format"
        )

    if not is_last and continue_:
        raise InvalidPromptException(
            "only last message can have 'continue' equal to True"
        )


def _validate_functions(functions: list[dict], function_call: str) -> list[dict]:
    for f in functions:
        if f["name"].strip() == function_call.strip():
            return [f]

    raise InvalidFunctionName(function_call)


def to_prompt(
    messages: ChatML,
    bos: str = "<|im_start|>",
    eos: str = "<|im_end|>",
    model_dump: Optional[callable] = None,
    functions: list[dict] | None = None,
    function_call: str | None = None,
) -> str:
    # Input format:
    # [
    #     {"role": "system", "name": "situation", "content": "I am talking to Diwank"},
    #     {"role": "assistant", "name": "Samantha", "content": "Hey Diwank"},
    #     {"role": "user", "name": "Diwank", "content": "Hey!"},
    # ]

    # Output format:
    #
    # <|section|>situation
    # I am talking to Diwank<|endsection|>
    # <|section|>me (Samantha)
    # Hey Diwank<|endsection|>
    # <|section|>person (Diwank)
    # Hey<|endsection|>
    # <|section|>me (Samantha)\n

    if not isinstance(messages, list):
        raise InvalidPromptException("must be a list")

    if functions:
        if function_call not in ("auto", "none", None):
            functions = {
                "role": "system",
                "name": "functions",
                "content": "\n".join(
                    [
                        json.dumps(f, indent=4)
                        for f in _validate_functions(functions, function_call)
                    ]
                ),
            }
            messages.insert(1, functions)
            fun_call = {"role": "function_call", "continue": True}
            fun_call.update({"content": f'{{"name": "{function_call}", '})

            if messages[-1].get("continue"):
                raise InvalidPromptException(
                    "Conflicting instructions, "
                    "please remove the last instruction with 'continue' "
                    "flag set to 'true' or set the flag to 'false'. "
                    "You can either remove `functions` and/or `function_call` parameters."
                )

            messages.append(fun_call)
        elif function_call in ("auto", None):
            messages.insert(
                1,
                {
                    "role": "system",
                    "name": "functions",
                    "content": "\n".join([json.dumps(f, indent=4) for f in functions]),
                },
            )

    prompt = StringIO()
    add_extra_message = False
    for idx, message in enumerate(messages):
        if not isinstance(message, dict) and model_dump is not None:
            message = model_dump(message)

        continue_ = message.get("continue", False)
        is_last = idx == len(messages) - 1

        _validate_message(message, continue_, is_last)
        if is_last and not continue_:
            add_extra_message = True

        end_tag = "" if is_last and continue_ else f"{eos}\n"
        content = f"{bos}{message_role_to_prefix(message)}\n{message.get('content', '').strip()}{end_tag}"
        prompt.write(content)

    if add_extra_message:
        new_last_msg = {"name": None, "role": "assistant", "content": None}

        content = (
            bos
            if functions and function_call in ("auto", None)
            else f"{bos}{message_role_to_prefix(new_last_msg)}\n"
        )
        prompt.write(content)

    return prompt.getvalue()
