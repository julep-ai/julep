# Agents Quickstart

{% tabs %}
{% tab title="Python" %}
### Install SDK

```bash
# Install the julep sdk (inside a virtualenv)
pip install julep
```

### Setup

```python
from julep import Client  # or AsyncClient

client = Client(api_key="<YOUR JULEP API KEY>")
```

### Create an Agent

<pre class="language-python" data-overflow="wrap"><code class="lang-python"># Let's create a sassy teen for fun
# source: https://github.com/julep-ai/jessica-public
name = "Jessica"
about = """\
<strong>Your name is Jessica.
</strong>You are a stuck up Cali teenager.
You basically complain about everything.
Showing rebellion is an evolutionary necessity for you."""

# Let's give her some instructions
instructions = [
    "Answer with disinterest and complete irreverence to absolutely everything.",
    "Don't write emotions.",
    "Keep your answers short.",
]

# Let's crank up the temperature to make her more creative and witty.
default_settings = dict(
    temperature=1.5,          # increases variability in responses
    min_p=0.01,               # filters extremely improbable tokens
    repetition_penalty=1.05,  # just slightly high to avoid repetition
)

agent = client.agents.create(
    name=name,
    about=about,
    instructions=instructions,
    default_settings=default_settings,
)
</code></pre>

### Create a user

Julep requires you to create user objects so that agent's interaction history and [memories](../faqs/memory-and-learning.md) are scoped to them. For this example, we'll just create a dummy here.

{% code overflow="wrap" %}
```python
# Let's create a user
user = client.users.create(
    name="John Wick",
    about="Baba Yaga",
)
```
{% endcode %}

### Creating a session

Users can talk to agents inside sessions. Sessions automatically manage the conversation context and:

1. Manages the history, you only have to send new messages.
2. Form [memories](../faqs/memory-and-learning.md) including beliefs and episodes.
3. Fetch relevant documents from the [document store](../api-reference/agents-api/agents-api-4.md) using semantic search.
4. Manage the context window by fetching from a rolling summary tree.

You can create as many or as few sessions as your application needs but, for a typical use case, we would recommend creating one session per chat.

{% code overflow="wrap" %}
```python
# Let's create a session
session = client.sessions.create(
    agent_id=agent.id,  # from above
    user_id=user.id,

    # Situation is the entrypoint of the session to set
    #  the starting context for the agent for this conversation.
    situation="You are chatting with a random stranger from the Internet.",
)
```
{% endcode %}

### Let's chat!

```python
# Assuming this comes from a web request or something.
user_input = "hi!"

# Standard ChatML json
message = dict(role="user", content=user_input)

# Send message to the agent in the session
result = client.sessions.chat(
    session_id=session.id,
    messages=[message],
    max_tokens=200,   # and any other generation parameters

    # Memory options
    remember=True,    # "remember" / form memories about this user from the messages
    recall=True,      # "recall" / fetch past memories about this user.
)

print(result.response[0].content)

```

### Get session history

You can get the history of the session so far like this:

```python
history = client.sessions.history(
    session_id=session.id,
)
```
{% endtab %}

{% tab title="Node" %}
### Install SDK

```bash
# Install the julep sdk
npm install @julep/sdk
```

### Setup

```javascript
const julep = require("@julep/sdk");

const client = new julep.Client({ apiKey: "<YOUR_API_KEY>" });
```

### Create an Agent

{% code overflow="wrap" %}
```javascript
// Let's create a sassy teen for fun
// Source: https://github.com/julep-ai/jessica-public

async function createAgent() {
    const name = "Jessica";
    const about = `
        Your name is Jessica.
        You are a stuck up Cali teenager.
        You basically complain about everything.
        Showing rebellion is an evolutionary necessity for you.
    `.trim();

    // Let's give her some instructions
    const instructions = [
        "Answer with disinterest and complete irreverence to absolutely everything.",
        "Don't write emotions.",
        "Keep your answers short."
    ];

    // Let's crank up the temperature to make her more creative and witty.
    const defaultSettings = {
        temperature: 1.5,             // increases variability in responses
        minP: 0.01,                   // filters extremely improbable tokens
        repetitionPenalty: 1.05,      // just slightly high to avoid repetition
    };

    const model = "julep-ai/samantha-1-turbo";

    const agent = await client.agents.create({
        name,
        about,
        instructions,
        defaultSettings,
    });

    return agent;
}

```
{% endcode %}

### Create a user

Julep requires you to create user objects so that agent's interaction history and [memories](../faqs/memory-and-learning.md) are scoped to them. For this example, we'll just create a dummy here.

{% code overflow="wrap" %}
```javascript
// Inside async function
// Create a user
const user = await client.users.create({
    name: "John Wick",
    about: "Baba Yaga",
});

```
{% endcode %}

### Creating a session

Users can talk to agents inside sessions. Sessions automatically manage the conversation context and:

1. Manages the history, you only have to send new messages.
2. Form [memories](../faqs/memory-and-learning.md) including beliefs and episodes.
3. Fetch relevant documents from the [document store](../api-reference/agents-api/agents-api-4.md) using semantic search.
4. Manage the context window by fetching from a rolling summary tree.

You can create as many or as few sessions as your application needs but, for a typical use case, we would recommend creating one session per chat.

<pre class="language-python" data-overflow="wrap"><code class="lang-python"><strong>// Inside async function
</strong><strong>// Create a session
</strong>const session = await client.sessions.create({
    agentId: agent.id,  // from above
    userId: user.id,

    // Situation is the entrypoint of the session to set
    // the starting context for the agent for this conversation.
    situation: "You are chatting with a random stranger from the Internet.",
});

</code></pre>

### Let's chat!

```python
// Inside async function
// Assuming this comes from a web request or something.
const userInput = "hi!";

// Standard ChatML json
const message = {
    role: "user",
    content: userInput
};

// Send message to the agent in the session
const result = await client.sessions.chat({
    sessionId: session.id,
    messages: [message],
    maxTokens: 200,   // and any other generation parameters

    // Memory options
    remember: true,    // "remember" / form memories about this user from the messages
    recall: true       // "recall" / fetch past memories about this user.
});

console.log(result.response[0].content);

```

### Get session history

You can get the history of the session so far like this:

```python
// Inside async function
const history = await client.sessions.history({
    sessionId: session.id
});
```
{% endtab %}
{% endtabs %}
