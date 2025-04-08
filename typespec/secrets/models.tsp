import "@typespec/rest";
import "@typespec/openapi";
import "@typespec/versioning";
import "@typespec/http";
import "../common";
import "../versions.tsp";

using TypeSpec.Http;
using TypeSpec.Rest;
using TypeSpec.Versioning;
using Common;
using Versions;

namespace Secrets;

//
// SECRET MODELS
//

/** A secret that can be used in tasks and sessions */
model Secret {
  /** Unique identifier for the secret */
  @key
  secret_id: uuid;

  /** ID of the developer who owns this secret */
  developer_id: uuid;

  /** Name of the secret */
  name: string;

  /** Description of what the secret is used for */
  description?: string;

  /** The decrypted secret value */
  value: string;

  ...HasTimestamps;
  ...HasMetadata;
}

/** Input for creating a new secret */
model SecretCreate {
  /** Name of the secret */
  name: string;

  /** Description of what the secret is used for */
  description?: string;

  /** The secret value to store */
  value: string;

  /** Additional metadata about the secret */
  metadata?: Record<string>;
}

/** Input for updating a secret */
model SecretUpdate {
  /** New name for the secret */
  name?: string;

  /** New description for the secret */
  description?: string;

  /** The secret value to store */
  value: string;

  /** New metadata for the secret */
  metadata?: Record<string>;
}
