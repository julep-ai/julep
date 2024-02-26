// clientInit.test.js

const { v4: uuidv4 } = require("uuid");
const { setupClient } = require("./fixtures");

describe("Client Request Tests", () => {
  let client;

  beforeAll(() => {
    client = setupClient();
  });

  test("test client instantiation", async () => {
    expect(client).toBeDefined();
  });

  // test("test client request", async () => {
  //   const response = await client.agents.get(uuidv4());
  //   expect(response).toBeDefined();
  // });
});
