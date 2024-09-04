// memories.test.ts

import { beforeEach, describe, expect, it } from "@jest/globals";

import { setupClient } from "./fixtures";
import { Client } from "../src";
import { Entries_ChatMLRole } from "../src/api";

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
      requestBody: {
        model,
        name,
        about,
        instructions,
        default_settings: defaultSettings,
      },
    });

    const user = await client.users.create({
      requestBody: {
        name: "John Wick",
        about: "Baba Yaga",
        metadata: { age: 40 },
      },
    });

    // ensure that the user is created
    await client.users.list({
      metadataFilter: "{ age: 40 }",
      offset: 0,
    });

    const situation =
      "You are chatting with a random stranger from the Internet.";

    const session = await client.sessions.create({
      requestBody: {
        agent: agent.id,
        user: user.id,
        situation: situation,
        render_templates: true,
        context_overflow: "truncate",
        token_budget: 200,
      },
    });

    const userInput = "hi!";

    const message = { role: "user" as Entries_ChatMLRole, content: userInput };

    const result = await client.sessions.chat({
      id: session.id,
      requestBody: {
        messages: [message],
        max_tokens: 200,
        stream: false,
        remember: true,
        recall: true,
        save: true,
      },
    });

    const responseMsg = result.choices[0];
    expect(responseMsg).toHaveProperty("role");
    expect(responseMsg).toHaveProperty("content");
  }, 10000);
});
