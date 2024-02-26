// fixtures.js

const { Client } = require("../");

function setupClient() {
  // Mock server base URL
  const baseUrl = "http://localhost:8080";
  const apiKey = "thisisnotarealapikey";
  const client = new Client({ apiKey, baseUrl });

  return client;
}

module.exports = { setupClient };
