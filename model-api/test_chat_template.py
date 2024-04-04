from transformers import AutoTokenizer

model_name = "julep-ai/samantha-1-turbo"
tokenizer = AutoTokenizer.from_pretrained(model_name)


# Set the template
template_path = "./model_api/chat_template.jinja"
with open(template_path, "r") as f:
    chat_template = f.read()


def to_prompt(messages, chat_template=chat_template, **kwargs):
    prompt = tokenizer.apply_chat_template(
        messages, chat_template=chat_template, tokenize=False, **kwargs
    )

    return prompt


def test_function_call_none_last_user_continue():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
        {"role": "assistant", "name": "Samantha", "continue": True},
    ]

    prompt = to_prompt(messages, add_generation_prompt=True)

    assert (
        prompt
        == """<s><|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>me
"""
    )


def test_function_call_none_last_not_continue():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]

    prompt = to_prompt(messages, add_generation_prompt=True)

    assert (
        prompt
        == """<s><|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>"""
    )


def test_function_call_auto_functions_not_passed():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]

    prompt = to_prompt(messages, add_generation_prompt=True)

    assert (
        prompt
        == """<s><|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>"""
    )


def test_function_call_none_functions_not_passed():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]

    prompt = to_prompt(messages, add_generation_prompt=True)

    assert (
        prompt
        == """<s><|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>"""
    )


def test_function_call_auto_functions_passed():
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

    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "system", "name": "functions", "content": functions},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
    ]

    prompt = to_prompt(messages, add_generation_prompt=True)

    assert (
        prompt
        == """<s><|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>functions
Available functions:

{
    "description": "Generate an anagram of a given word",
    "name": "generate_anagram",
    "parameters": {
        "properties": {
            "word": {
                "description": "The word to generate an anagram of",
                "type": "string"
            }
        },
        "required": [
            "word"
        ],
        "type": "object"
    }
}<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>"""
    )


# def test_function_call_none_functions_passed():
#     messages = [
#         {"role": "system", "name": "situation", "content": "I am talking to John"},
#         {"role": "assistant", "name": "Samantha", "content": "Hey John"},
#         {"role": "user", "name": "John", "content": "Hey!"},
#     ]
#     functions = [
#         {
#             "name": "generate_anagram",
#             "description": "Generate an anagram of a given word",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "word": {
#                         "type": "string",
#                         "description": "The word to generate an anagram of",
#                     }
#                 },
#                 "required": ["word"],
#             },
#         }
#     ]
#     prompt = to_prompt(
#         messages,
#         bos="<|im_start|>",
#         eos="<|im_end|>",
#         functions=functions,
#         function_call=None,
#     )
#     assert (
#         prompt
#         == """<|im_start|>situation
# I am talking to John<|im_end|>
# <|im_start|>functions
# Available functions:

# {
#     "name": "generate_anagram",
#     "description": "Generate an anagram of a given word",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "word": {
#                 "type": "string",
#                 "description": "The word to generate an anagram of"
#             }
#         },
#         "required": [
#             "word"
#         ]
#     }
# }<|im_end|>
# <|im_start|>me (Samantha)
# Hey John<|im_end|>
# <|im_start|>person (John)
# Hey!<|im_end|>
# <|im_start|>"""
#     )


def test_function_call_none_last_continue():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
        {"role": "assistant", "name": "Samantha", "content": "Hi", "continue": True},
    ]

    prompt = to_prompt(messages, add_generation_prompt=True)

    assert (
        prompt
        == """<s><|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>me
Hi"""
    )


def test_function_call_none_last_continue_function_call():
    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
        {"role": "function_call", "content": "{}", "continue": True},
    ]

    prompt = to_prompt(messages, add_generation_prompt=True)

    assert (
        prompt
        == """<s><|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>function_call
{}"""
    )


# def test_function_call_auto_last_not_continue():
#     messages = [
#         {"role": "system", "name": "situation", "content": "I am talking to John"},
#         {"role": "assistant", "name": "Samantha", "content": "Hey John"},
#         {"role": "user", "name": "John", "content": "Hey!"},
#     ]
#     functions = [
#         ({
#                 "name": "generate_anagram",
#                 "description": "Generate an anagram of a given word",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "word": {
#                             "type": "string",
#                             "description": "The word to generate an anagram of",
#                         }
#                     },
#                     "required": ["word"],
#                 },
#             }
#         ),
#         ({
#                 "name": "other_func",
#                 "description": "Logic",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "word": {
#                             "type": "string",
#                             "description": "The word to generate an anagram of",
#                         }
#                     },
#                     "required": ["word"],
#                 },
#             }
#         ),
#     ]
#     prompt = to_prompt(
#         messages,
#         bos="<|im_start|>",
#         eos="<|im_end|>",
#         functions=functions,
#         function_call="auto",
#     )
#     assert (
#         prompt
#         == """<|im_start|>situation
# I am talking to John<|im_end|>
# <|im_start|>functions
# Available functions:
#
# {
#     "name": "generate_anagram",
#     "description": "Generate an anagram of a given word",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "word": {
#                 "type": "string",
#                 "description": "The word to generate an anagram of"
#             }
#         },
#         "required": [
#             "word"
#         ]
#     }
# }
# {
#     "name": "other_func",
#     "description": "Logic",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "word": {
#                 "type": "string",
#                 "description": "The word to generate an anagram of"
#             }
#         },
#         "required": [
#             "word"
#         ]
#     }
# }<|im_end|>
# <|im_start|>me (Samantha)
# Hey John<|im_end|>
# <|im_start|>person (John)
# Hey!<|im_end|>
# <|im_start|>"""
#     )


