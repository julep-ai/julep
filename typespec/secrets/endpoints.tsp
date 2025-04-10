import "@typespec/http";

import "./models.tsp";
import "../common";

using TypeSpec.Http;

using Common;

namespace Secrets;

//
// SECRET ENDPOINTS
//

interface DeveloperSecretsEndpoints
    extends ChildLimitOffsetPagination<Secret, "List secrets (paginated)">,
        ChildCreateEndpoint<CreateSecretRequest, Secret, "Create a new secret">,
        ChildUpdateEndpoint<UpdateSecretRequest, Secret, "Update an existing secret by id (overwrites existing values)">,
        ChildDeleteEndpoint<"Delete a secret by id"> {}

interface AgentSecretsEndpoints
    extends ChildLimitOffsetPagination<Secret, "List secrets (paginated)">,
        ChildCreateEndpoint<CreateSecretRequest, Secret, "Create a new secret">,
        ChildUpdateEndpoint<UpdateSecretRequest, Secret, "Update an existing secret by id (overwrites existing values)">,
        ChildDeleteEndpoint<"Delete a secret by id"> {}

interface GetSecretEndpoints {
    @post
    @doc("Get a secret by name")
    secret(
        @path
        @doc("The owner ID")
        id: uuid;

        @bodyRoot
        @doc("Request to get a secret")
        body: GetSecretRequest;
    ): {
        @statusCode _: "200";

        @bodyRoot
        @doc("Response from the model")
        body: GetSecretResponse;
    };
}