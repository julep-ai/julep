/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AgentDefaultSettings } from "./AgentDefaultSettings";
export type Agent = {
  /**
   * Name of the agent
   */
  name: string;
  /**
   * About the agent
   */
  about?: string;
  /**
   * Agent created at (RFC-3339 format)
   */
  created_at?: string;
  /**
   * Agent updated at (RFC-3339 format)
   */
  updated_at?: string;
  /**
   * Agent id (UUID)
   */
  id: string;
  /**
   * Default settings for all sessions created by this agent
   */
  default_settings?: AgentDefaultSettings;
  /**
   * The model to use with this agent
   */
  model: string;
  /**
   * Optional metadata
   */
  metadata?: Record<string, any>;
  /**
   * Instructions for the agent
   */
  instructions?: string | Array<string>;
};
