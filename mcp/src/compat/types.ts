export interface ClientCapabilities {
  topLevelUnions: boolean;
  validJson: boolean;
  refs: boolean;
  unions: boolean;
  formats: boolean;
  toolNameLength: number | undefined;
  supportsStreaming: boolean;
  requiresOAuth: boolean;
}