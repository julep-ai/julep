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
    extends ChildLimitOffsetPagination<Doc, "List Docs owned by a User">,
        ChildCreateEndpoint<CreateDocRequest, "Create a Doc for this User"> {}

interface AgentEndpoints
    extends ChildLimitOffsetPagination<Doc, "List Docs owned by an Agent">,
        ChildCreateEndpoint<CreateDocRequest, "Create a Doc for this Agent"> {}

interface IndividualDocEndpoints
    extends GetEndpoint<Doc, "Get Doc by id">,
        DeleteEndpoint<"Delete an existing Doc by id"> {}

interface SearchEndpoints<DocString extends valueof string = "Search for documents"> {
    @doc(DocString)
    @post
    search(
        @path
        @doc("ID of the parent")
        id: uuid,

        body: DocSearchRequest,
    ): DocSearchResponse;
}

interface EmbedEndpoints {
    @doc("Embed a query for search")
    @post
    embed(body: EmbedQueryRequest): EmbedQueryResponse;
}
