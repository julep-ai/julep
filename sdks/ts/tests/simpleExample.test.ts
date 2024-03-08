In TypeScript, it looks like this:

```typescript
// memories.test.ts

import { setupClient } from "./fixtures";

describe("Simple Agents Example", () => {
  let client: any;

  beforeEach(() => {
    client = setupClient();
  });

  it("jessica sample", async () => {
    const name = "Jessica";
    const about = `Your name is Jessica. You are a stuck up Cali teenager. You basically complain about everything. Showing rebellion is an evolutionary necessity for you.`.trim();

    const instructions = [
      "Answer with disinterest and complete irreverence to absolutely everything.",
      "Don't write emotions.",
      "Keep your answers short.",
    ];

    const defaultSettings = {
      temperature: 1.5,
      minP: 0.01,
      repetitionPenalty: 1.05,
    };

    const agent = await client.agents.create({
      name: name,
      about: about,
      instructions: instructions,
      defaultSettings: defaultSettings,
    });

    const user = await client.users.create({
      name: "John Wick",
      about: "Baba Yaga",
    });

    const situation =
      "You are chatting with a random stranger from the Internet.";

    const session = await client.sessions.create({
      agentId: agent.id,
      userId: user.id,
      situation: situation,
    });

    const userInput = "hi!";

    const message = { role: "user", content: userInput };

    const result = await client.sessions.chat(session.id, {
      messages: [message],
      maxTokens: 200,
      stream: false,
      remember: true,
      recall: true,
    });

    const [responseMsg, ..._] = result.response[0];
    expect(responseMsg).toHaveProperty("role");
    expect(responseMsg).toHaveProperty("content");
  });
});
```

This is assuming that the setupClient function returns any datatype. You might want to replace any with the actual type in your code. Also, make sure to replace the import path if the file is not in the same directory.
