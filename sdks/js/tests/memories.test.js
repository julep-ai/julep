// tests.js

const { v4: uuidv4 } = require("uuid");

const { Memory } = require("../src/api/serialization/types");
const { setupClient } = require("./fixtures");

describe("Julep Client Tests", () => {
  let client;

  beforeEach(() => {
    // Setup the Julep client before each test
    client = setupClient();
  });

  test("async memories.list", async () => {
    const response = await client.memories.list({
      agentId: uuidv4(),
      query: "test query",
      types: "test types",
      userId: uuidv4(),
      limit: 100,
      offset: 0,
    });

    expect(response.length).toBeGreaterThan(0);
    expect(response[0]).toBeInstanceOf(Memory);
  });
});
