// docs.test.js

const { v4: uuidv4 } = require("uuid");

const { setupClient } = require("./fixtures");

describe("Julep Client Tests", () => {
  let client;

  beforeAll(() => {
    client = setupClient();
  });

  test("agent docs.get", async () => {
    const response = await client.docs.get({ agentId: uuidv4() });

    expect(response.length).toBeGreaterThan(0);
    expect(response[0]).toHaveProperty("createdAt");
  });

  test("user docs.get", async () => {
    const response = await client.docs.get({ userId: uuidv4() });

    expect(response.length).toBeGreaterThan(0);
    expect(response[0]).toHaveProperty("createdAt");
  });

  test("agent docs.create", async () => {
    const response = await client.docs.create({
      agentId: uuidv4(),
      doc: { title: "test title", content: "test content" },
    });

    expect(response).toHaveProperty("createdAt");
  });

  test("user docs.create", async () => {
    const response = await client.docs.create({
      userId: uuidv4(),
      doc: { title: "test title", content: "test content" },
    });

    expect(response).toHaveProperty("createdAt");
  });

  test("agent docs.delete", async () => {
    const response = await client.docs.delete({
      agentId: uuidv4(),
      docId: uuidv4(),
    });

    expect(response).toBeNull();
  });

  test("user docs.delete", async () => {
    const response = await client.docs.delete({
      userId: uuidv4(),
      docId: uuidv4(),
    });

    expect(response).toBeNull();
  });
});
