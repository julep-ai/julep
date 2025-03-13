import "@typespec/http";
import "../common";

using Common;

namespace Responses;

// Common response properties
model ResponseProperties {
  instructions?: string;
  previous_response_id?: string;
  reasoning?: {
    effort?: "low" | "medium" | "high";
    summary?: string;
  };
  text?: {
    format?: {
      type: "text" | "json_object";
    };
  };
  tool_choice?: "auto" | "none" | {
    type: "function";
    function: {
      name: string;
    };
  };
  tools?: Tool[];
  truncation?: "disabled" | "auto";
  metadata?: Record<unknown>;
}

// Model for creating a response
model CreateResponse {
  `model`: string;
  input: string | InputItem[];
  include?: Includable[];
  parallel_tool_calls?: boolean = true;
  store?: boolean = true;
  stream?: boolean = false;
  max_tokens?: int32;
  temperature?: float = 1.0;
  top_p?: float = 1.0;
  n?: int32;
  stop?: string | string[];
  presence_penalty?: float;
  frequency_penalty?: float;
  logit_bias?: Record<unknown>;
  user?: string;
  instructions?: string;
  previous_response_id?: string;
  reasoning?: {
    effort?: "low" | "medium" | "high";
  };
  text?: {
    format?: {
      type: "text" | "json_object";
    };
  };
  tool_choice?: "auto" | "none" | {
    type: "function";
    function: {
      name: string;
    };
  };
  tools?: Tool[];
  truncation?: "disabled" | "auto";
  metadata?: Record<unknown>;
}

// Model for response
model Response {
  id: string;
  object: "response";
  created_at: int32;
  status: "completed" | "failed" | "in_progress" | "incomplete";
  error?: ResponseError;
  incomplete_details?: {
    reason: "max_output_tokens" | "content_filter";
  };
  instructions?: string;
  max_output_tokens?: int32;
  `model`: string;
  output: MessageOutputItem[];
  parallel_tool_calls: boolean = true;
  previous_response_id?: string;
  reasoning?: {
    effort?: "low" | "medium" | "high";
    summary?: string;
  };
  store?: boolean = true;
  temperature: float = 1.0;
  text?: {
    format?: {
      type: "text" | "json_object";
    };
  };
  tool_choice: "auto" | "none" | {
    type: "function";
    function: {
      name: string;
    };
  };
  tools: Tool[];
  top_p: float = 1.0;
  truncation: "disabled" | "auto";
  usage: ResponseUsage;
  user?: string;
  metadata: Record<unknown>;
}

// Model for response usage information
model ResponseUsage {
  input_tokens: int32;
  input_tokens_details: {
    cached_tokens: int32;
  };
  output_tokens: int32;
  output_tokens_details: {
    reasoning_tokens: int32;
  };
  total_tokens: int32;
}

// Model for response error
model ResponseError {
  message: string;
  type: string;
  param?: string;
  code?: string;
}

// Model for output items in a response
// @discriminator("type")
model OutputItem {
  type: string;
}

// Message output item
model MessageOutputItem extends OutputItem {
  type: "message";
  id: string;
  status: "completed" | "in_progress";
  role: "assistant";
  content: TextContentPart[];
}

// Function call output item
model FunctionCallOutputItem extends OutputItem {
  type: "function_call";
  id: string;
  call_id: string;
  name: string;
  arguments: string;
  status: "completed" | "in_progress";
}

// Web search call output item
model WebSearchCallOutputItem extends OutputItem {
  type: "web_search_call";
  id: string;
  status: "completed" | "in_progress";
}

// File search call output item
model FileSearchCallOutputItem extends OutputItem {
  type: "file_search_call";
  id: string;
  status: "completed" | "in_progress";
  queries: string[];
  results?: unknown;
}

// Content part in a message
// @discriminator("type")
model ContentPart {
  type: string;
}

// Text content part
model TextContentPart extends ContentPart {
  type: "output_text";
  text: string;
  annotations: Annotation[];
}

// Annotation in text content
// @discriminator("type")
model Annotation {
  type: string;
}

// URL citation annotation
model UrlCitationAnnotation extends Annotation {
  type: "url_citation";
  start_index: int32;
  end_index: int32;
  url: string;
  title: string;
}

// File citation annotation
model FileCitationAnnotation extends Annotation {
  type: "file_citation";
  index: int32;
  file_id: string;
  filename: string;
}

// Input item for creating a response
model InputItem {
  role: "user" | "assistant" | "system" | "developer";
  content: InputContentItem[];
}

// Content item in an input
// @discriminator("type")
model InputContentItem {
  type: string;
}

// Text content item in an input
model TextInputContentItem extends InputContentItem {
  type: "input_text";
  text: string;
}

// Image content item in an input
model ImageInputContentItem extends InputContentItem {
  type: "input_image";
  image_url: string;
}

// Includable item for response creation field "include"
enum Includable {
  "file_search_call.results",
  "message.input_image.image_url",
  "computer_call_output.output.image_url"
}

// Tool for response creation
// @discriminator("type")
model Tool {
  type: string;
}

// Function tool
model FunctionTool extends Tool {
  type: "function";
  name: string;
  description?: string;
  parameters: Record<unknown>;
  strict?: boolean;
}

// Web search tool
model WebSearchTool extends Tool {
  type: "web_search_preview";
  domains?: string[];
  search_context_size?: "small" | "medium" | "large";
  user_location?: {
    type: "approximate";
    city?: string;
    country?: string;
    region?: string;
    timezone?: string;
  };
}

// File search tool
model FileSearchTool extends Tool {
  type: "file_search";
  filters?: unknown;
  max_num_results?: int32;
  ranking_options?: {
    ranker?: "auto";
    score_threshold?: float;
  };
  vector_store_ids: string[];
}