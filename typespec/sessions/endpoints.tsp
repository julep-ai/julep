import "@typespec/http";
import "@typespec/openapi";
import "../common";
import "./models.tsp";

using TypeSpec.Http;
using TypeSpec.OpenAPI;

using Common;

namespace Sessions;

//
// SESSION ENDPOINTS
//

interface Endpoints
    extends LimitOffsetPagination<Session, "Session">,
        CreateEndpoint<Session, "Session", CreateSessionRequest>,
        CreateOrUpdateEndpoint<Session, "Session", CreateOrUpdateSessionRequest>,
        UpdateEndpoint<Session, "Session", UpdateSessionRequest>,
        PatchEndpoint<Session, "Session", PatchSessionRequest>,
        DeleteEndpoint<Session, "Session">,
        GetEndpoint<Session, "Session"> {}