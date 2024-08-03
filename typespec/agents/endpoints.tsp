import "../common";
import "./models.tsp";

using Common;

namespace Agents;

//
// AGENT ENDPOINTS
//

interface Endpoints
    extends LimitOffsetPagination<Agent, "List Agents (paginated)">,
        CreateEndpoint<CreateAgentRequest, "Create a new Agent">,
        CreateOrUpdateEndpoint<CreateOrUpdateAgentRequest, "Create or update an Agent">,
        UpdateEndpoint<UpdateAgentRequest, "Update an existing Agent by id (overwrites existing values; use PATCH for merging instead)">,
        PatchEndpoint<PatchAgentRequest, "Update an existing Agent by id (merges with existing values)">,
        DeleteEndpoint<"Delete Agent by id">,
        GetEndpoint<Agent, "Get an Agent by id"> {}