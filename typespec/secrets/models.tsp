import "../common";

using Common;

namespace Secrets;

//
// SECRET MODELS
//

/** A secret that can be used in tasks and sessions */
model Secret {
  ...HasId;
  ...HasTimestamps;
  ...HasMetadata;

  /** ID of the developer who owns this secret */
  developer_id?: uuid;

  /** ID of the agent this secret is associated with (optional) */
  agent_id?: uuid;

  /** Name of the secret */
  name: string;

  /** Description of what the secret is used for */
  description?: string;

  /** The decrypted secret value */
  value: string;
}

@withVisibility("create", "update")
model UpdateSecretRequest {
    ...Secret;
}

@withVisibility("create")
model CreateSecretRequest {
    ...UpdateSecretRequest;
}

model PatchSecretRequest is UpdateSecretRequest {}

model GetSecretRequest {
    name: string;
}

model GetSecretResponse {
    ...Secret;
}
