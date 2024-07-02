# Adaptive Context ᴺᴱᵂ

### What is Adaptive Context?

Adaptive Context is a feature in Julep that intelligently manages the context size for long-running sessions. It allows users to continue adding messages to a session indefinitely without worrying about hitting context window limits or incurring excessive costs.

This feature uses a combination of techniques including compression, summarization, trimming, and entity extraction to compactify the input context when it approaches a predefined token budget. Adaptive Context works for both text-based and multimodal models, applying similar techniques to images when they are part of the context.

By enabling Adaptive Context, you can maintain extended conversations or process large amounts of data without losing significant information or experiencing interruptions due to context limitations.

<figure><img src="../../.gitbook/assets/image (5).png" alt=""><figcaption></figcaption></figure>

### Key Attributes

Adaptive Context is controlled by two main parameters within the Session object:



<table><thead><tr><th width="212">Attribute</th><th width="178">Type</th><th>Description</th></tr></thead><tbody><tr><td><code>token_budget</code></td><td><code>integer | null</code></td><td>Defines the maximum number of tokens allowed in the context. When null, it defaults to the size of the context window for the model used in the session.</td></tr><tr><td><code>context_overflow</code></td><td><code>"truncate" | "adaptive" | null</code></td><td>Determines how Julep handles context when it exceeds the token budget.</td></tr></tbody></table>

These attributes allow you to fine-tune how Julep manages context in your sessions, giving you control over token usage and context handling behavior.

### How Adaptive Context Works

Adaptive Context operates based on the `context_overflow` setting you choose for your session. Here's how each mode functions:

1. _Disabled_ (Default):
   * Julep doesn't apply any special handling.
   *   The model API throws an error if the context exceeds the model's context window limit.\


       <figure><img src="../../.gitbook/assets/image (6).png" alt="" width="375"><figcaption></figcaption></figure>
2. _Truncate_:
   * When the context size approaches the `token_budget`, Julep automatically drops messages from the beginning of the conversation.
   * The system prompt is always preserved.
   *   This ensures the context size stays within the specified `token_budget`.\


       <figure><img src="../../.gitbook/assets/image (7).png" alt=""><figcaption></figcaption></figure>
3.  _Adaptive_:

    * Julep actively monitors the context size.
    * When the size exceeds half of the `token_budget`, Julep initiates a background process:
      1. Extracts key entities from the context.
      2. Summarizes and merges redundant messages.
      3. Trims remaining messages to remove padding and repetitive content.
    * This process repeats until the token count is brought under the `token_budget`.
    * For multimodal models, similar techniques are applied to images in the context.



    <figure><img src="../../.gitbook/assets/image (1).png" alt=""><figcaption></figcaption></figure>

The Adaptive mode allows for indefinite extension of conversations while preserving the most relevant information, making it ideal for long-running sessions or processing large amounts of data.

### Using Adaptive Context

Enabling Adaptive Context is straightforward and can be done when creating a new session. Here's how to use it:

#### Example

```python
from julep import Client

# Initialize the Julep client
client = Client(api_key="your_api_key")

# Create a new session with Adaptive Context enabled
session = client.sessions.create(
    agent_id="your_agent_id",
    token_budget=2048,
    context_overflow="adaptive"
)

# Now you can use this session for your conversations
# The context will be adaptively managed as you interact
```

In this example:

* We set a `token_budget` of 2048 tokens.
* We enable the "adaptive" `context_overflow` mode.

You can adjust these parameters based on your specific needs. For instance, you might choose a larger `token_budget` for more complex conversations, or use "truncate" instead of "adaptive" if you prefer simpler context management.

Remember, if you don't specify these parameters, Julep will use the default settings (null for both), which means no special context management will be applied.

<figure><img src="../../.gitbook/assets/image (8).png" alt="" width="319"><figcaption></figcaption></figure>

### Benefits of Adaptive Context

* **Unlimited conversation length**: Continue interactions without hitting context limits.
* **Cost control**: Manage token usage efficiently, preventing unexpected cost increases.
* **Information preservation**: Retain key information while reducing redundancy.
* **Automated management**: No manual intervention needed for context handling.
* **Model flexibility**: Works with both text and multimodal models.

These benefits make Adaptive Context particularly useful for applications requiring extended dialogues, complex problem-solving, or processing of large datasets within a single session.

### Considerations and Best Practices

When choosing a `context_overflow` strategy, consider your specific use case:

1. None (Default):
   * Suitable for: Short, simple interactions or when you need full control over context management.
   * Not ideal for: Long conversations or processing large amounts of data.
2. Truncate:
   * Suitable for: Applications where recent context is more important than historical data, such as real-time customer support or live event commentary.
   * Not ideal for: Complex problem-solving tasks that require maintaining full conversation history.
3.  Adaptive:

    * Suitable for: Long-running analytical tasks, multi-step problem solving, or extended tutoring sessions where preserving key information is crucial.
    * Not ideal for: Applications where verbatim conversation history must be maintained, such as legal or compliance-related chat logs.

    <figure><img src="../../.gitbook/assets/image (9).png" alt=""><figcaption></figcaption></figure>

**Additional considerations**:

* Adjust `token_budget` based on your model and task complexity.
* For multimodal applications, consider the impact of image processing on context management.
* Monitor performance and adjust settings as needed for your specific use case.
* Be aware that aggressive context management may occasionally result in loss of nuanced details.

Experiment with different settings to find the optimal balance between context preservation and efficient token usage for your application.
