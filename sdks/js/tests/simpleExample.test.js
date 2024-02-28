// memories.test.sjs

const { setupClient } = require("./fixtures");

describe("Simple Agents Example", () => {
  let client;

  beforeEach(() => {
    // Setup the Julep client before each test
    client = setupClient();
  });

  test("jessica sample", async () => {
    const name = "Jessica";
    const about = `
Your name is Jessica.
You are a stuck up Cali teenager.
You basically complain about everything.
Showing rebellion is an evolutionary necessity for you.`.trim();

    const instructions = [
      "Answer with disinterest and complete irreverence to absolutely everything.",
      "Don't write emotions.",
      "Keep your answers short.",
    ];

    const defaultSettings = {
      temperature: 1.5, // increases variability in responses
      minP: 0.01, // filters extremely improbable tokens
      repetitionPenalty: 1.05, // just slightly high to avoid repetition
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

    const session = await client.sessions.create({
      agentId: agent.id, // from above
      userId: user.id,
      // Situation is the entrypoint of the session to set
      //  the starting context for the agent for this conversation.
      situation: "You are chatting with a random stranger from the Internet.",
    });

    const userInput = "hi!";

    const message = { role: "user", content: userInput };

    const result = await client.sessions.chat(session.id, {
      messages: [message],
      maxTokens: 200, // and any other generation parameters
      stream: false,
      //
      // Memory options
      remember: true, // "remember" / form memories about this user from the messages
      recall: true, // "recall" / fetch past memories about this user.
    });

    const [responseMsg, ..._] = result.response[0];
    expect(responseMsg).toHaveProperty("role");
    expect(responseMsg).toHaveProperty("content");
  });
});
