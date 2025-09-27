import "@typespec/http";
import "../common";
import "./models.tsp";

using TypeSpec.Http;
using Common;

namespace Agents;

//
// AGENT ENDPOINTS
//

interface Endpoints
    extends LimitOffsetPagination<Agent, "List Agents (paginated)">,
        CreateEndpoint<CreateAgentRequest, Agent, "Create a new Agent">,
        CreateOrUpdateEndpoint<CreateOrUpdateAgentRequest, Agent, "Create or update an Agent">,
        UpdateEndpoint<UpdateAgentRequest, Agent, "Update an existing Agent by id (overwrites existing values; use PATCH for merging instead)">,
        PatchEndpoint<PatchAgentRequest, Agent, "Update an existing Agent by id (merges with existing values)">,
        DeleteEndpoint<"Delete Agent by id">,
        GetEndpoint<Agent, "Get an Agent by id"> {
    
    @route("models")
    @get
    @doc("List all available models")
    listModels(): ListModelsResponse;
}
