// memories.test.ts

import { v4 as uuidv4 } from "uuid";
import { beforeEach, describe, expect, test } from "@jest/globals";

import { setupClient } from "./fixtures";

describe("Julep Client Tests", () => {
  let client: any;

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
    expect(response[0]).toHaveProperty("createdAt");
  });
});
