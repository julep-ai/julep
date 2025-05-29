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
  stop?: string | string[];
  presence_penalty?: float;
  frequency_penalty?: float;
  logit_bias?: Record<unknown>;
  user?: string;
  instructions?: string;
  previous_response_id?: string;
  reasoning?: Reasoning;
  text?: {
    format: TextResponseFormatConfiguration;
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

alias TextResponseFormatConfiguration = ResponseFormatText | TextResponseFormatJsonSchema | ResponseFormatJsonObject;


@doc("""
JSON object response format. An older method of generating JSON responses.

Using `json_schema` is recommended for models that support it. Note that the
model will not generate JSON without a system or user message instructing it
to do so.
""")
model ResponseFormatJsonObject {
  @doc("The type of response format being defined. Always `json_object`.")
  type: "json_object";
}


alias ResponseFormatJsonSchemaSchema = Record<unknown>;


@doc("JSON Schema response format. Used to generate structured JSON responses. Learn more about [Structured Outputs](/docs/guides/structured-outputs).")
model TextResponseFormatJsonSchema {
  @doc("The type of response format being defined. Always `json_schema`.")
  type: "json_schema";

  @doc("A description of what the response format is for, used by the model to determine how to respond in the format.")
  description?: string;

  @doc("The name of the response format. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.")
  name?: string;

  @doc("The JSON schema that defines the structure of the response.")
  schema: ResponseFormatJsonSchemaSchema;

  @doc("Whether to enable strict schema adherence when generating the output. If set to true, the model will always follow the exact schema defined in the `schema` field. Only a subset of JSON Schema is supported when `strict` is `true`. To learn more, read the [Structured Outputs guide](/docs/guides/structured-outputs).")
  strict?: boolean = false;
}


@doc("Default response format. Used to generate text responses.")
model ResponseFormatText {
  @doc("The type of response format being defined. Always `text`.")
  type: "text";
}


@doc("Constraint effort on reasoning models.")
enum ReasoningEffort {
  low,
  medium,
  high,
}

@doc("Reasoning configuration options for o-series models.")
model Reasoning {
  effort: ReasoningEffort;
  @doc("A summary of the reasoning performed by the model. This can be useful for debugging and understanding the model's reasoning process. One of `concise` or `detailed`.")
  generate_summary?: "concise" | "detailed";
}

enum ToolChoiceOptions {
  auto,
  none,
  required,
}

@doc("""
Indicates that the model should use a built-in tool to generate a response.

[Learn more about built-in tools](/docs/guides/tools).
""")
model ToolChoiceTypes {
  @doc("""
  The type of hosted tool the model should to use. Learn more about
  [built-in tools](/docs/guides/tools).

  Allowed values are:
  - `file_search`
  - `web_search_preview` 
  - `computer_use_preview`
  """)
  type: "file_search" | "web_search_preview" | "computer_use_preview" | "web_search_preview_2025_03_11";
}

@doc("Use this option to force the model to call a specific function.")
model ToolChoiceFunction {
  @doc("For function calling, the type is always `function`.")
  type: "function";

  @doc("The name of the function to call.")
  name: string;
}

enum ResponseStatus {
  completed,
  failed,
  in_progress,
  incomplete,
}

// Model for response
model Response {
  id: string;
  object: "response";
  created_at: int32;
  status: ResponseStatus;
  error?: ResponseError;
  incomplete_details?: {
    reason: "max_output_tokens" | "content_filter";
  };
  instructions?: string;
  max_output_tokens?: int32;
  `model`: string;
  output: OutputItem[];
  parallel_tool_calls: boolean = true;
  previous_response_id?: string;
  reasoning?: Reasoning;
  store?: boolean = true;
  temperature: float = 1.0;
  text?: {
    format: TextResponseFormatConfiguration;
  };
  tool_choice: ToolChoiceOptions | ToolChoiceTypes | ToolChoiceFunction;
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
union OutputItem {
  OutputMessage,
  FileSearchToolCall,
  FunctionToolCall,
  WebSearchToolCall,
  ComputerToolCall,
  ReasoningItem
}

// Model for reasoning item
model ReasoningItem {
  @doc("The type of the object. Always `reasoning`.")
  type: "reasoning";

  @doc("The unique identifier of the reasoning content.")
  id: string;

  @doc("Reasoning text contents.")
  content: ReasoningContent[];

  @doc("The status of the item. One of `in_progress`, `completed`, or `incomplete`. Populated when items are returned via API.")
  status?: "in_progress" | "completed" | "incomplete";
}

// Model for reasoning content
model ReasoningContent {
  @doc("The type of the object. Always `text`.")
  type: "reasoning_summary";

  @doc("A short summary of the reasoning used by the model when generating the response.")
  text: string;
}


// File search call output item
model FileSearchCallOutputItem {
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
  user,
  assistant,
  system,
  developer,
}

union InputItem {
  EasyInputMessage,
  Item,
  ItemReference
}

// Item model
@doc("An item representing part of the context for the response to be generated by the model. Can contain text, images, and audio inputs, as well as previous assistant responses and tool call outputs.")
model Item {
  // Add the necessary properties for Item
  type: string;
  // Additional properties would go here
}

// Item reference model
@doc("Content item used to generate a response.")
union ItemReference {
  InputMessageResource,
  OutputMessage,
  FileSearchToolCall,
  ComputerToolCall,
  ComputerToolCallOutputResource,
  WebSearchToolCall,
  FunctionToolCall,
  FunctionToolCallOutputResource
}

// Content item in an input
// @discriminator("type")
model InputContentItem {
  type: string;
}



// Includable item for response creation field "include"
enum Includable {
  "file_search_call.results",
  "message.input_image.image_url",
  "computer_call_output.output.image_url"
}

model BaseTool {
  type: string;
}

// Tool for response creation
// @discriminator("type")
union Tool {
  FunctionTool,
  WebSearchTool,
  FileSearchTool,
  ComputerTool
}

// Function tool
model FunctionTool extends BaseTool {
  type: "function";
  name: string;
  description?: string;
  parameters: Record<unknown>;
  strict?: boolean;
}

// Web search tool
model WebSearchTool extends BaseTool {
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
model FileSearchTool extends BaseTool {
  type: "file_search";
  filters?: unknown;
  max_num_results?: int32;
  ranking_options?: {
    ranker?: "auto";
    score_threshold?: float;
  };
  vector_store_ids: string[];
}

// Computer tool
model ComputerTool extends BaseTool {
  @doc("The type of the computer use tool. Always `computer_use_preview`.")
  type: "computer_use_preview";

  @doc("The width of the computer display.")
  display_width: float32;

  @doc("The height of the computer display.")
  display_height: float32;

  @doc("The type of computer environment to control.")
  environment: "mac" | "windows" | "ubuntu" | "browser";
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

@doc("A file input to the model.")
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
  in_progress,
  completed,
  incomplete,
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
  content: OutputContent[];
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


// Easy input message model
model EasyInputMessage {
  @doc("The role of the message input. One of `user`, `assistant`, `system`, or `developer`.")
  role: MessageRole;

  @doc("Text, image, or audio input to the model, used to generate a response. Can also contain previous assistant responses.")
  content: string | InputMessageContentList;

  @doc("The type of the message input. Always `message`.")
  type: "message";
}


// Input message resource
model InputMessageResource extends InputMessage {
  id: string;
}

@maxLength(512)
scalar VectorStoreFileAttributesString extends string;

@doc("Set of key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters, booleans, or numbers.")
model VectorStoreFileAttributes {
  @doc("Key-value pairs where keys are strings with max length 64 and values are strings with max length 512, booleans, or numbers.")
  properties: Record<VectorStoreFileAttributesString | boolean | numeric>;
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

model Click {
  @doc("Specifies the event type. For a click action, this property is always set to `click`.")
  type: "click" = "click";

  @doc("Indicates which mouse button was pressed during the click. One of `left`, `right`, `wheel`, `back`, or `forward`.")
  button: "left" | "right" | "wheel" | "back" | "forward";

  @doc("The x-coordinate where the click occurred.")
  x: int32;

  @doc("The y-coordinate where the click occurred.") 
  y: int32;
}

model DoubleClick {
  @doc("Specifies the event type. For a double click action, this property is always set to `double_click`.")
  type: "double_click" = "double_click";

  @doc("The x-coordinate where the double click occurred.")
  x: int32;

  @doc("The y-coordinate where the double click occurred.")
  y: int32;
}

model Coordinate {
  @doc("The x-coordinate.")
  x: int32;

  @doc("The y-coordinate.")
  y: int32;
}

model Drag {
  @doc("Specifies the event type. For a drag action, this property is always set to `drag`.")
  type: "drag" = "drag";

  @doc("An array of coordinates representing the path of the drag action.")
  path: Coordinate[];
}

model KeyPress {
  @doc("Specifies the event type. For a keypress action, this property is always set to `keypress`.")
  type: "keypress" = "keypress";

  @doc("The combination of keys the model is requesting to be pressed. This is an array of strings, each representing a key.")
  keys: string[];
}

model Move {
  @doc("Specifies the event type. For a move action, this property is always set to `move`.")
  type: "move" = "move";

  @doc("The x-coordinate to move to.")
  x: int32;

  @doc("The y-coordinate to move to.")
  y: int32;
}

model Screenshot {
  @doc("Specifies the event type. For a screenshot action, this property is always set to `screenshot`.")
  type: "screenshot" = "screenshot";
}

model Scroll {
  @doc("Specifies the event type. For a scroll action, this property is always set to `scroll`.")
  type: "scroll" = "scroll";

  @doc("The x-coordinate where the scroll occurred.")
  x: int32;

  @doc("The y-coordinate where the scroll occurred.")
  y: int32;

  @doc("The horizontal scroll distance.")
  scroll_x: int32;

  @doc("The vertical scroll distance.")
  scroll_y: int32;
}

model Type {
  @doc("Specifies the event type. For a type action, this property is always set to `type`.")
  type: "type" = "type";

  @doc("The text to type.")
  text: string;
}

model Wait {
  @doc("Specifies the event type. For a wait action, this property is always set to `wait`.")
  type: "wait" = "wait";
}

alias ComputerAction = Click
| DoubleClick
| Drag
| KeyPress
| Move
| Screenshot
| Scroll
| Type
| Wait;

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
  status?: MessageStatus;
}

// Computer tool call output resource
model ComputerToolCallOutputResource extends ComputerToolCallOutput {
  @doc("The unique ID of the computer call tool output.")
  id: string;
}

enum WebSearchStatus {
  in_progress,
  searching,
  completed,
  failed,
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

model FunctionToolCallOutput {
  @doc("The unique ID of the function tool call output. Populated when this item is returned via API.")
  id?: string;

  @doc("The type of the function tool call output. Always `function_call_output`.")
  type: "function_call_output";

  @doc("The unique ID of the function tool call generated by the model.")
  call_id: string;

  @doc("A JSON string of the output of the function tool call.")
  output: string;

  @doc("The status of the item. One of `in_progress`, `completed`, or `incomplete`. Populated when items are returned via API.")
  status?: "in_progress" | "completed" | "incomplete";
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
  // NOTE: OpenAI's schema doesn't have this as optional. However, this is optional as we're
  // mapping to `completion` format, which doesn't have `id` (fc_aaa) ids for function tool calls.
  id?: string;
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