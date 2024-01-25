# APIs

## APIs Offered

We offer two main sets of APIs:

1. **Agents API with Memory**: The main offering of the platform is a stateful API that:
   1. Creates and manages agents,
   1. Manages user sessions,
   1. Only needs the most recent message for a given "session",
   1. Handles the prompt and context window packing, and
   1. Learns and remembers facts and "beliefs" about individual users.

1. **Model API**: Model APIs are compatible with the `openai` API and can be used with their client libraries without modification.

***

### Notes

* Our models are trained as `ChatCompletion` models and the recommended way is to call the API using the `ChatCompletion` class by passing a list of [chatml](https://github.com/openai/openai-python/blob/main/chatml.md) messages.
*   However, you can also format prompts directly and use the `Completion` class according to our prompt format.

    \
    (This is subject to change and is not recommended except if you know what you're doing)

{% hint style="info" %}
**Important**: Make sure to consult the [model cards](models.md) for the correct if you choose to format the prompts yourself and use the `Completion` classes instead.
{% endhint %}
