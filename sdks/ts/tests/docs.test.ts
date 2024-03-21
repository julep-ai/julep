// docs.test.ts

import { afterAll, beforeAll, describe, expect, test } from "@jest/globals";

import { setupClient } from "./fixtures";
import { Client } from "../src";
import { Agent, User } from "../src/api";

describe("Julep Client Tests", () => {
  let client: Client;
  let testAgent: Partial<Agent> & { id: string };
  let testUser: User;
  let testAgentDocId: string;
  let testUserDocId: string;

  const mockDoc = { title: "test title", content: "test content" };

  beforeAll(async () => {
    client = setupClient();
    testAgent = await client.agents.create({
      name: "test agent",
      about: "test about",
      instructions: [],
    });
    testUser = await client.users.create({
      name: "test user",
      about: "test about",
    });
  });

  afterAll(async () => {
    await client.agents.delete(testAgent.id);
    await client.users.delete(testUser.id);
  });

  test("agent docs.create", async () => {
    const response = await client.docs.create({
      agentId: testAgent.id,
      doc: mockDoc,
    });

    testAgentDocId = response.id;

    expect(response).toHaveProperty("created_at");
    expect(response.content).toBe(mockDoc.content);
    expect(response.title).toBe(mockDoc.title);
  });

  test("user docs.create", async () => {
    const response = await client.docs.create({
      userId: testUser.id,
      doc: mockDoc,
    });

    testUserDocId = response.id;

    expect(response).toHaveProperty("created_at");
    expect(response.content).toBe(mockDoc.content);
    expect(response.title).toBe(mockDoc.title);
  });

  test("agent docs.get", async () => {
    const response = await client.docs.get({ agentId: testAgent.id });

    expect(response?.items!.length).toBeGreaterThan(0);
    expect(response?.items![0].content).toBe(mockDoc.content);
    expect(response?.items![0].title).toBe(mockDoc.title);
  });

  test("user docs.get", async () => {
    const response = await client.docs.get({ userId: testUser.id });

    expect(response?.items!.length).toBeGreaterThan(0);
    expect(response?.items![0].content).toBe(mockDoc.content);
    expect(response?.items![0].title).toBe(mockDoc.title);
  });

  test("agent docs.delete", async () => {
    const response = await client.docs.delete({
      agentId: testAgent.id,
      docId: testAgentDocId,
    });

    expect(response).toBeUndefined();
  });

  test("user docs.delete", async () => {
    const response = await client.docs.delete({
      userId: testUser.id,
      docId: testUserDocId,
    });

    expect(response).toBeUndefined();
  });
});
