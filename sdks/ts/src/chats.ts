import { Chat_CompletionResponseFormat, Chat_GenerationPreset, Common_identifierSafeUnicode, Common_logit_bias, Common_uuid, Entries_InputChatMLMessage, Tools_FunctionTool, Tools_NamedToolChoice } from "./api";
import { BaseRoutes } from "./baseRoutes"

export class ChatsRoutes extends BaseRoutes {
    async generate({
        id,
        requestBody,
    }: {
        id: Common_uuid;
        requestBody:
        | {
            messages: Array<Entries_InputChatMLMessage>;
            tools?: Array<Tools_FunctionTool>;
            tool_choice?: "auto" | "none" | Tools_NamedToolChoice;
            readonly recall: boolean;
            readonly remember: boolean;
            save: boolean;
            model?: Common_identifierSafeUnicode;
            stream: boolean;
            stop?: Array<string>;
            seed?: number;
            max_tokens?: number;
            logit_bias?: Record<string, Common_logit_bias>;
            response_format?: Chat_CompletionResponseFormat;
            agent?: Common_uuid;
            preset?: Chat_GenerationPreset;
        }
        | {
            messages: Array<Entries_InputChatMLMessage>;
            tools?: Array<Tools_FunctionTool>;
            tool_choice?: "auto" | "none" | Tools_NamedToolChoice;
            readonly recall: boolean;
            readonly remember: boolean;
            save: boolean;
            model?: Common_identifierSafeUnicode;
            stream: boolean;
            stop?: Array<string>;
            seed?: number;
            max_tokens?: number;
            logit_bias?: Record<string, Common_logit_bias>;
            response_format?: Chat_CompletionResponseFormat;
            agent?: Common_uuid;
            frequency_penalty?: number;
            presence_penalty?: number;
            temperature?: number;
            top_p?: number;
        }
        | {
            messages: Array<Entries_InputChatMLMessage>;
            tools?: Array<Tools_FunctionTool>;
            tool_choice?: "auto" | "none" | Tools_NamedToolChoice;
            readonly recall: boolean;
            readonly remember: boolean;
            save: boolean;
            model?: Common_identifierSafeUnicode;
            stream: boolean;
            stop?: Array<string>;
            seed?: number;
            max_tokens?: number;
            logit_bias?: Record<string, Common_logit_bias>;
            response_format?: Chat_CompletionResponseFormat;
            agent?: Common_uuid;
            repetition_penalty?: number;
            length_penalty?: number;
            temperature?: number;
            top_p?: number;
            min_p?: number;
        };
    }) {
        return await this.apiClient.default.chatRouteGenerate({ id, requestBody })
    }
}