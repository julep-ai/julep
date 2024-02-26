// fixtures.js

const { Client } = require("../");

function setupClient() {
  // Mock server base URL
  const baseURL = "http://localhost:8080";
  const client = new Client({ apiKey: "thisisnotarealapikey", baseURL });

  return client;
}

module.exports = { setupClient };
