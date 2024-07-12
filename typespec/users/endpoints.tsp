import "../common";
import "./models.tsp";

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