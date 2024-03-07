// fixtures.js

const { Client } = require("../");

const { TEST_API_KEY, TEST_API_URL } = process.env;

const baseUrl = TEST_API_URL || "http://localhost:8080/api";
const apiKey = TEST_API_KEY || "thisisnotarealapikey";

function setupClient() {
  // Mock server base URL
  const client = new Client({ apiKey, baseUrl });

  return client;
}

module.exports = { setupClient };
