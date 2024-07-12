import "../agents";
import "../common";
import "../users";
import "./models.tsp";

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
