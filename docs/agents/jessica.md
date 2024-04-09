---
description: Jessica
---

# Jessica Playground

## What is Jessica

<figure><img src="../.gitbook/assets/jessica.png" alt="Jessica page"><figcaption></figcaption></figure>

<figure><img src="../.gitbook/assets/jessica-prompt.png" alt="Jessica prompt"><figcaption></figcaption></figure>

Jessica is an example agent that uses the Julep Agents API that you can access at [https://jessica.julep.ai](https://jessica.julep.ai).

The playground is also open source which you can access [here](https://github.com/julep-ai/jessica-public).

## How to run and deploy

To run your own agent using this playground, you simply need to modify the `.env` file and add the following variables.

```.env
NEXT_PUBLIC_AGENT_ID=<AGENT_ID>
API_KEY=<API_KEY>
```

To get these variables, first you need to generate an API Key which you can get from the [Julep Platform](https://platform.julep.ai).
Lastly, you can generate the agent id using the Julep SDK using `createAgent`.
