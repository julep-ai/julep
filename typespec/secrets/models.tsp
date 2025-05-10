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
