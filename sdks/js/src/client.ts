import { OpenAI, Chat, Completions } from 'openai'; // Assuming equivalent OpenAI types and functionality in TS
import { AgentsManager } from './managers/agent';
import { UsersManager } from './managers/user';
import { DocsManager } from './managers/doc';
import { MemoriesManager } from './managers/memory';
import { SessionsManager } from './managers/session';
import { ToolsManager } from './managers/tool';

class Client {
    private _apiClient: any; // Adjust based on JulepApi TypeScript equivalent
    private _openaiClient: OpenAI;

    agents: AgentsManager;
    users: UsersManager;
    sessions: SessionsManager;
    docs: DocsManager;
    memories: MemoriesManager;
    tools: ToolsManager;

    chat: Chat;
    completions: Completions;

    constructor(
        private api_key: string = process.env.JULEP_API_KEY!,
        private base_url: string = process.env.JULEP_API_URL!
    ) {
        if (!api_key || !base_url) {
            throw new Error('api_key and base_url must be provided or set as environment variables');
        }

        // Assuming JulepApi is an Axios instance or similar HTTP client tailored for TypeScript
        this._apiClient = new JulepApi({ api_key, base_url });

        this.agents = new AgentsManager(this._apiClient);
        this.users = new UsersManager(this._apiClient);
        this.sessions = new SessionsManager(this._apiClient);
        this.docs = new DocsManager(this._apiClient);
        this.memories = new MemoriesManager(this._apiClient);
        this.tools = new ToolsManager(this._apiClient);

        // Setup for OpenAI client assuming it's similar to the Python version
        this._openaiClient = new OpenAI(api_key, `${base_url}/v1`);

        this.chat = this._openaiClient.chat;
        this.completions = this._openaiClient.completions;
    }
}
