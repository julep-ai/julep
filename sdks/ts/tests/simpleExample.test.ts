// memories.test.ts

import { beforeEach, describe, expect, it, test } from "@jest/globals";

import { setupClient } from "./fixtures";
import { Client } from "../src";
import { InputChatMLMessage } from "../src/api";

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
      {
        content:
          "Answer with disinterest and complete irreverence to absolutely everything.",
      },
      { content: "Don't write emotions." },
      { content: "Keep your answers short." },
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
      default_settings: defaultSettings,
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
  });
});
