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
        ChildDeleteEndpoint<"Delete a Doc for this User">,
        ChildCreateEndpoint<CreateDocRequest, Doc, "Create a Doc for this User"> {}

interface AgentEndpoints
    extends ChildLimitOffsetPagination<Doc, "List Docs owned by an Agent">,
        ChildDeleteEndpoint<"Delete a Doc for this Agent">,
        ChildCreateEndpoint<CreateDocRequest, Doc, "Create a Doc for this Agent"> {}

interface IndividualDocEndpoints
    extends GetEndpoint<Doc, "Get Doc by id"> {}

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

interface BulkDeleteEndpoints<DocString extends valueof string = "Bulk delete documents"> {
    @doc(DocString)
    @delete
    deleteBulk(
        @path
        @doc("ID of the parent")
        id: uuid,

        ...BulkDeleteDocsRequest,
    ): {
        @statusCode _: "202";

        @body
        @doc("Details of the resource deleted along with ID")
        body: ResourceDeletedResponse[];
    };
}

interface EmbedEndpoints {
    @doc("Embed a query for search")
    @post
    embed(body: EmbedQueryRequest): EmbedQueryResponse;
}
