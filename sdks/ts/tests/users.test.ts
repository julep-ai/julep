// tests/user.test.ts

import { v4 as uuidv4 } from "uuid";
import { setupClient } from "./fixtures";

describe("User API", () => {
  let client: any;

  beforeAll(() => {
    client = setupClient();
  });

  test("async users.get", async () => {
    const response = await client.users.get(uuidv4());
    expect(response).toHaveProperty("createdAt");
  });

  test("async users.create", async () => {
    const response = await client.users.create({
      name: "test user",
      about: "test user about",
    });

    expect(response).toHaveProperty("createdAt");
  });

  test("async users.list", async () => {
    const response = await client.users.list();
    expect(response.length).toBeGreaterThan(0);
    expect(response[0]).toHaveProperty("createdAt");
  });

  test("async users.update", async () => {
    const response = await client.users.update({
      userId: uuidv4(),
      name: "test user",
      about: "test user about",
    });

    expect(response).toHaveProperty("updatedAt");
  });

  test("async users.delete", async () => {
    const response = await client.users.delete(uuidv4());

    expect(response).toBeNull();
  });
});

