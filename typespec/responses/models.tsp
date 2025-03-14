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
  output: string;
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

alias Annotation = FileCitation | UrlCitation | FilePath;

// File citation
model FileCitation {
  @doc("The type of the file citation. Always `file_citation`.")
  type: "file_citation";

  @doc("The index of the file in the list of files.")
  index: int32;

  @doc("The ID of the file.")
  file_id: string;
}

// URL citation
model UrlCitation {
  @doc("The URL of the web resource.")
  url: string;

  @doc("The title of the web resource.")
  title: string;

  @doc("The type of the URL citation. Always `url_citation`.")
  type: "url_citation";

  @doc("The index of the first character of the URL citation in the message.")
  start_index: int32;

  @doc("The index of the last character of the URL citation in the message.")
  end_index: int32;
}

model FilePath {
  @doc("The type of the file path. Always `file_path`.")
  type: "file_path";

  @doc("The ID of the file.")
  file_id: string;

  @doc("The index of the file in the list of files.")
  index: int32;
}

enum MessageRole {
  user
  assistant
  system
  developer
}

// Input item for creating a response
model InputItem {
  role: MessageRole;
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

model InputText {
  @doc("The type of the input item. Always `input_text`.")
  type: "input_text";

  @doc("The text input to the model.")
  text: string;
}

model InputImage {
  @doc("The type of the input item. Always `input_image`.")
  type: "input_image";

  @doc("The URL of the image to be sent to the model. A fully qualified URL or base64 encoded image in a data URL.")
  image_url?: string;

  @doc("The ID of the file to be sent to the model.")
  file_id?: string;

  @doc("The detail level of the image to be sent to the model. One of `high`, `low`, or `auto`. Defaults to `auto`.")
  detail: "high" | "low" | "auto" = "auto";
}

model InputFile {
  @doc("The type of the input item. Always `input_file`.")
  type: "input_file";

  @doc("The ID of the file to be sent to the model.")
  file_id?: string;

  @doc("The name of the file to be sent to the model.")
  filename?: string;

  @doc("The content of the file to be sent to the model.")
  file_data?: string;
}

alias InputContent = InputText | InputImage | InputFile;

// A list of one or many input items to the model, containing different content types
model InputMessageContentList is InputContent[];

enum MessageStatus {
  in_progress
  completed
  incomplete
}

// Input message
model InputMessage {
  type: "message";
  role: MessageRole;
  status: MessageStatus;
  content: InputMessageContentList;
}

model OutputMessage {
  id: string;
  type: "message";
  role: MessageRole;
  status: MessageStatus;
  content: OutputContent;
}

// A refusal from the model
model Refusal {
  @doc("The type of the refusal. Always `refusal`.")
  type: "refusal";

  @doc("The refusal explanation from the model.")
  refusal: string;
}

model OutputText {
  @doc("The type of the output text. Always `output_text`.")
  type: "output_text";

  @doc("The text output from the model.")
  text: string;

  @doc("The annotations of the text output.")
  annotations: Annotation[];
}

alias OutputContent = OutputText | Refusal;


// Input message resource
model InputMessageResource extends InputMessage {
  id: string;
}


// File search tool call
model FileSearchToolCall {
  @doc("The unique ID of the file search tool call.")
  id: string;

  @doc("The type of the file search tool call. Always `file_search_call`.")
  type: "file_search_call";

  @doc("The status of the file search tool call. One of `in_progress`, `searching`, `incomplete` or `failed`")
  status: "in_progress" | "searching" | "completed" | "incomplete" | "failed";

  @doc("The queries used to search for files.")
  queries: string[];

  @doc("The results of the file search tool call.")
  results?: {
    @doc("The unique ID of the file.")
    file_id: string;

    @doc("The text that was retrieved from the file.")
    text: string;

    @doc("The name of the file.")
    filename: string;

    @doc("The attributes of the file.")
    attributes: VectorStoreFileAttributes;

    @doc("The relevance score of the file - a value between 0 and 1.")
    score: float32;
  }[];
}

model ComputerToolCallSafetyCheck {
  @doc("The ID of the pending safety check.")
  id: string;

  @doc("The type of the pending safety check.")
  code: string;

  @doc("Details about the pending safety check.")
  message: string;
}

// Computer tool call
model ComputerToolCall {
  @doc("The type of the computer call. Always `computer_call`.")
  type: "computer_call";

  @doc("The unique ID of the computer call.")
  id: string;

  @doc("An identifier used when responding to the tool call with output.")
  call_id: string;

  @doc("The action to perform.")
  action: ComputerAction;

  @doc("The pending safety checks for the computer call.")
  pending_safety_checks: ComputerToolCallSafetyCheck[];

  @doc("The status of the item. One of `in_progress`, `completed`, or `incomplete`. Populated when items are returned via API.")
  status: "in_progress" | "completed" | "incomplete";
}

model ComputerScreenshotImage {
  @doc("Specifies the event type. For a computer screenshot, this property is always set to `computer_screenshot`.")
  type: "computer_screenshot";

  @doc("The URL of the screenshot image.")
  image_url?: string;

  @doc("The identifier of an uploaded file that contains the screenshot.")
  file_id?: string;
}

model ComputerToolCallOutput {
  @doc("The type of the computer tool call output. Always `computer_call_output`.")
  type: "computer_call_output";

  @doc("The ID of the computer tool call output.")
  id?: string;

  @doc("The ID of the computer tool call that produced the output.")
  call_id: string;

  @doc("The safety checks reported by the API that have been acknowledged by the developer.")
  acknowledged_safety_checks?: ComputerToolCallSafetyCheck[];

  @doc("The output screenshot image.")
  output: ComputerScreenshotImage;

  @doc("The status of the message input. One of `in_progress`, `completed`, or `incomplete`. Populated when input items are returned via API.")
  status?: "in_progress" | "completed" | "incomplete";
}

// Computer tool call output resource
model ComputerToolCallOutputResource extends ComputerToolCallOutput {
  @doc("The unique ID of the computer call tool output.")
  id: string;
}

enum WebSearchStatus {
  in_progress
  searching
  completed
  failed
}

// Web search tool call
model WebSearchToolCall {
  @doc("The unique ID of the web search tool call.")
  id: string;

  @doc("The type of the web search tool call. Always `web_search_call`.")
  type: "web_search_call";

  @doc("The status of the web search tool call.")
  status: WebSearchStatus;
}

// Function tool call
model FunctionToolCall {
  @doc("The unique ID of the function tool call.")
  id: string;

  @doc("The type of the function tool call. Always `function_call`.")
  type: "function_call";

  @doc("The unique ID of the function tool call generated by the model.")
  call_id: string;

  @doc("The name of the function to run.")
  name: string;

  @doc("A JSON string of the arguments to pass to the function.")
  arguments: string;

  @doc("The status of the item. One of `in_progress`, `completed`, or `incomplete`. Populated when items are returned via API.")
  status?: "in_progress" | "completed" | "incomplete";
}

// Function tool call output resource
model FunctionToolCallOutputResource extends FunctionToolCallOutput {
  @doc("The unique ID of the function call tool output.")
  id: string;
}

alias ItemResource = InputMessageResource
| OutputMessage
| FileSearchToolCall
| ComputerToolCall
| ComputerToolCallOutputResource
| WebSearchToolCall
| FunctionToolCall
| FunctionToolCallOutputResource;

model ResponseItemList {
  @doc("The type of object returned, must be `list`.")
  object: "list";

  @doc("A list of items used to generate this response.")
  data: ItemResource[];

  @doc("Whether there are more items available.")
  has_more: boolean;

  @doc("The ID of the first item in the list.")
  first_id: string;

  @doc("The ID of the last item in the list.")
  last_id: string;
}