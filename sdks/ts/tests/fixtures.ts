// fixtures.ts

import { Client } from "../";
import { config } from "dotenv";

config();

const { TEST_API_KEY, TEST_API_URL } = process.env;

const baseUrl: string = TEST_API_URL || "http://localhost:8080/api";
const apiKey: string = TEST_API_KEY || "thisisnotarealapikey";

const setupClient = (): Client => {

  const client = new Client({ apiKey, baseUrl });

  return client;
}

export { setupClient };
