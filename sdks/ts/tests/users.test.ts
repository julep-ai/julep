// tests/user.test.ts

import { beforeAll, describe, expect, test } from "@jest/globals";

import { setupClient } from "./fixtures";
import { Client } from "../src";
import { User } from "../src/api";

const mockUser = {
  name: "test user",
  about: "test user about",
};

const mockUserUpdate = {
  name: "updated user",
  about: "updated user about",
};

describe("User API", () => {
  let client: Client;
  let testUser: User;

  beforeAll(() => {
    client = setupClient();
  });

  test("async users.create", async () => {
    const response = await client.users.create(mockUser);

    testUser = response;

    expect(response).toHaveProperty("created_at");
    expect(response.about).toBe(mockUser.about);
    expect(response.name).toBe(mockUser.name);
  });

  test("async users.get", async () => {
    const response = await client.users.get(testUser.id);

    expect(response.about).toBe(mockUser.about);
    expect(response.name).toBe(mockUser.name);
    expect(response).toHaveProperty("created_at");
  });

  test("async users.update", async () => {
    const response = await client.users.update(testUser.id, mockUserUpdate);

    expect(response.id).toBe(testUser.id);
    expect(response).toHaveProperty("updated_at");
    expect(response.name).toBe(mockUserUpdate.name);
    expect(response.about).toBe(mockUserUpdate.about);
  });

  test("async users.list", async () => {
    const response = await client.users.list();

    expect(response.length).toBeGreaterThan(0);

    const user = response.find((user) => user.id === testUser.id);

    expect(user).toBeDefined();
    expect(user!.id).toBe(testUser.id);
    expect(user).toHaveProperty("created_at");
    expect(user).toHaveProperty("updated_at");
    expect(user!.name).toBe(mockUserUpdate.name);
    expect(user!.about).toBe(mockUserUpdate.about);
  });

  test("async users.delete", async () => {
    const response = await client.users.delete(testUser.id);

    expect(response).toBeUndefined();
  });
});
