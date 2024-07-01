import typia, { tags } from "typia";

import { isUndefined, omitBy } from "lodash";
import {
  ChatInput,
  ChatMLMessage,
  ChatResponse,
  ResourceCreatedResponse,
  ResourceUpdatedResponse,
  Session,
  Suggestion,
} from "../api";
import { BaseManager } from "./base";

export interface CreateSessionPayload {
  userId?: string;
  agentId: string;
  situation?: string;
  metadata?: Record<string, any>;
  renderTemplates?: boolean;
  tokenBudget?: number;

  // Can only be one of the following values: "truncate", "adaptive"
  contextOverflow?: "truncate" | "adaptive";
}

export class SessionsManager extends BaseManager {
  /**
   * Retrieves a session by its ID.
   * @param sessionId The unique identifier of the session.
   * @returns A promise that resolves with the session object.
   */
  async get(sessionId: string & tags.Format<"uuid">): Promise<Session> {
    typia.assertGuard<string & tags.Format<"uuid">>(sessionId);

    return this.apiClient.default.getSession({ sessionId });
  }

  async create(
    payload: CreateSessionPayload,
  ): Promise<ResourceCreatedResponse> {
    const {
      userId,
      agentId,
      situation,
      tokenBudget,
      contextOverflow,
      metadata = {},
      renderTemplates = false,
    }: CreateSessionPayload = typia.assert<CreateSessionPayload>(payload);

    const requestBody = {
      user_id: userId,
      agent_id: agentId,
      situation,
      metadata,
      render_templates: renderTemplates,
      token_budget: tokenBudget,
      context_overflow: contextOverflow,
    };

    type rkey = keyof typeof requestBody;

    for (const key of Object.keys(requestBody)) {
      if (requestBody[key as rkey] === undefined) {
        delete requestBody[key as rkey];
      }
    }

    return this.apiClient.default
      .createSession({ requestBody })
      .catch((error) => Promise.reject(error));
  }

  async list(
    options: {
      limit?: number &
        tags.Type<"uint32"> &
        tags.Minimum<1> &
        tags.Maximum<1000>;
      offset?: number & tags.Minimum<1> & tags.Maximum<1000>;
      metadataFilter?: { [key: string]: any };
    } = {},
  ): Promise<Array<Session>> {
    const {
      limit = 100,
      offset = 0,
      metadataFilter = {},
    } = typia.assert<{
      limit?: number &
        tags.Type<"uint32"> &
        tags.Minimum<1> &
        tags.Maximum<1000>;
      offset?: number & tags.Minimum<1> & tags.Maximum<1000>;
      metadataFilter?: { [key: string]: any };
    }>(options);

    const metadataFilterString: string = JSON.stringify(metadataFilter);

    const result = await this.apiClient.default.listSessions({
      limit,
      offset,
      metadataFilter: metadataFilterString,
    });

    return result.items || [];
  }

  async delete(sessionId: string & tags.Format<"uuid">): Promise<void> {
    typia.assertGuard<string & tags.Format<"uuid">>(sessionId);

    await this.apiClient.default.deleteSession({ sessionId });
  }

  async update(
    sessionId: string & tags.Format<"uuid">,
    options: {
      situation: string;
      tokenBudget?: number & tags.Minimum<1>;
      contextOverflow?: "truncate" | "adaptive";
      metadata?: Record<string, any>;
    },
    overwrite = false,
  ): Promise<ResourceUpdatedResponse> {
    typia.assertGuard<string & tags.Format<"uuid">>(sessionId);

    const {
      situation,
      tokenBudget,
      contextOverflow,
      metadata = {},
    } = typia.assert<{
      situation: string;
      tokenBudget?: number & tags.Minimum<1>;
      contextOverflow?: "truncate" | "adaptive";
      metadata?: Record<string, any>;
    }>(options);

    const requestBody = {
      situation,
      metadata,
      token_budget: tokenBudget,
      context_overflow: contextOverflow,
    };

    type rkey = keyof typeof requestBody;

    for (const key of Object.keys(requestBody)) {
      if (requestBody[key as rkey] === undefined) {
        delete requestBody[key as rkey];
      }
    }

    if (overwrite) {
      return this.apiClient.default.updateSession({ sessionId, requestBody });
    } else {
      return this.apiClient.default.patchSession({ sessionId, requestBody });
    }
  }

  async chat(
    sessionId: string & tags.Format<"uuid">,
    input: ChatInput,
  ): Promise<ChatResponse> {
    typia.assertGuard<string & tags.Format<"uuid">>(sessionId);

    const {
      messages,
      frequency_penalty,
      length_penalty,
      logit_bias,
      max_tokens,
      presence_penalty,
      recall,
      remember,
      repetition_penalty,
      response_format,
      seed,
      stop,
      stream,
      temperature,
      tool_choice,
      tools,
      top_p,
    } = typia.assert<ChatInput>(input);

    const options = omitBy(
      {
        tools,
        tool_choice,
        frequency_penalty,
        length_penalty,
        logit_bias,
        max_tokens,
        presence_penalty,
        repetition_penalty,
        response_format,
        seed,
        stop,
        stream,
        temperature,
        top_p,
        recall,
        remember,
      },
      isUndefined,
    );

    const requestBody = {
      messages,
      ...options,
    };

    return await this.apiClient.default.chat({ sessionId, requestBody });
  }

  async suggestions(
    sessionId: string & tags.Format<"uuid">,
    options: {
      limit?: number & tags.Minimum<1> & tags.Maximum<1000>;
      offset?: number & tags.Minimum<0>;
    } = {},
  ): Promise<Array<Suggestion>> {
    typia.assertGuard<string & tags.Format<"uuid">>(sessionId);

    const { limit = 100, offset = 0 } = typia.assert<{
      limit?: number & tags.Minimum<1> & tags.Maximum<1000>;
      offset?: number & tags.Minimum<0>;
    }>(options);

    const result = await this.apiClient.default.getSuggestions({
      sessionId,
      limit,
      offset,
    });

    return result.items || [];
  }

  async history(
    sessionId: string & tags.Format<"uuid">,
    options: {
      limit?: number & tags.Minimum<1> & tags.Maximum<1000>;
      offset?: number & tags.Minimum<0>;
    } = {},
  ): Promise<Array<ChatMLMessage>> {
    typia.assertGuard<string & tags.Format<"uuid">>(sessionId);

    const { limit = 100, offset = 0 } = typia.assert<{
      limit?: number & tags.Minimum<1> & tags.Maximum<1000>;
      offset?: number & tags.Minimum<0>;
    }>(options);

    const result = await this.apiClient.default.getHistory({
      sessionId,
      limit,
      offset,
    });

    return result.items || [];
  }

  async deleteHistory(sessionId: string & tags.Format<"uuid">): Promise<void> {
    typia.assertGuard<string & tags.Format<"uuid">>(sessionId);

    await this.apiClient.default.deleteSessionHistory({ sessionId });
  }
}
