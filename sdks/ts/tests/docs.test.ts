// docs.test.ts

import { v4 as uuidv4 } from "uuid";
import { beforeAll, describe, expect, test } from "@jest/globals";

import { setupClient } from "./fixtures";
import { Client } from "../src";

describe("Julep Client Tests", () => {
  let client: Client;
  let agent: any;
  let user: any;

  beforeAll(async () => {
    client = setupClient();
    agent = await client.agents.create({
      name: "test agent",
      about: "test about",
      instructions: [],
    });
    user = await client.users.create({
      name: "test user",
      about: "test about",
    });
  });

  test("agent docs.get", async () => {
    const response = await client.docs.get({ agentId: uuidv4() });

    expect(response?.items!.length).toBeGreaterThan(0);
    expect(response?.items![0]).toHaveProperty("id");
  });

  test("user docs.get", async () => {
    const response = await client.docs.get({ userId: user.id });

    expect(response?.items!.length).toBeGreaterThan(0);
    expect(response?.items![0]).toHaveProperty("id");
  });

  test("agent docs.create", async () => {
    const response = await client.docs.create({
      agentId: agent.id,
      doc: { title: "test title", content: "test content" },
    });

    expect(response).toHaveProperty("id");
  });

  test("user docs.create", async () => {
    const response = await client.docs.create({
      userId: user.id,
      doc: { title: "test title", content: "test content" },
    });

    expect(response).toHaveProperty("createdAt");
  });

  test("agent docs.delete", async () => {
    const createResponse = await client.docs.create({
      agentId: agent.id,
      doc: { title: "test title", content: "test content" },
    });

    const response = await client.docs.delete({
      agentId: agent.id,
      docId: createResponse.id,
    });

    expect(response).toBeUndefined();
  });

  test("user docs.delete", async () => {
    const createResponse = await client.docs.create({
      userId: user.id,
      doc: { title: "test title", content: "test content" },
    });

    const response = await client.docs.delete({
      userId: user.id,
      docId: createResponse.id,
    });

    expect(response).toBeUndefined();
  });
});
