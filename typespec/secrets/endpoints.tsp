import "@typespec/rest";
import "@typespec/openapi";
import "@typespec/versioning";
import "@typespec/http";
import "./models.tsp";
import "../versions.tsp";
import "../common";

using TypeSpec.Http;
using TypeSpec.Rest;
using TypeSpec.Versioning;
using TypeSpec.OpenAPI;
using Versions;
using Common;

@versioned(ApiVersions)
namespace Julep.Secrets;

@route("/secrets")
interface Secrets {
  /** Create a new secret */
  @post
  @summary("Create a new secret")
  @doc("""
    Creates a new secret that can be used in tasks and sessions.
    The secret value will be encrypted at rest.
  """)
  create(
    @body secret: SecretCreate
  ): Secret | DuplicateSecretError;

  /** List all secrets */
  @get
  @summary("List all secrets")
  @doc("""
    Lists all secrets for the current developer.
    Secrets are returned without their values.
  """)
  list(
    @query
    @doc("Maximum number of secrets to return")
    limit?: int32 = 100;

    @query
    @doc("Number of secrets to skip")
    offset?: int32 = 0;

    @query
    @doc("Filter secrets by name prefix")
    name_prefix?: string;
  ): Secret[];

  /** Get a secret */
  @get
  @summary("Get a secret")
  @doc("""
    Gets a secret by ID.
    The secret value is not returned.
  """)
  @route("{secret_id}")
  get(
    @path
    @doc("ID of the secret to get")
    secret_id: uuid
  ): Secret | SecretNotFoundError;

  /** Get a secret's value */
  @get
  @summary("Get a secret's value")
  @doc("""
    Gets a secret's decrypted value.
    This endpoint requires special permissions.
  """)
  @route("{secret_id}/value")
  getValue(
    @path
    @doc("ID of the secret to get")
    secret_id: uuid
  ): SecretValue | SecretNotFoundError;

  /** Update a secret */
  @put
  @summary("Update a secret")
  @doc("""
    Updates a secret's metadata.
    The secret value cannot be updated.
  """)
  @route("{secret_id}")
  update(
    @path
    @doc("ID of the secret to update")
    secret_id: uuid,

    @body secret: SecretUpdate
  ): Secret | SecretNotFoundError;

  /** Delete a secret */
  @delete
  @summary("Delete a secret")
  @doc("""
    Deletes a secret.
    This operation cannot be undone.
  """)
  @route("{secret_id}")
  delete(
    @path
    @doc("ID of the secret to delete")
    secret_id: uuid
  ): Secret | SecretNotFoundError;
} 