// sessions.test.ts
import { afterAll, beforeAll, describe, expect, it } from "@jest/globals";

import { setupClient } from "./fixtures"; // Adjust path if necessary
import {
  Agents_Agent as Agent,
  Chat_MessageChatResponse,
  Common_ResourceCreatedResponse,
} from "../src/api";
import { Client } from "../src";

const { TEST_MODEL } = process.env;

const model: string = TEST_MODEL || "julep-ai/samantha-1-turbo";

const mockAgent = {
  model,
  name: "test agent",
  about: "test agent about",
  instructions: ["test agent instructions"],
  default_settings: { temperature: 0.5 },
};

const mockUser = {
  name: "test user",
  about: "test user about",
};

const mockSession = {
  situation: "test situation",
  render_templates: true,
  token_budget: 200,
  context_overflow: null,
};

const mockSessionWithTemplate = {
  situation: "Say 'hello {{ session.metadata.arg }}'",
  metadata: { arg: "banana" },
  renderTemplates: true,
  render_templates: true,
  token_budget: 200,
  context_overflow: null,
};

const mockSessionUpdate = {
  situation: "updated situation",
  render_templates: true,
  token_budget: 200,
  context_overflow: null,
};

describe("Sessions API", () => {
  let client: Client;
  let testSessionId: string;
  let testUser: Common_ResourceCreatedResponse;
  let testAgent: Partial<Agent> & { id: string };

  beforeAll(async () => {
    client = setupClient();
    testAgent = await client.agents.create({ requestBody: mockAgent });
    testUser = await client.users.create({ requestBody: mockUser });
  });

  afterAll(async () => {
    await client.agents.delete({ id: testAgent.id });
    await client.users.delete({ id: testUser.id });
  });

  it("sessions.create", async () => {
    const response = await client.sessions.create({
      requestBody: {
        user: testUser.id,
        agent: testAgent.id,
        ...mockSession,
      },
    });

    testSessionId = response.id;

    expect(response).toBeDefined();
    expect(response).toHaveProperty("created_at");
  });

  it("sessions.get", async () => {
    const response = await client.sessions.get({ id: testSessionId });

    expect(response).toHaveProperty("created_at");
    expect(response.situation).toBe(mockSession.situation);
  });

  it("sessions.update", async () => {
    const response = await client.sessions.update({
      id: testSessionId,
      requestBody: mockSessionUpdate,
    });

    expect(response).toHaveProperty("updated_at");
  });

  it("sessions.update with overwrite", async () => {
    const response = await client.sessions.update({
      id: testSessionId,
      requestBody: mockSessionUpdate,
    });

    expect(response).toHaveProperty("updated_at");
  });

  it("sessions.list", async () => {
    const response = await client.sessions.list({ offset: 0 });

    expect(response.items.length).toBeGreaterThan(0);

    const session = response.items.find(
      (session) => session.id === testSessionId,
    );

    expect(session?.situation).toBe(mockSessionUpdate.situation);
  });

  it("sessions.chat", async () => {
    const response = await client.sessions.chat({
      id: testSessionId,
      requestBody: {
        messages: [
          {
            role: "user",
            content: "test content",
            name: "test name",
          },
        ],
        max_tokens: 1000,
        presence_penalty: 0.5,
        repetition_penalty: 0.5,
        temperature: 0.7,
        top_p: 0.9,
        recall: false,
        remember: false,
        save: false,
        stream: false,
      },
    });

    expect(response.choices).toBeDefined();
  }, 5000);

  it("sessions.chat with template", async () => {
    const session = await client.sessions.create({
      requestBody: {
        user: testUser.id,
        agent: testAgent.id,
        ...mockSessionWithTemplate,
      },
    });

    const response = await client.sessions.chat({
      id: session.id,
      requestBody: {
        messages: [
          {
            role: "user",
            content: "please say it",
          },
        ],
        max_tokens: 10,
        recall: false,
        remember: false,
        save: false,
        stream: false,
      },
    });

    expect(response.choices).toBeDefined();

    // Check that the template was filled in
    expect(response.choices[0][0].content).toContain(
      mockSessionWithTemplate.metadata.arg,
    );
  }, 5000);

  //   it("sessions.suggestions", async () => {
  //     const response = await client.sessions.suggestions(testSessionId);

  //     expect(response.length).toBeGreaterThan(0);
  //   });

  it("sessions.history", async () => {
    const response = await client.sessions.history({ id: testSessionId });

    expect(response.entries.length).toBeGreaterThan(0);
  });

  it("sessions.deleteHistory", async () => {
    const response = await client.sessions.deleteHistory({ id: testSessionId });

    expect(response).toBeUndefined();
  });

  it("sessions.delete", async () => {
    const response = await client.sessions.delete({ id: testSessionId });
    expect(response).toBeUndefined();
  });
});
