export interface Agent {
  name: string;
  about: string;
  instructions?: Array<import("../").Instruction>;
  createdAt?: Date | null;
  updatedAt?: Date | null;
  id: string;
  defaultSettings?: AgentDefaultSettings | null;
  model: string;
  metadata?: AgentMetadata | null;
}

export enum AgentDefaultSettingsPreset {
  ProblemSolving = "problem_solving",
  Conversational = "conversational",
  Fun = "fun",
  Prose = "prose",
  Creative = "creative",
  Business = "business",
  Deterministic = "deterministic",
  Code = "code",
  Multilingual = "multilingual",
}

export interface AgentDefaultSettings {
  frequencyPenalty?: number | null;
  lengthPenalty?: number | null;
  presencePenalty?: number | null;
  repetitionPenalty?: number | null;
  temperature?: number | null;
  topP?: number | null;
  minP?: number | null;
  preset?: AgentDefaultSettingsPreset | null;
}

export interface AgentMetadata {
  [key: string]: any;
}

export type Belief = {
  type: "belief";
  subject?: string | null;
  content: string;
  rationale?: string | null;
  weight: number;
  sentiment: number;
  createdAt: Date;
  id: string;
};

export interface ChatInputData {
  messages: Array<InputChatMlMessage>;
  tools?: Array<Tool> | null;
  toolChoice?: ChatInputDataToolChoice | null;
}

export type ChatInputDataToolChoice = ToolChoiceOption | NamedToolChoice;

export interface ChatMlMessage {
  role: ChatMlMessageRole;
  content: string;
  name?: string | null;
  createdAt: Date;
  id: string;
}

export enum ChatMlMessageRole {
  User = "user",
  Assistant = "assistant",
  System = "system",
  FunctionCall = "function_call",
}

export interface ChatResponse {
  id: string;
  finishReason: ChatResponseFinishReason;
  response: Array<Array<ChatMlMessage>>;
  usage: CompletionUsage;
  jobs?: Array<string> | null;
}

export type ChatResponseFinishReason = "stop" | "length" | "tool_calls" | "content_filter" | "function_call";

export interface ChatSettings {
  frequencyPenalty?: number;
  lengthPenalty?: number;
  logitBias?: Record<string, number | undefined>;
  maxTokens?: number;
  presencePenalty?: number;
  repetitionPenalty?: number;
  responseFormat?: ChatSettingsResponseFormat;
  seed?: number;
  stop?: ChatSettingsStop;
  stream?: boolean;
  temperature?: number;
  topP?: number;
  minP?: number;
  preset?: ChatSettingsPreset;
}

export enum ChatSettingsPreset {
  ProblemSolving = "problem_solving",
  Conversational = "conversational",
  Fun = "fun",
  Prose = "prose",
  Creative = "creative",
  Business = "business",
  Deterministic = "deterministic",
  Code = "code",
  Multilingual = "multilingual",
}

export interface ChatSettingsResponseFormat {
  type?: ChatSettingsResponseFormatType;
  pattern?: string;
  schema?: ChatSettingsResponseFormatSchema;
}

interface ChatSettingsResponseFormatSchema {
  // This schema is an empty object
}

export enum ChatSettingsResponseFormatType {
  Text = "text",
  JsonObject = "json_object",
  Regex = "regex",
}

type ChatSettingsStop = string | string[];

export type CompletionUsage = {
  completionTokens: number;
  promptTokens: number;
  totalTokens: number;
};

interface CreateAgentRequestMetadata {}

export interface CreateDoc {
  title: string;
  content: string;
  metadata?: CreateDocMetadata;
}

interface CreateDocMetadata {}

interface CreateSessionRequestMetadata {}

export interface CreateToolRequest {
  type: CreateToolRequestType;
  function: Promise<import("..").FunctionDef>;
}

enum CreateToolRequestType {
  Function = "function",
  Webhook = "webhook",
}

interface CreateUserRequestMetadata {}

export type Doc = {
  title: string;
  content: string;
  id: string;
  createdAt: Date;
  metadata?: any; // Adjust the type according to the actual metadata structure
};

type DocMetadata = {};

type Entity = {
  id: string;
};

type Episode = {
  type: "episode";
  subject?: string;
  content: string;
  weight: number;
  createdAt: Date;
  lastAccessedAt: Date;
  happenedAt: Date;
  duration?: number;
  id: string;
}; // Adjust the type definition if needed

type FunctionCallOption = {
  name: string;
};

export type FunctionDef = {
  description?: string;
  name: string;
  parameters: FunctionParameters;
};

type FunctionParameters = Record<string, any>;

type GetAgentDocsResponse = {
  items?: Doc[];
};

export type GetAgentMemoriesResponse = {
  items?: Memory[];
};

export type GetAgentToolsResponse = {
  items?: Tool[];
};

export type GetHistoryResponse = {
  items?: ChatMlMessage[];
};

export type GetSuggestionsResponse = {
  items?: Suggestion[];
};

export type GetUserDocsResponse = {
  items?: Doc[];
};

export type InputChatMlMessage = {
  role: InputChatMlMessageRole;
  content: string;
  name?: string;
  continue?: boolean;
};

type InputChatMlMessageRole = "user" | "assistant" | "system" | "function_call";

export type Instruction = {
  content: string;
  important?: boolean;
};

type JobStatus = {
  name: string;
  reason?: string;
  createdAt: Date;
  updatedAt?: Date;
  id: string;
  hasProgress?: boolean;
  progress?: number;
  state: JobStatusState;
};

type JobStatusState = "pending" | "in_progress" | "retrying" | "succeeded" | "aborted" | "failed" | "unknown";

export type ListAgentsResponse = {
  items: Agent[];
};

export type ListSessionsResponse = {
  items: Session[];
};

export type ListUsersResponse = {
  items: User[];
};

type Memory = Belief | Episode | Entity;

export type MemoryAccessOptions = {
  recall?: boolean;
  remember?: boolean;
};
