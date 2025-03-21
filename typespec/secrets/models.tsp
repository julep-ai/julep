import "../common";

using TypeSpec.Http;
using TypeSpec.OpenAPI;
using TypeSpec.Versioning;
using Common;

namespace Secrets;

/** Response containing a list of items */
model ListResponse<T> {
  /** The list of items */
  items: T[];
}

/** Response for a resource deletion */
model ResourceDeletedResponse {
  /** The ID of the deleted resource */
  id: string;
}

/** Secret model for encrypting and storing sensitive values */
model Secret {
    /** The secret's unique identifier */
    @visibility("read")
    id: uuid;

    /** The name of the secret (unique within developer and agent scope) */
    name: string;

    /** The encrypted value of the secret (never returned back in API responses) */
    @visibility("create", "update")
    value: string;

    /** Optional description of what the secret is used for */
    description?: string;

    /** Optional metadata for the secret */
    metadata?: Record<unknown>;
    
    /** The agent that can access this secret (if null, all developer's agents can access) */
    @visibility("create", "update")
    agent_id?: uuid;

    /** The developer that owns this secret */
    @visibility("read")
    developer_id?: uuid;

    ...HasTimestamps;
}

/** Payload for creating a secret */
@withVisibility("create")
model CreateSecretRequest {
    ...Secret;
}

/** Payload for updating a secret */
@withVisibility("update")
model UpdateSecretRequest {
    ...Secret;
}

/** Payload for patching a secret */
model PatchSecretRequest is UpdateSecretRequest {}

/** Response for listing secrets */
model SecretsSummary {
    /** The secret's unique identifier */
    id: uuid;

    /** The name of the secret */
    name: string;

    /** Optional description of what the secret is used for */
    description?: string;

    /** When the secret was created */
    created_at: utcDateTime;

    /** When the secret was last updated */
    updated_at: utcDateTime;

    /** The agent that can access this secret (if null, all developer's agents can access) */
    agent_id?: uuid;
}