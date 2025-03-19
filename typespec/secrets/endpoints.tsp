import "./models.tsp";
import "../common";

using TypeSpec.Http;
using TypeSpec.OpenAPI;
using TypeSpec.Versioning;
using Common;
using Secrets;

namespace Secrets;

@route("/developers/{id}/secrets")
@tag("Secrets")
interface DeveloperSecretsRoute {
    @summary("Create a Secret")
    @doc("Create a new Secret for a Developer")
    @post
    createSecret(@path id: uuid, @body secret: CreateSecretRequest): Secret;

    @summary("List Secrets")
    @doc("List all Secrets for a Developer")
    @get
    listSecrets(@path id: uuid): ListResponse<SecretsSummary>;
}

@route("/developers/{developer_id}/secrets/{id}")
@tag("Secrets")
interface DeveloperSecretRoute {
    @summary("Get Secret details")
    @doc("Get Secret details (without the encrypted value)")
    @get
    getSecretDetails(@path developer_id: uuid, @path id: uuid): SecretsSummary;

    @summary("Update Secret")
    @doc("Update an existing Secret")
    @put
    updateSecret(@path developer_id: uuid, @path id: uuid, @body secret: UpdateSecretRequest): Secret;

    @summary("Patch Secret")
    @doc("Patch an existing Secret")
    @patch
    patchSecret(@path developer_id: uuid, @path id: uuid, @body secret: PatchSecretRequest): Secret;

    @summary("Delete Secret")
    @doc("Delete a Secret")
    @delete
    deleteSecret(@path developer_id: uuid, @path id: uuid): ResourceDeletedResponse;
}

@route("/agents/{id}/secrets")
@tag("Secrets")
interface AgentSecretsRoute {
    @summary("Create an Agent Secret")
    @doc("Create a new Secret for a specific Agent")
    @post
    createAgentSecret(@path id: uuid, @body secret: CreateSecretRequest): Secret;

    @summary("List Agent Secrets")
    @doc("List all Secrets for a specific Agent")
    @get
    listAgentSecrets(@path id: uuid): ListResponse<SecretsSummary>;
}

@route("/agents/{agent_id}/secrets/{id}")
@tag("Secrets")
interface AgentSecretRoute {
    @summary("Get Agent Secret details")
    @doc("Get Agent Secret details (without the encrypted value)")
    @get
    getAgentSecretDetails(@path agent_id: uuid, @path id: uuid): SecretsSummary;

    @summary("Update Agent Secret")
    @doc("Update an existing Agent Secret")
    @put
    updateAgentSecret(@path agent_id: uuid, @path id: uuid, @body secret: UpdateSecretRequest): Secret;

    @summary("Patch Agent Secret")
    @doc("Patch an existing Agent Secret")
    @patch
    patchAgentSecret(@path agent_id: uuid, @path id: uuid, @body secret: PatchSecretRequest): Secret;

    @summary("Delete Agent Secret")
    @doc("Delete an Agent Secret")
    @delete
    deleteAgentSecret(@path agent_id: uuid, @path id: uuid): ResourceDeletedResponse;
}