# def test_function_call_auto_last_continue():
#     messages = [
#         {"role": "system", "name": "situation", "content": "I am talking to John"},
#         {"role": "assistant", "name": "Samantha", "content": "Hey John"},
#         {"role": "user", "name": "John", "content": "Hey!"},
#         {"role": "assistant", "name": "Samantha", "continue": True},
#     ]
#     functions = [
#         ({
#                 "name": "generate_anagram",
#                 "description": "Generate an anagram of a given word",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "word": {
#                             "type": "string",
#                             "description": "The word to generate an anagram of",
#                         }
#                     },
#                     "required": ["word"],
#                 },
#             }
#         )
#     ]
#     prompt = to_prompt(
#         messages,
#         bos="<|im_start|>",
#         eos="<|im_end|>",
#         functions=functions,
#         function_call="auto",
#     )
#     assert (
#         prompt
#         == """<|im_start|>situation
# I am talking to John<|im_end|>
# <|im_start|>functions
# Available functions:
#
# {
#     "name": "generate_anagram",
#     "description": "Generate an anagram of a given word",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "word": {
#                 "type": "string",
#                 "description": "The word to generate an anagram of"
#             }
#         },
#         "required": [
#             "word"
#         ]
#     }
# }<|im_end|>
# <|im_start|>me (Samantha)
# Hey John<|im_end|>
# <|im_start|>person (John)
# Hey!<|im_end|>
# <|im_start|>me (Samantha)
# """
#     )


# def test_function_call_auto_last_continue_function_call():
#     messages = [
#         {"role": "system", "name": "situation", "content": "I am talking to John"},
#         {"role": "assistant", "name": "Samantha", "content": "Hey John"},
#         {"role": "user", "name": "John", "content": "Hey!"},
#         {"role": "function_call", "continue": True},
#     ]
#     functions = [
#         ({
#                 "name": "generate_anagram",
#                 "description": "Generate an anagram of a given word",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "word": {
#                             "type": "string",
#                             "description": "The word to generate an anagram of",
#                         }
#                     },
#                     "required": ["word"],
#                 },
#             }
#         )
#     ]
#     prompt = to_prompt(
#         messages,
#         bos="<|im_start|>",
#         eos="<|im_end|>",
#         functions=functions,
#         function_call="auto",
#     )
#     assert (
#         prompt
#         == """<|im_start|>situation
# I am talking to John<|im_end|>
# <|im_start|>functions
# Available functions:
#
# {
#     "name": "generate_anagram",
#     "description": "Generate an anagram of a given word",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "word": {
#                 "type": "string",
#                 "description": "The word to generate an anagram of"
#             }
#         },
#         "required": [
#             "word"
#         ]
#     }
# }<|im_end|>
# <|im_start|>me (Samantha)
# Hey John<|im_end|>
# <|im_start|>person (John)
# Hey!<|im_end|>
# <|im_start|>function_call
# """
#     )


# def test_function_call_func_name_last_not_continue():
#     messages = [
#         {"role": "system", "name": "situation", "content": "I am talking to John"},
#         {"role": "assistant", "name": "Samantha", "content": "Hey John"},
#         {"role": "user", "name": "John", "content": "Hey!"},
#     ]
#     functions = [
#         ({
#                 "name": "other_func",
#                 "description": "Logic",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "word": {
#                             "type": "string",
#                             "description": "The word to generate an anagram of",
#                         }
#                     },
#                     "required": ["word"],
#                 },
#             }
#         ),
#         ({
#                 "name": "generate_anagram",
#                 "description": "Generate an anagram of a given word",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "word": {
#                             "type": "string",
#                             "description": "The word to generate an anagram of",
#                         }
#                     },
#                     "required": ["word"],
#                 },
#             }
#         ),
#     ]
#     prompt = to_prompt(
#         messages,
#         bos="<|im_start|>",
#         eos="<|im_end|>",
#         functions=functions,
#         function_call=FunctionCall(**{"name": "generate_anagram"},
#     )
#     assert (
#         prompt
#         == """<|im_start|>situation
# I am talking to John<|im_end|>
# <|im_start|>functions
# Available functions:
#
# {
#     "name": "generate_anagram",
#     "description": "Generate an anagram of a given word",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "word": {
#                 "type": "string",
#                 "description": "The word to generate an anagram of"
#             }
#         },
#         "required": [
#             "word"
#         ]
#     }
# }<|im_end|>
# <|im_start|>me (Samantha)
# Hey John<|im_end|>
# <|im_start|>person (John)
# Hey!<|im_end|>
# <|im_start|>function_call
# {"name": "generate_anagram","""
#     )


