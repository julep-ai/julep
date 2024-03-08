// docs.test.ts

import { v4 as uuidv4 } from "uuid";
import { beforeAll, describe, expect, test } from "@jest/globals";

import { setupClient } from "./fixtures";
import { Client } from "../src";

describe("Julep Client Tests", () => {
  let client: Client;

  beforeAll(() => {
    client = setupClient();
  });

  test("agent docs.get", async () => {
    const response = await client.docs.get({ agentId: uuidv4() });

    expect(response?.items!.length).toBeGreaterThan(0);
    expect(response?.items![0]).toHaveProperty("id");
  });

  test("user docs.get", async () => {
    const response = await client.docs.get({ userId: uuidv4() });

    expect(response?.items!.length).toBeGreaterThan(0);
    expect(response?.items![0]).toHaveProperty("id");
  });

  test("agent docs.create", async () => {
    const response = await client.docs.create({
      agentId: uuidv4(),
      doc: { title: "test title", content: "test content" },
    });

    expect(response).toHaveProperty("id");
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

    expect(response).toBeUndefined();
  });

  test("user docs.delete", async () => {
    const response = await client.docs.delete({
      userId: uuidv4(),
      docId: uuidv4(),
    });

    expect(response).toBeUndefined();
  });
});
