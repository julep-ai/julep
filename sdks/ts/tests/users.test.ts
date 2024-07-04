// tests/user.test.ts

import { beforeAll, describe, expect, test } from "@jest/globals";
import { v4 as uuidv4 } from "uuid";

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

const mockUserWithId = {
  name: "test user",
  id: uuidv4(),
  about: "test user about",
};

describe("User API", () => {
  let client: Client;
  let testUser: User;

  beforeAll(() => {
    client = setupClient();
  });

  test("users.create with ID", async () => {
    const response = await client.users.create(mockUserWithId);

    testUser = response;

    expect(response).toHaveProperty("created_at");
    expect(testUser.about).toBe(mockUser.about);
    expect(testUser.name).toBe(mockUser.name);
    expect(testUser.id).toBe(mockUserWithId.id);
  });

  test("users.create", async () => {
    const response = await client.users.create(mockUser);

    testUser = response;

    expect(response).toHaveProperty("created_at");
    expect(response.about).toBe(mockUser.about);
    expect(response.name).toBe(mockUser.name);
  });

  test("users.get", async () => {
    const response = await client.users.get(testUser.id);

    expect(response.about).toBe(mockUser.about);
    expect(response.name).toBe(mockUser.name);
    expect(response).toHaveProperty("created_at");
  });

  test("users.update", async () => {
    const response = await client.users.update(testUser.id, {
      name: mockUserUpdate.name,
    });

    expect(response.id).toBe(testUser.id);
    expect(response).toHaveProperty("updated_at");
    expect(response.name).toBe(mockUserUpdate.name);
  });

  test("users.update with overwrite", async () => {
    const response = await client.users.update(
      testUser.id,
      {
        ...mockUserUpdate,
      },
      true,
    );

    expect(response.id).toBe(testUser.id);
    expect(response).toHaveProperty("updated_at");
    expect(response.name).toBe(mockUserUpdate.name);
    expect(response.about).toBe(mockUserUpdate.about);
  });

  test("users.list", async () => {
    const response = await client.users.list();

    expect(response.length).toBeGreaterThan(0);

    const user = response.find((user) => user.id === testUser.id);

    expect(user).toBeDefined();
    expect(user!.id).toBe(testUser.id);
    expect(user).toHaveProperty("created_at");
    expect(user).toHaveProperty("updated_at");
  });

  test("users.delete", async () => {
    const response = await client.users.delete(testUser.id);

    expect(response).toBeUndefined();
  });
});
