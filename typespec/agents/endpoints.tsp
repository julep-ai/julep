import "@typespec/http";
import "@typespec/openapi";

import "../common";
import "./models.tsp";

using TypeSpec.Http;
using TypeSpec.OpenAPI;

using Common;

namespace Agents;

//
// AGENT ENDPOINTS
//

interface Endpoints
    extends LimitOffsetPagination<Agent, "Agent">,
        CreateEndpoint<Agent, "Agent", CreateAgentRequest>,
        CreateOrUpdateEndpoint<Agent, "Agent", CreateOrUpdateAgentRequest>,
        UpdateEndpoint<Agent, "Agent", UpdateAgentRequest>,
        PatchEndpoint<Agent, "Agent", PatchAgentRequest>,
        DeleteEndpoint<Agent, "Agent">,
        GetEndpoint<Agent, "Agent"> {}