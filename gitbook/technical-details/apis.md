# APIs

## APIs Offered

We offer three different sets of APIs:

1. **Stateless API**: Stateless APIs are compatible with the `openai` API and can be used with their client libraries without modification.
2. **Stateful API with Memory**: (_Coming soon!_) We also offer a stateful API that:
   1. Manages user sessions.
   2. Simple API where you need to send _only_ the most recent message for a given "session".
   3. Handles the prompt and context window packing.
   4. (Optional) Can learn and remember facts and "beliefs" about individual users.
3. **Custom finetuning**: (_Coming soon!_)

***

### Notes

* Our models are trained as `ChatCompletion` models and the recommended way is to call the API using the `ChatCompletion` class by passing a list of [chatml](https://github.com/openai/openai-python/blob/main/chatml.md) messages.
*   However, you can also format prompts directly and use the `Completion` class according to our prompt format.

    \
    (This is subject to change and is not recommended except if you know what you're doing)

{% hint style="info" %}
**Important**: Make sure to consult the [model cards](models.md) for the correct if you choose to format the prompts yourself and use the `Completion` classes instead.
{% endhint %}
