// client.js

const { OpenAI, Chat, Completions } = require("openai");
const { AgentsManager } = require("./managers/agent");
const { UsersManager } = require("./managers/user");
const { DocsManager } = require("./managers/doc");
const { MemoriesManager } = require("./managers/memory");
const { SessionsManager } = require("./managers/session");
const { ToolsManager } = require("./managers/tool");

const { JULEP_API_KEY, JULEP_API_URL } = require("./env");

class Client {
  /**
   * @param {string} [api_key=JULEP_API_KEY] - API key for the Julep API
   * @param {string} [base_url=JULEP_API_URL] - Base URL for the Julep API
   */
  constructor(api_key = JULEP_API_KEY, base_url = JULEP_API_URL) {
    if (!api_key || !base_url) {
      throw new Error(
        "api_key and base_url must be provided or set as environment variables",
      );
    }

    /** @private */
    this._apiClient = new JulepApi({ api_key, base_url });

    /** @type {OpenAI} */
    this._openaiClient = new OpenAI(api_key, `${base_url}/v1`);

    /** @type {AgentsManager} */
    this.agents = new AgentsManager(this._apiClient);

    /** @type {UsersManager} */
    this.users = new UsersManager(this._apiClient);

    /** @type {SessionsManager} */
    this.sessions = new SessionsManager(this._apiClient);

    /** @type {DocsManager} */
    this.docs = new DocsManager(this._apiClient);

    /** @type {MemoriesManager} */
    this.memories = new MemoriesManager(this._apiClient);

    /** @type {ToolsManager} */
    this.tools = new ToolsManager(this._apiClient);

    /** @type {Chat} */
    this.chat = this._openaiClient.chat;

    /** @type {Completions} */
    this.completions = this._openaiClient.completions;
  }
}
