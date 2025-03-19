import "./models.tsp";
import "../common";

using Common;
using Secrets;

namespace Secrets;

@route("/developers/{id}/secrets")
@tag("Secrets")
interface DeveloperSecretsRoute {
    @summary("Create a Secret")
    @doc("Create a new Secret for a Developer")
    createSecret is StandardCreate<CreateSecretRequest, Secret>;

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
    getSecretDetails is StandardGet<SecretsSummary>;

    @summary("Update Secret")
    @doc("Update an existing Secret")
    updateSecret is StandardUpdate<UpdateSecretRequest, Secret>;

    @summary("Patch Secret")
    @doc("Patch an existing Secret")
    patchSecret is StandardPatch<PatchSecretRequest, Secret>;

    @summary("Delete Secret")
    @doc("Delete a Secret")
    deleteSecret is StandardDelete;
}

@route("/agents/{id}/secrets")
@tag("Secrets")
interface AgentSecretsRoute {
    @summary("Create an Agent Secret")
    @doc("Create a new Secret for a specific Agent")
    createAgentSecret is StandardCreate<CreateSecretRequest, Secret>;

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
    getAgentSecretDetails is StandardGet<SecretsSummary>;

    @summary("Update Agent Secret")
    @doc("Update an existing Agent Secret")
    updateAgentSecret is StandardUpdate<UpdateSecretRequest, Secret>;

    @summary("Patch Agent Secret")
    @doc("Patch an existing Agent Secret")
    patchAgentSecret is StandardPatch<PatchSecretRequest, Secret>;

    @summary("Delete Agent Secret")
    @doc("Delete an Agent Secret")
    deleteAgentSecret is StandardDelete;
}