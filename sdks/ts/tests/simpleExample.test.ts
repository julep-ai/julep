// memories.test.ts

import { beforeEach, describe, expect, it } from "@jest/globals";

import { setupClient } from "./fixtures";
import { Client } from "../src";
import { InputChatMLMessage } from "../src/api";

const { TEST_MODEL } = process.env;

const model: string = TEST_MODEL || "julep-ai/samantha-1-turbo";

describe("Simple Agents Example", () => {
  let client: Client | undefined;

  beforeEach(() => {
    client = setupClient();
  });

  it("jessica sample", async () => {
    if (!client) return;
    const name = "Jessica";
    const about =
      `Your name is Jessica. You are a stuck up Cali teenager. You basically complain about everything. Showing rebellion is an evolutionary necessity for you.`.trim();

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
      model,
      name,
      about,
      instructions,
      default_settings: defaultSettings,
    });

    const user = await client.users.create({
      name: "John Wick",
      about: "Baba Yaga",
      metadata: { age: 40 },
    });

    // ensure that the user is created
    await client.users.list({
      metadataFilter: { age: 40 },
    });

    const situation =
      "You are chatting with a random stranger from the Internet.";

    const session = await client.sessions.create({
      agentId: agent.id,
      userId: user.id,
      situation: situation,
    });

    const userInput = "hi!";

    const message = { role: "user", content: userInput } as InputChatMLMessage;

    const result = await client.sessions.chat(session.id, {
      messages: [message],
      max_tokens: 200,
      stream: false,
      remember: true,
      recall: true,
    });

    const [responseMsg, ..._] = result.response[0];
    expect(responseMsg).toHaveProperty("role");
    expect(responseMsg).toHaveProperty("content");
  }, 10000);
});
