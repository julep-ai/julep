// sessions.test.js

const { v4: uuidv4 } = require("uuid");
const { setupClient } = require("./fixtures"); // Adjust path if necessary

describe("Sessions API", () => {
  let client;

  beforeAll(() => {
    client = setupClient();
  });

  test("sessions.get", async () => {
    const response = await client.sessions.get(uuidv4());

    expect(response).toHaveProperty("createdAt");
  });

  test("sessions.create", async () => {
    const response = await client.sessions.create({
      userId: uuidv4(),
      agentId: uuidv4(),
      situation: "test situation",
    });

    expect(response.createdAt).toBeDefined();
  });

  test("sessions.list", async () => {
    const response = await client.sessions.list();

    expect(response.length).toBeGreaterThan(0);
  });

  test("sessions.update", async () => {
    const response = await client.sessions.update({
      sessionId: uuidv4(),
      situation: "test situation",
    });

    expect(response.updatedAt).toBeDefined();
  });

  test("sessions.delete", async () => {
    const response = await client.sessions.delete(uuidv4());
    expect(response).toBeNull();
  });

  test("sessions.chat", async () => {
    const response = await client.sessions.chat({
      sessionId: uuidv4().toString(),
      messages: [
        new InputChatMlMessage({
          role: InputChatMlMessageRole.USER,
          content: "test content",
          name: "test name",
        }),
      ],
      tools: [
        new Tool({
          type: "function",
          function: {
            description: "test description",
            name: "test name",
            parameters: { testArg: "test val" },
          },
          id: uuidv4().toString(),
        }),
      ],
      toolChoice: new ToolChoiceOption("auto"),
      frequencyPenalty: 0.5,
      lengthPenalty: 0.5,
      logitBias: { test: 1 },
      maxTokens: 120,
      presencePenalty: 0.5,
      repetitionPenalty: 0.5,
      responseFormat: new ChatSettingsResponseFormat({
        type: ChatSettingsResponseFormatType.TEXT,
      }),
      seed: 1,
      stop: ["<"],
      stream: false,
      temperature: 0.7,
      topP: 0.9,
      recall: false,
      remember: false,
    });

    expect(response.object).toBe("chat.completion");
  });

  test("sessions.suggestions", async () => {
    const response = await client.sessions.suggestions(uuidv4());

    expect(response.length).toBeGreaterThan(0);
  });

  test("sessions.history", async () => {
    const response = await client.sessions.history(uuidv4());

    expect(response.length).toBeGreaterThan(0);
  });
});
