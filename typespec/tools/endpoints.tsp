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
    extends UpdateEndpoint<Tool, "Tool", UpdateToolRequest>,
        PatchEndpoint<Tool, "Tool", PatchToolRequest>,
        DeleteEndpoint<Tool, "Tool"> {}

interface AgentEndpoints
    extends ChildLimitOffsetPagination<Tool, "Tool", Agent, "Agent">,
        ChildCreateEndpoint<Tool, "Tool", Agent, "Agent", CreateAgentRequest> {}
