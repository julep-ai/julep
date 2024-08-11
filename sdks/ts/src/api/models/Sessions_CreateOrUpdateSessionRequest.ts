/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
import type { Sessions_ContextOverflowType } from "./Sessions_ContextOverflowType";
import type { Sessions_CreateSessionRequest } from "./Sessions_CreateSessionRequest";
export type Sessions_CreateOrUpdateSessionRequest =
  Sessions_CreateSessionRequest & {
    id: Common_uuid;
    /**
     * User ID of user associated with this session
     */
    user?: Common_uuid;
    users?: Array<Common_uuid>;
    /**
     * Agent ID of agent associated with this session
     */
    agent?: Common_uuid;
    agents?: Array<Common_uuid>;
    /**
     * A specific situation that sets the background for this session
     */
    situation: string;
    /**
     * Render system and assistant message content as jinja templates
     */
    render_templates: boolean;
    /**
     * Threshold value for the adaptive context functionality
     */
    token_budget: number | null;
    /**
     * Action to start on context window overflow
     */
    context_overflow: Sessions_ContextOverflowType | null;
    metadata?: Record<string, any>;
  };
