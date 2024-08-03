import "../common";
import "./models.tsp";

using Common;

namespace Sessions;

//
// SESSION ENDPOINTS
//

interface Endpoints
    extends LimitOffsetPagination<Session, "List sessions (paginated)">,
        CreateEndpoint<CreateSessionRequest, "Create a new session">,
        CreateOrUpdateEndpoint<CreateOrUpdateSessionRequest, "Create or update a session">,
        UpdateEndpoint<UpdateSessionRequest, "Update an existing session by its id (overwrites all existing values)">,
        PatchEndpoint<PatchSessionRequest, "Update an existing session by its id (merges with existing values)">,
        DeleteEndpoint<"Delete a session by its id">,
        GetEndpoint<Session, "Get a session by id"> {}