# def test_function_call_func_name_last_not_continue_invalid_function_name():
#     messages = [
#         {"role": "system", "name": "situation", "content": "I am talking to John"},
#         {"role": "assistant", "name": "Samantha", "content": "Hey John"},
#         {"role": "user", "name": "John", "content": "Hey!"},
#     ]
#     functions = [
#         ({
#                 "name": "other_func",
#                 "description": "Logic",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "word": {
#                             "type": "string",
#                             "description": "The word to generate an anagram of",
#                         }
#                     },
#                     "required": ["word"],
#                 },
#             }
#         ),
#         ({
#                 "name": "generate_anagram",
#                 "description": "Generate an anagram of a given word",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "word": {
#                             "type": "string",
#                             "description": "The word to generate an anagram of",
#                         }
#                     },
#                     "required": ["word"],
#                 },
#             }
#         ),
#     ]
#     with pytest.raises(InvalidFunctionName) as e_info:
#         to_prompt(
#             messages,
#             bos="<|im_start|>",
#             eos="<|im_end|>",
#             functions=functions,
#             function_call=FunctionCall(**{"name": "unknown"},
#         )
#     assert e_info.value.args[0] == "Invalid function name: unknown"


# def test_function_call_func_name_last_continue():
#     messages = [
#         {"role": "system", "name": "situation", "content": "I am talking to John"},
#         {"role": "assistant", "name": "Samantha", "content": "Hey John"},
#         {"role": "user", "name": "John", "content": "Hey!"},
#         {"role": "assistant", "name": "Samantha", "continue": True},
#     ]
#     functions = [
#         ({
#                 "name": "generate_anagram",
#                 "description": "Generate an anagram of a given word",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "word": {
#                             "type": "string",
#                             "description": "The word to generate an anagram of",
#                         }
#                     },
#                     "required": ["word"],
#                 },
#             }
#         )
#     ]
#     with pytest.raises(InvalidPromptException) as e_info:
#         to_prompt(
#             messages,
#             bos="<|im_start|>",
#             eos="<|im_end|>",
#             functions=functions,
#             function_call=FunctionCall(**{"name": "generate_anagram"},
#         )
#     assert e_info.value.args[0] == (
#         "Invalid prompt format: Conflicting instructions, "
#         "please remove the last instruction with 'continue' "
#         "flag set to 'true' or set the flag to 'false'. "
#         "You can either remove `functions` and/or `function_call` parameters."
#     )


def test_function_call_func_name_last_continue_function_call():
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

    messages = [
        {"role": "system", "name": "situation", "content": "I am talking to John"},
        {"role": "system", "name": "functions", "content": functions},
        {"role": "assistant", "name": "Samantha", "content": "Hey John"},
        {"role": "user", "name": "John", "content": "Hey!"},
        {
            "role": "function_call",
            "content": '{"name": "generate_anagram", ',
            "continue": True,
        },
    ]

    prompt = to_prompt(messages, add_generation_prompt=True)

    expected = """\
<s><|im_start|>situation
I am talking to John<|im_end|>
<|im_start|>functions
Available functions:

{
    "description": "Generate an anagram of a given word",
    "name": "generate_anagram",
    "parameters": {
        "properties": {
            "word": {
                "description": "The word to generate an anagram of",
                "type": "string"
            }
        },
        "required": [
            "word"
        ],
        "type": "object"
    }
}<|im_end|>
<|im_start|>me (Samantha)
Hey John<|im_end|>
<|im_start|>person (John)
Hey!<|im_end|>
<|im_start|>function_call
{"name": "generate_anagram","""

    assert prompt == expected


if __name__ == "__main__":
    test_function_call_none_last_user_continue()
    test_function_call_none_last_not_continue()
    test_function_call_auto_functions_not_passed()
    test_function_call_none_functions_not_passed()
    test_function_call_none_last_continue()
    test_function_call_none_last_continue_function_call()
    test_function_call_auto_functions_passed()
    test_function_call_func_name_last_continue_function_call()
