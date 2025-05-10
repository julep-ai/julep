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
