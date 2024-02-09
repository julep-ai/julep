import pytest
from .conversions import to_prompt
from .exceptions import InvalidFunctionName, InvalidPromptException


def test_function_call_none_last_not_continue():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]
    functions = []
    prompt = to_prompt(
        messages,
        bos="<|im_start|>",
        eos="<|im_end|>",
        functions=functions,
        function_call="none",
    )
    assert (
        prompt
        == """<|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>me
"""
    )


def test_function_call_auto_functions_not_passed():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]
    functions = []
    prompt = to_prompt(
        messages,
        bos="<|im_start|>",
        eos="<|im_end|>",
        functions=functions,
        function_call="auto",
    )
    assert (
        prompt
        == """<|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>me
"""
    )


def test_function_call_none_functions_not_passed():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]
    functions = []
    prompt = to_prompt(
        messages,
        bos="<|im_start|>",
        eos="<|im_end|>",
        functions=functions,
        function_call=None,
    )
    assert (
        prompt
        == """<|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>me
"""
    )


def test_function_call_auto_functions_passed():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]
    functions = [
        {
            "name": "generate_anagram",
            "description": "Generate an anagram of a given word",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        }
    ]
    prompt = to_prompt(
        messages,
        bos="<|im_start|>",
        eos="<|im_end|>",
        functions=functions,
        function_call="auto",
    )
    assert (
        prompt
        == """<|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>functions
{
    "name": "generate_anagram",
    "description": "Generate an anagram of a given word",
    "parameters": {
        "type": "object",
        "properties": {
            "word": {
                "type": "string",
                "description": "The word to generate an anagram of"
            }
        },
        "required": [
            "word"
        ]
    }
}<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>"""
    )


def test_function_call_none_functions_passed():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]
    functions = [
        {
            "name": "generate_anagram",
            "description": "Generate an anagram of a given word",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        }
    ]
    prompt = to_prompt(
        messages,
        bos="<|im_start|>",
        eos="<|im_end|>",
        functions=functions,
        function_call=None,
    )
    assert (
        prompt
        == """<|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>functions
{
    "name": "generate_anagram",
    "description": "Generate an anagram of a given word",
    "parameters": {
        "type": "object",
        "properties": {
            "word": {
                "type": "string",
                "description": "The word to generate an anagram of"
            }
        },
        "required": [
            "word"
        ]
    }
}<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>"""
    )


def test_function_call_none_last_continue():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
        {"role": "assistant", "name": "Samantha", "continue": True},
    ]
    functions = []
    prompt = to_prompt(
        messages,
        bos="<|im_start|>",
        eos="<|im_end|>",
        functions=functions,
        function_call="none",
    )
    assert (
        prompt
        == """<|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>me (Samantha)
"""
    )


def test_function_call_none_last_continue_function_call():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
        {"role": "function_call", "content": "{}", "continue": True},
    ]
    functions = []
    prompt = to_prompt(
        messages,
        bos="<|im_start|>",
        eos="<|im_end|>",
        functions=functions,
        function_call="none",
    )
    assert (
        prompt
        == """<|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>function_call
{}"""
    )


def test_function_call_auto_last_not_continue():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]
    functions = [
        {
            "name": "generate_anagram",
            "description": "Generate an anagram of a given word",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        },
        {
            "name": "other_func",
            "description": "Logic",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        },
    ]
    prompt = to_prompt(
        messages,
        bos="<|im_start|>",
        eos="<|im_end|>",
        functions=functions,
        function_call="auto",
    )
    assert (
        prompt
        == """<|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>functions
{
    "name": "generate_anagram",
    "description": "Generate an anagram of a given word",
    "parameters": {
        "type": "object",
        "properties": {
            "word": {
                "type": "string",
                "description": "The word to generate an anagram of"
            }
        },
        "required": [
            "word"
        ]
    }
}
{
    "name": "other_func",
    "description": "Logic",
    "parameters": {
        "type": "object",
        "properties": {
            "word": {
                "type": "string",
                "description": "The word to generate an anagram of"
            }
        },
        "required": [
            "word"
        ]
    }
}<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>"""
    )


