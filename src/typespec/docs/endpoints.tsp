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
    extends ChildDeleteEndpoint<"Delete a Doc for this User">,
        ChildCreateEndpoint<CreateDocRequest, Doc, "Create a Doc for this User"> {
    @get
    @doc("List Docs owned by a User")
    list(
        @path
        @doc("ID of parent")
        id: uuid,

        ...PaginationOptions,
        
        @query
        @doc("Whether to include embeddings in the response")
        include_embeddings?: boolean = true,
    ): {
        items: Doc[];
    };
}

interface AgentEndpoints
    extends ChildDeleteEndpoint<"Delete a Doc for this Agent">,
        ChildCreateEndpoint<CreateDocRequest, Doc, "Create a Doc for this Agent"> {
    @get
    @doc("List Docs owned by an Agent")
    list(
        @path
        @doc("ID of parent")
        id: uuid,

        ...PaginationOptions,
        
        @query
        @doc("Whether to include embeddings in the response")
        include_embeddings?: boolean = true,
    ): {
        items: Doc[];
    };
}

interface IndividualDocEndpoints {
    @get
    @doc("Get Doc by id")
    get(
        @path
        @doc("ID of the resource")
        id: uuid,
        
        @query
        @doc("Whether to include embeddings in the response")
        include_embeddings?: boolean = true,
    ): Doc;
}

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
