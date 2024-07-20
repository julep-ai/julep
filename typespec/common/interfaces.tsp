import "@typespec/http";

import "./scalars.tsp";
import "./types.tsp";

using TypeSpec.Http;

namespace Common;

//
// COMMON INTERFACES
//

interface LimitOffsetPagination<
    Type,
    DocString extends valueof string = "List resources (paginated)"
> {
    @get
    @doc(DocString)
    list(...PaginationOptions): {
        results: Type[];
    };
}

interface CreateEndpoint<
    CreateType,
    DocString extends valueof string = "Create a new resource"
> {
    @post
    @doc(DocString)
    create(@header contentType: yaml | json, ...CreateType): {
        @statusCode _: "201";

        @body
        @doc("Details of the resource created along with ID")
        body: ResourceCreatedResponse;
    };
}

interface CreateOrUpdateEndpoint<
    CreateOrUpdateType,
    DocString extends valueof string = "Create or update a resource (ID is required in payload; existing resource will be overwritten)"
> {
    @put
    @doc(DocString)
    createOrUpdate(@header contentType: yaml | json, ...CreateOrUpdateType): {
        @statusCode _: "200";

        @body
        @doc("Details of the resource updated along with ID")
        body: ResourceUpdatedResponse;
    };
}

interface UpdateEndpoint<
    UpdateType,
    DocString extends valueof string = "Update resource by id (overwrite existing values)"
> {
    @put
    @doc(DocString)
    update(
        @header contentType: yaml | json,

        @path
        @doc("ID of the resource")
        id: uuid,

        ...UpdateType,
    ): {
        @statusCode _: "200";

        @body
        @doc("Details of the resource updated along with ID")
        body: ResourceUpdatedResponse;
    };
}

interface PatchEndpoint<
    PatchType,
    DocString extends valueof string = "Patch resource by its id (merge changes with existing values)"
> {
    @patch
    @doc(DocString)
    patch(
        @header contentType: yaml | json,

        @path
        @doc("ID of the resource")
        id: uuid,

        ...PatchType,
    ): {
        @statusCode _: "200";

        @body
        @doc("Details of the resource patched along with ID")
        body: ResourceUpdatedResponse;
    };
}

interface GetEndpoint<
    Type,
    DocString extends valueof string = "Get resource by id"
> {
    @get
    @doc(DocString)
    get(
        @path
        @doc("ID of the resource")
        id: uuid,
    ): Type;
}

interface DeleteEndpoint<DocString extends valueof string = "Delete resource by id"> {
    @delete
    @doc(DocString)
    delete(
        @path
        @doc("ID of the resource")
        id: uuid,
    ): {
        @statusCode _: "202";

        @body
        @doc("Details of the resource deleted along with ID")
        body: ResourceDeletedResponse;
    };
}

interface ChildLimitOffsetPagination<
    T,
    DocString extends valueof string = "List items owned by the given parent"
> {
    @get
    @doc(DocString)
    list(
        @path
        @doc("ID of parent")
        id: uuid,

        ...PaginationOptions,
    ): {
        results: T[];
    };
}

interface ChildCreateEndpoint<
    CreateType,
    DocString extends valueof string = "Create a new resource owned by the given parent"
> {
    @post
    @doc(DocString)
    create(
        @header contentType: yaml | json,

        @path
        @doc("ID of parent resource")
        id: uuid,

        ...CreateType,
    ): {
        @statusCode _: "201";

        @body
        @doc("Details of the resource created along with ID")
        body: ResourceCreatedResponse;
    };
}

interface ChildDeleteEndpoint<
    DocString extends valueof string = "Delete a resource owned by the given parent using its id"
> {
    @post
    @doc(
        DocString
    )
    delete(
        @path
        @doc(
            "ID of parent resource",
        )
        parent_id: uuid,

        @path
        @doc(
            "ID of the resource to be deleted",
        )
        id: uuid,
    ): {
        @statusCode _: "202";

        @body
        @doc(
            "Details of the resource deleted along with ID",
        )
        body: ResourceDeletedResponse;
    };
}
