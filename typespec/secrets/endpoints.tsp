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

namespace Secrets;

//
// SECRET ENDPOINTS
//

interface Endpoints
    extends LimitOffsetPagination<Secret, "List secrets (paginated)">,
        CreateEndpoint<SecretCreate, Secret, "Create a new secret">,
        UpdateEndpoint<SecretUpdate, Secret, "Update an existing secret by id (overwrites existing values)">,
        DeleteEndpoint<"Delete a secret by id">,
        GetEndpoint<Secret, "Get a secret by id"> {}
