import "../common";
import "../agents";
import "./models.tsp";

using Common;
using Agents;

namespace Tools;

//
// TOOL ENDPOINTS
//

interface AgentEndpoints
    extends ChildLimitOffsetPagination<Tool, "List tools of the given agent">,
        ChildCreateEndpoint<CreateAgentRequest, "Create a new tool for this agent">,
        ChildUpdateEndpoint<UpdateToolRequest, "Update an existing tool (overwrite existing values)">,
        ChildPatchEndpoint<PatchToolRequest, "Update an existing tool (merges with existing values)">,
        ChildDeleteEndpoint<"Delete an existing tool by id"> {}
