import "@typespec/http";
import "@typespec/openapi";

import "../agents";
import "../common";
import "../users";
import "./models.tsp";

using TypeSpec.Http;
using TypeSpec.OpenAPI;

using Agents;
using Common;
using Users;

namespace Docs;

//
// DOCS ENDPOINTS
//

interface UserEndpoints
    extends ChildLimitOffsetPagination<Doc, "Doc", User, "User"> {}

interface AgentEndpoints
    extends ChildLimitOffsetPagination<Doc, "Doc", Agent, "Agent"> {}

interface IndividualDocEndpoints
    extends GetEndpoint<Doc, "Doc">,
        DeleteEndpoint<Doc, "Doc"> {}
