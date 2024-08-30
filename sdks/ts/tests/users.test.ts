// tests/user.test.ts

import { beforeAll, describe, expect, test } from "@jest/globals";

import { setupClient } from "./fixtures";
import { Client } from "../src";
import { Common_ResourceCreatedResponse, Users_User as User } from "../src/api";

const mockUser = {
  requestBody: {
    name: "test user",
    about: "test user about",
  },
};

const mockUserUpdate = {
  name: "updated user",
  about: "updated user about",
};

describe("User API", () => {
  let client: Client;
  let testUser: Common_ResourceCreatedResponse;

  beforeAll(() => {
    client = setupClient();
  });

  test("users.create", async () => {
    const response = await client.users.create(mockUser);

    testUser = response;

    expect(response).toHaveProperty("created_at");
    expect(response).toHaveProperty("id");
    expect(response).toHaveProperty("jobs");
  });

  test("users.get", async () => {
    const response = await client.users.get({ id: testUser.id });

    expect(response.about).toBe(mockUser.requestBody.about);
    expect(response.name).toBe(mockUser.requestBody.name);
    expect(response).toHaveProperty("created_at");
  });

  test("users.update", async () => {
    const response = await client.users.update({
      id: testUser.id, requestBody: {
        name: mockUserUpdate.name,
        about: mockUserUpdate.about,
      }
    });

    expect(response.id).toBe(testUser.id);
    expect(response).toHaveProperty("updated_at");
    expect(response).toHaveProperty("jobs");
  });

  test("users.list", async () => {
    const response = await client.users.list({ offset: 0 });

    expect(response.items.length).toBeGreaterThan(0);

    const user = response.items.find((user) => user.id === testUser.id);

    expect(user).toBeDefined();
    expect(user!.id).toBe(testUser.id);
    expect(user).toHaveProperty("created_at");
    expect(user).toHaveProperty("updated_at");
  });

  test("users.delete", async () => {
    const response = await client.users.delete({ id: testUser.id });

    expect(response).toBeUndefined();
  });
});
