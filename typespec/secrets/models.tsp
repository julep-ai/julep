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

@withVisibility(Lifecycle.Create, Lifecycle.Update)
model UpdateSecretRequest {
    ...Secret;
}

@withVisibility(Lifecycle.Create)
model CreateSecretRequest {
    ...UpdateSecretRequest;
}


model PatchSecretRequest is UpdateSecretRequest {}
