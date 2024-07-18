import "@typespec/http";

import "../agents";
import "../common";
import "../users";
import "./models.tsp";

using TypeSpec.Http;

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

interface SearchEndpoints<TName extends string> {
    @doc("Search for documents owned by {TName}", {TName: TName})
    @post
    search(
        @path
        @doc("ID of the {TName}", {TName: TName})
        id: User.id | Agent.id,

        ...PaginationOptions<"Doc">,
        body: DocSearchRequest,
    ): {
        results: DocReference[];
    };
}

interface EmbedEndpoints {
    @doc("Embed a query for search")
    @post
    embed(
        body: EmbedQueryRequest,
    ): EmbedQueryResponse;
}
