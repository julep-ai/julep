import "../common";
import "../agents";
import "./models.tsp";

using Common;
using Agents;

namespace Tools;

//
// TOOL ENDPOINTS
//

interface Endpoints
    extends UpdateEndpoint<UpdateToolRequest, "Update an existing tool (overwrite existing values)">,
        PatchEndpoint<PatchToolRequest, "Update an existing tool (merges with existing values)">,
        DeleteEndpoint<"Delete an existing tool by id"> {}

interface AgentEndpoints
    extends ChildLimitOffsetPagination<Tool, "List tools of the given agent">,
        ChildCreateEndpoint<CreateAgentRequest, "Create a new tool for this agent"> {}
