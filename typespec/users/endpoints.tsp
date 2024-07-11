import "@typespec/http";
import "@typespec/openapi";

import "../common";
import "./models.tsp";

using TypeSpec.Http;
using TypeSpec.OpenAPI;

using Common;

namespace Users;

//
// USER ENDPOINTS
//

interface Endpoints
    extends LimitOffsetPagination<User, "User">,
        CreateEndpoint<User, "User", CreateUserRequest>,
        CreateOrUpdateEndpoint<User, "User", CreateOrUpdateUserRequest>,
        UpdateEndpoint<User, "User", UpdateUserRequest>,
        PatchEndpoint<User, "User", PatchUserRequest>,
        DeleteEndpoint<User, "User">,
        GetEndpoint<User, "User"> {}