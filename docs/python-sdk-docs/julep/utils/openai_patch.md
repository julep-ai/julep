# Openai Patch

[Julep Python SDK Index](../../README.md#julep-python-sdk-index) / [Julep](../index.md#julep) / [Utils](./index.md#utils) / Openai Patch

> Auto-generated documentation for [julep.utils.openai_patch](../../../../../../julep/utils/openai_patch.py) module.

- [Openai Patch](#openai-patch)
  - [patch_chat_acreate](#patch_chat_acreate)
  - [patch_chat_create](#patch_chat_create)
  - [patch_completions_acreate](#patch_completions_acreate)
  - [patch_completions_create](#patch_completions_create)

## patch_chat_acreate

[Show source in openai_patch.py:95](../../../../../../julep/utils/openai_patch.py#L95)

Asynchronously patches the `chat.completions.create` method of the OpenAI client.

This function updates the `chat.completions.create` method to an asynchronous version, enabling the inclusion of additional parameters and adjustments to its behavior.

#### Arguments

- client (OpenAI): The OpenAI client instance to be patched.

#### Returns

- `-` *OpenAI* - The patched OpenAI client instance with the updated `chat.completions.create` method.

#### Signature

```python
def patch_chat_acreate(client: OpenAI): ...
```



## patch_chat_create

[Show source in openai_patch.py:270](../../../../../../julep/utils/openai_patch.py#L270)

#### Signature

```python
def patch_chat_create(client: OpenAI): ...
```



## patch_completions_acreate

[Show source in openai_patch.py:20](../../../../../../julep/utils/openai_patch.py#L20)

Asynchronously patches the `completions.create` method of the OpenAI client.

This function replaces the original `completions.create` method with a custom asynchronous version that allows for additional parameters and custom behavior.

#### Arguments

- client (OpenAI): The OpenAI client instance to be patched.

#### Returns

- `-` *OpenAI* - The patched OpenAI client instance with the modified `completions.create` method.

#### Signature

```python
def patch_completions_acreate(client: OpenAI): ...
```



## patch_completions_create

[Show source in openai_patch.py:195](../../../../../../julep/utils/openai_patch.py#L195)

Patches the `completions.create` method (non-async version) of the OpenAI client.

This function replaces the original `completions.create` method with a custom version that supports additional parameters and custom behavior, without changing it to an asynchronous function.

#### Arguments

- client (OpenAI): The OpenAI client instance to be patched.

#### Returns

- `-` *OpenAI* - The patched OpenAI client instance with the modified `completions.create` method.

#### Signature

```python
def patch_completions_create(client: OpenAI): ...
```