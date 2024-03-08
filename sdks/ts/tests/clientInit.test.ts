// clientInit.test.ts

import { v4 as uuidv4 } from "uuid";
import { beforeAll, describe, expect, it, test } from "@jest/globals";

import { setupClient } from "./fixtures";

describe("Client Request Tests", () => {
  let client: any;

  beforeAll(() => {
    client = setupClient();
  });

  it("test client instantiation", async () => {
    expect(client).toBeDefined();
  });

  // it("test client request", async () => {
  //   const response = await client.agents.get(uuidv4());
  //   expect(response).toBeDefined();
  // });
});
