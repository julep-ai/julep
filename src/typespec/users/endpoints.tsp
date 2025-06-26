import "../common";
import "./models.tsp";

using Common;

namespace Users;

//
// USER ENDPOINTS
//

interface Endpoints
    extends LimitOffsetPagination<User, "List users (paginated)">,
        CreateEndpoint<CreateUserRequest, User, "Create a new user">,
        CreateOrUpdateEndpoint<CreateOrUpdateUserRequest, User, "Create or update a user">,
        UpdateEndpoint<UpdateUserRequest, User, "Update an existing user by id (overwrite existing values)">,
        PatchEndpoint<PatchUserRequest, User, "Update an existing user by id (merge with existing values)">,
        DeleteEndpoint<"Delete a user by id">,
        GetEndpoint<User, "Get a user by id"> {}