def test_function_call_auto_last_continue():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
        {"role": "assistant", "name": "Samantha", "continue": True},
    ]
    functions = [
        {
            "name": "generate_anagram",
            "description": "Generate an anagram of a given word",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        }
    ]
    prompt = to_prompt(
        messages,
        bos="<|im_start|>",
        eos="<|im_end|>",
        functions=functions,
        function_call="auto",
    )
    assert (
        prompt
        == """<|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>functions
{
    "name": "generate_anagram",
    "description": "Generate an anagram of a given word",
    "parameters": {
        "type": "object",
        "properties": {
            "word": {
                "type": "string",
                "description": "The word to generate an anagram of"
            }
        },
        "required": [
            "word"
        ]
    }
}<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>me (Samantha)
"""
    )


def test_function_call_auto_last_continue_function_call():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
        {"role": "function_call", "continue": True},
    ]
    functions = [
        {
            "name": "generate_anagram",
            "description": "Generate an anagram of a given word",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        }
    ]
    prompt = to_prompt(
        messages,
        bos="<|im_start|>",
        eos="<|im_end|>",
        functions=functions,
        function_call="auto",
    )
    assert (
        prompt
        == """<|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>functions
{
    "name": "generate_anagram",
    "description": "Generate an anagram of a given word",
    "parameters": {
        "type": "object",
        "properties": {
            "word": {
                "type": "string",
                "description": "The word to generate an anagram of"
            }
        },
        "required": [
            "word"
        ]
    }
}<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>function_call
"""
    )


def test_function_call_func_name_last_not_continue():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]
    functions = [
        {
            "name": "other_func",
            "description": "Logic",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        },
        {
            "name": "generate_anagram",
            "description": "Generate an anagram of a given word",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        },
    ]
    prompt = to_prompt(
        messages,
        bos="<|im_start|>",
        eos="<|im_end|>",
        functions=functions,
        function_call="generate_anagram",
    )
    assert (
        prompt
        == """<|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>functions
{
    "name": "generate_anagram",
    "description": "Generate an anagram of a given word",
    "parameters": {
        "type": "object",
        "properties": {
            "word": {
                "type": "string",
                "description": "The word to generate an anagram of"
            }
        },
        "required": [
            "word"
        ]
    }
}<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>function_call
{"name": "generate_anagram","""
    )


def test_function_call_func_name_last_not_continue_invalid_function_name():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]
    functions = [
        {
            "name": "other_func",
            "description": "Logic",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        },
        {
            "name": "generate_anagram",
            "description": "Generate an anagram of a given word",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        },
    ]
    with pytest.raises(InvalidFunctionName) as e_info:
        to_prompt(
            messages,
            bos="<|im_start|>",
            eos="<|im_end|>",
            functions=functions,
            function_call="unknown",
        )
    assert e_info.value.args[0] == "Invalid function name: unknown"


def test_function_call_func_name_last_continue():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
        {"role": "assistant", "name": "Samantha", "continue": True},
    ]
    functions = [
        {
            "name": "generate_anagram",
            "description": "Generate an anagram of a given word",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        }
    ]
    with pytest.raises(InvalidPromptException) as e_info:
        to_prompt(
            messages,
            bos="<|im_start|>",
            eos="<|im_end|>",
            functions=functions,
            function_call="generate_anagram",
        )
    assert e_info.value.args[0] == (
        "Invalid prompt format: Conflicting instructions, "
        "please remove the last instruction with 'continue' "
        "flag set to 'true' or set the flag to 'false'. "
        "You can either remove `functions` and/or `function_call` parameters."
    )


def test_function_call_func_name_last_continue_function_call():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
        {
            "role": "function_call",
            "content": '{"name": "generate_anagram", ',
            "continue": True,
        },
    ]
    functions = [
        {
            "name": "generate_anagram",
            "description": "Generate an anagram of a given word",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to generate an anagram of",
                    }
                },
                "required": ["word"],
            },
        }
    ]
    with pytest.raises(InvalidPromptException) as e_info:
        to_prompt(
            messages,
            bos="<|im_start|>",
            eos="<|im_end|>",
            functions=functions,
            function_call="generate_anagram",
        )
    assert e_info.value.args[0] == (
        "Invalid prompt format: Conflicting instructions, "
        "please remove the last instruction with 'continue' "
        "flag set to 'true' or set the flag to 'false'. "
        "You can either remove `functions` and/or `function_call` parameters."
    )
