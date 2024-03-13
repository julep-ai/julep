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
import { CustomHttpRequest } from "./utils/requestConstructor";

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
   * @param {ClientOptions} [options={}] - Options for the client.
   * @param {string} [options.apiKey=JULEP_API_KEY] - API key for the Julep API.
   * @param {string} [options.baseUrl=JULEP_API_URL] - Base URL for the Julep API.
   * @throws {Error} Throws an error if apiKey and baseUrl are not provided.
   */
  constructor({
    apiKey = JULEP_API_KEY,
    baseUrl = JULEP_API_URL || "https://api-alpha.julep.ai/api",
  }: ClientOptions = {}) {
    if (!apiKey || !baseUrl) {
      throw new Error("apiKey and baseUrl must be provided or set as environment variables");
    }

    this._apiClient = new JulepApiClient({ TOKEN: apiKey, BASE: baseUrl }, CustomHttpRequest);

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

  /** Manager for interacting with agents. */
  agents: AgentsManager;

  /** Manager for interacting with users. */
  users: UsersManager;

  /** Manager for interacting with sessions. */
  sessions: SessionsManager;

  /** Manager for interacting with documents. */
  docs: DocsManager;

  /** Manager for interacting with memories. */
  memories: MemoriesManager;

  /** Manager for interacting with tools. */
  tools: ToolsManager;

  /** OpenAI Chat API. */
  chat: Chat;

  /** OpenAI Completions API. */
  completions: Completions;
}
