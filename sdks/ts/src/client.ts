import { OpenAI } from "openai";
import { Chat, Completions } from "openai/resources/index";
import { AgentsManager } from "./managers/agent";
import { UsersManager } from "./managers/user";
import { DocsManager } from "./managers/doc";
import { MemoriesManager } from "./managers/memory";
import { SessionsManager } from "./managers/session";
import { ToolsManager } from "./managers/tool";
import { JulepApiClient } from "./api";
import { JULEP_API_KEY, JULEP_API_URL } from "./env";
import { patchCreate } from "./utils/openaiPatch";

interface ClientOptions {
  apiKey?: string;
  baseUrl?: string;
}

/**
 * Client for interacting with the Julep API and OpenAI.
 */
export class Client {
  private _apiClient: JulepApiClient;
  private _openaiClient: OpenAI;

  /**
   * Creates an instance of Client.
   * Initializes the client with the provided or default API key and base URL. If neither are provided nor set as environment variables, an error is thrown.
   * @param {ClientOptions} [options={}] - Configuration options for the client.
   * @param {string} [options.apiKey=JULEP_API_KEY] - API key for the Julep API. Defaults to the JULEP_API_KEY environment variable if not provided.
   * @param {string} [options.baseUrl=JULEP_API_URL] - Base URL for the Julep API. Defaults to the JULEP_API_URL environment variable or "https://api-alpha.julep.ai/api" if not provided.
   * @throws {Error} Throws an error if both apiKey and baseUrl are not provided and not set as environment variables.
   */
  constructor({
    apiKey = JULEP_API_KEY,
    baseUrl = JULEP_API_URL || "https://api-alpha.julep.ai/api",
  }: ClientOptions = {}) {
    if (!apiKey || !baseUrl) {
      throw new Error(
        "apiKey and baseUrl must be provided or set as environment variables",
      );
    }

    this._apiClient = new JulepApiClient({
      TOKEN: apiKey,
      BASE: baseUrl,
      WITH_CREDENTIALS: false,
    });

    const openaiBaseUrl = new URL(baseUrl).origin;
    this._openaiClient = new OpenAI({
      apiKey,
      baseURL: `${openaiBaseUrl}/v1`,
      dangerouslyAllowBrowser: true,
    });

    this.agents = new AgentsManager(this._apiClient);
    this.users = new UsersManager(this._apiClient);
    this.sessions = new SessionsManager(this._apiClient);
    this.docs = new DocsManager(this._apiClient);
    this.memories = new MemoriesManager(this._apiClient);
    this.tools = new ToolsManager(this._apiClient);
    this.chat = this._openaiClient.chat;
    patchCreate(this.chat.completions, this.chat);
    this.completions = this._openaiClient.completions;
    patchCreate(this.completions);
  }

  /**
   * Manager for interacting with agents.
   * Provides methods to manage and interact with agents within the Julep API.
   */
  agents: AgentsManager;

  /**
   * Manager for interacting with users.
   * Offers functionalities to handle user accounts and their data.
   */
  users: UsersManager;

  /**
   * Manager for interacting with sessions.
   * Facilitates the creation, management, and retrieval of user sessions.
   */
  sessions: SessionsManager;

  /**
   * Manager for interacting with documents.
   * Enables document management including creation, update, and deletion.
   */
  docs: DocsManager;

  /**
   * Manager for interacting with memories.
   * Allows for storing and retrieving user-specific data and preferences.
   */
  memories: MemoriesManager;

  /**
   * Manager for interacting with tools.
   * Provides access to various utility tools and functionalities.
   */
  tools: ToolsManager;

  /**
   * OpenAI Chat API.
   * This is patched to enhance functionality and ensure compatibility with Julep API.
   */
  chat: Chat;

  /**
   * OpenAI Completions API.
   * Enhanced with custom patches for improved integration and usage within Julep.
   */
  completions: Completions;
}
