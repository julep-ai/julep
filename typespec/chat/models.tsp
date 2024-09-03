import "@typespec/http";

import "../common";
import "../docs";
import "../entries";
import "../tools";

using TypeSpec.Http;

using Common;
using Docs;
using Entries;
using Tools;

namespace Chat;

//
// CHAT MODELS
//

/**
 * The reason the model stopped generating tokens. This will be `stop`
 * if the model hit a natural stop point or a provided stop sequence,
 * `length` if the maximum number of tokens specified in the request
 * was reached, `content_filter` if content was omitted due to a flag
 * from our content filters, `tool_calls` if the model called a tool.
 */
enum FinishReason {
    stop,
    length,
    content_filter,
    tool_calls,
}

/** Determines how the session accesses history and memories */
model MemoryAccessOptions {
    /** DISABLED: Whether this interaction should form new memories or not (will be enabled in a future release) */
    @visibility("read") // DISABLED
    remember: boolean = false;

    /** Whether previous memories and docs should be recalled or not */
    recall: boolean = true;

    /** Whether this interaction should be stored in the session history or not */
    save: boolean = true;
}

model SimpleCompletionResponseFormat {
    /** The format of the response */
    type: "text" | "json_object" = "text";
}

model SchemaCompletionResponseFormat {
    /** The format of the response */
    type: "json_schema" = "json_schema";

    /** The schema of the response */
    json_schema: Record<unknown>;
}

alias CompletionResponseFormat = SimpleCompletionResponseFormat | SchemaCompletionResponseFormat;

model CommonChatSettings {
    /** Identifier of the model to be used */
    `model`?: identifierSafeUnicode;

    /** Indicates if the server should stream the response as it's generated */
    stream: boolean = false;

    /** Up to 4 sequences where the API will stop generating further tokens. */
    @maxItems(4)
    stop: string[] = #[];

    /** If specified, the system will make a best effort to sample deterministically for that particular seed value */
    @minValue(-1)
    @maxValue(1000)
    seed?: int16;

    /** The maximum number of tokens to generate in the chat completion */
    @minValue(1)
    max_tokens?: uint32;

    /** Modify the likelihood of specified tokens appearing in the completion */
    logit_bias?: Record<logit_bias>;

    /** Response format (set to `json_object` to restrict output to JSON) */
    response_format?: CompletionResponseFormat;

    /** Agent ID of the agent to use for this interaction. (Only applicable for multi-agent sessions) */
    agent?: uuid;
}

model OpenAISettings {
    /** Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. */
    @minValue(-2)
    @maxValue(2)
    frequency_penalty?: float32;

    /** Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. */
    @minValue(-2)
    @maxValue(2)
    presence_penalty?: float32;

    /** What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. */
    @minValue(0)
    @maxValue(5)
    temperature?: float32;

    /** Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both. */
    @minValue(0)
    @maxValue(1)
    top_p?: float32;
}

model vLLMSettings {
    /** Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. */
    @minValue(0)
    @maxValue(2)
    repetition_penalty?: float32;

    /** Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. */
    @minValue(0)
    @maxValue(2)
    length_penalty?: float32;

    /** Minimum probability compared to leading token to be considered */
    @minValue(0)
    @maxValue(1)
    min_p?: float32;
}

/** Default settings for the chat session (also used by the agent) */
model DefaultChatSettings extends OpenAISettings {
    ...vLLMSettings;
}

model ChatSettings extends DefaultChatSettings {
    ...CommonChatSettings;
}

/** Usage statistics for the completion request */
model CompetionUsage {
    /** Number of tokens in the generated completion */
    @visibility("read")
    completion_tokens?: uint32;

    /** Number of tokens in the prompt */
    @visibility("read")
    prompt_tokens?: uint32;

    /** Total number of tokens used in the request (prompt + completion) */
    @visibility("read")
    total_tokens?: uint32;
}

model ChatInputData {
    /** A list of new input messages comprising the conversation so far. */
    @minItems(1)
    messages: InputChatMLMessage[];

    /** (Advanced) List of tools that are provided in addition to agent's default set of tools. */
    tools: Tool[] = #[];

    /** Can be one of existing tools given to the agent earlier or the ones provided in this request. */
    tool_choice?: ToolChoiceOption;
}

model ChatInput extends ChatInputData {
    ...MemoryAccessOptions;
    ...ChatSettings;
}

model BaseTokenLogProb {
    token: string;

    /** The log probability of the token */
    logprob: float32;

    bytes?: uint16[];
}

model TokenLogProb extends BaseTokenLogProb {
    /** The log probabilities of the tokens */
    @visibility("read")
    @minItems(1)
    top_logprobs: BaseTokenLogProb[];
}

model LogProbResponse {
    /** The log probabilities of the tokens */
    content: TokenLogProb[] | null;
}

model BaseChatOutput {
    index: uint32;

    /** The reason the model stopped generating tokens */
    finish_reason: FinishReason;

    /** The log probabilities of tokens */
    logprobs?: LogProbResponse;
}

/** The output returned by the model. Note that, depending on the model provider, they might return more than one message. */
model SingleChatOutput extends BaseChatOutput {
    message: InputChatMLMessage;
}

/** The output returned by the model. Note that, depending on the model provider, they might return more than one message. */
model MultipleChatOutput extends BaseChatOutput {
    @visibility("read")
    @minItems(1)
    messages: InputChatMLMessage[];
}

alias ChatOutput = SingleChatOutput | MultipleChatOutput;

/** Streaming chat completion output */
model ChatOutputChunk extends BaseChatOutput {
    /** The message generated by the model */
    delta: InputChatMLMessage;
}

model BaseChatResponse {
    /** Usage statistics for the completion request */
    usage?: CompetionUsage;

    /** Background job IDs that may have been spawned from this interaction. */
    @visibility("read")
    jobs: uuid[] = #[];

    /** Documents referenced for this request (for citation purposes). */
    @visibility("read")
    docs: DocReference[] = #[];

    ...HasCreatedAt;
    ...HasId;
}

model ChunkChatResponse extends BaseChatResponse {
    @header contentType: eventStream;

    /** The deltas generated by the model */
    choices: ChatOutputChunk[];
}

model MessageChatResponse extends BaseChatResponse {
    @header contentType: json;

    /** The deltas generated by the model */
    choices: ChatOutput[];
}

alias ChatResponse = ChunkChatResponse | MessageChatResponse;
