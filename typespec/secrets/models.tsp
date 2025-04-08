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

@versioned(ApiVersions)
namespace Julep.Secrets;

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

  /** New metadata for the secret */
  metadata?: Record<string>;
}

/** Response containing a secret's decrypted value */
model SecretValue {
  /** The decrypted secret value */
  value: string;
}

/** Error when a secret with the same name already exists */
@error
model DuplicateSecretError {
  @statusCode
  _: 409;

  /** Error code */
  code: "duplicate_secret";

  /** Error message */
  message: string;
}

/** Error when a secret is not found */
@error
model SecretNotFoundError {
  @statusCode
  _: 404;

  /** Error code */
  code: "secret_not_found";

  /** Error message */
  message: string;
} 