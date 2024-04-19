---
description: Jessica
---


<figure><img src="../.gitbook/assets/jessica.png" alt="Jessica page"><figcaption></figcaption></figure>

<figure><img src="../.gitbook/assets/jessica-prompt.png" alt="Jessica prompt"><figcaption></figcaption></figure>

Jessica is a satirical AI agent we designed using the Julep API for testing  interactions.  You can easily test and deploy Jessica or any custom-designed agent on the by visiting [this repo](https://github.com/julep-ai/jessica-public)

To run your own agent using this playground, you simply need to modify the `.env` file and add the following variables.

```.env
NEXT_PUBLIC_AGENT_ID=<AGENT_ID>
API_KEY=<API_KEY>
```

To get these variables, first you need to generate an API Key which you can get from the [Julep Platform](https://platform.julep.ai).
Lastly, you can generate the agent id using the Julep SDK using `createAgent`.
