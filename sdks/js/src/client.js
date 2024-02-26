// client.js

const { OpenAI, Chat, Completions } = require("openai");
// const { AgentsManager } = require("./managers/agent");
const { UsersManager } = require("./managers/user");
// const { DocsManager } = require("./managers/doc");
const { MemoriesManager } = require("./managers/memory");
// const { SessionsManager } = require("./managers/session");
// const { ToolsManager } = require("./managers/tool");

const { JULEP_API_KEY, JULEP_API_URL } = require("./env");

const { JulepApiClient } = require("./api");

class Client {
  /**
   * @param {string} [apiKey=JULEP_API_KEY] - API key for the Julep API
   * @param {string} [baseUrl=JULEP_API_URL] - Base URL for the Julep API
   */
  constructor({ apiKey = JULEP_API_KEY, baseUrl = JULEP_API_URL }) {
    if (!apiKey || !baseUrl) {
      throw new Error(
        "apiKey and baseUrl must be provided or set as environment variables",
      );
    }

    /** @private */
    this._apiClient = new JulepApiClient({ apiKey, environment: baseUrl });

    /** @type {OpenAI} */
    this._openaiClient = new OpenAI({ apiKey, baseUrl: `${baseUrl}/v1` });

    /** @type {AgentsManager} */
    // this.agents = new AgentsManager(this._apiClient);

    /** @type {UsersManager} */
    this.users = new UsersManager(this._apiClient);

    /** @type {SessionsManager} */
    // this.sessions = new SessionsManager(this._apiClient);

    /** @type {DocsManager} */
    // this.docs = new DocsManager(this._apiClient);

    /** @type {MemoriesManager} */
    this.memories = new MemoriesManager(this._apiClient);

    /** @type {ToolsManager} */
    // this.tools = new ToolsManager(this._apiClient);

    /** @type {Chat} */
    this.chat = this._openaiClient.chat;

    /** @type {Completions} */
    this.completions = this._openaiClient.completions;
  }
}

exports.Client = Client;
