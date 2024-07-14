import "@typespec/http";

import "./scalars.tsp";
import "./types.tsp";

using TypeSpec.Http;

namespace Common;

//
// COMMON INTERFACES
//

interface LimitOffsetPagination<T, TName extends string> {
    @get
    @doc("List {TName} items", {TName: TName})
    list(
        ...PaginationOptions<TName>
    ): {results: T[]};
}

interface CreateEndpoint<T, TName extends string, CreateT = T> {
    @post
    @doc("Create new {TName}", {TName: TName})
    create(
        @header contentType: yaml | json;

        ...CreateT
    ): {
        @statusCode _: "201";

        @body
        @doc("Details of {TName} resource created along with ID", {TName: TName})
        body: ResourceCreatedResponse<T, TName>;
    };
}

interface CreateOrUpdateEndpoint<T, TName extends string, CreateOrUpdateT = T> {
    @put
    @doc("Create or update {TName} (ID is required in payload; existing resource will be overwritten)", {TName: TName})
    createOrUpdate(
        @header contentType: yaml | json;

        ...CreateOrUpdateT
    ): {
        @statusCode _: "200";

        @body
        @doc("Details of {TName} resource updated along with ID", {TName: TName})
        body: ResourceUpdatedResponse<T, TName>;
    };
}

interface UpdateEndpoint<T, TName extends string, UpdateT = T> {
    @put
    @route("{id}")
    @doc("Update {TName} by id (overwrite)", {TName: TName})
    update(
        @header contentType: yaml | json;

        @path
        @doc("ID of the {TName}", {TName: TName})
        id: uuid,

        ...UpdateT,
    ): {
        @statusCode _: "200";

        @body
        @doc("Details of {TName} resource updated along with ID", {TName: TName})
        body: ResourceUpdatedResponse<T, TName>;
    };
}

interface PatchEndpoint<T, TName extends string, PatchT = T> {
    @patch
    @route("{id}")
    @doc("Patch {TName} by id (merge changes)", {TName: TName})
    patch(
        @header contentType: yaml | json;

        @path
        @doc("ID of the {TName}", {TName: TName})
        id: uuid,

        ...PatchT,
    ): {
        @statusCode _: "200";

        @body
        @doc("Details of {TName} resource patched along with ID", {TName: TName})
        body: ResourceUpdatedResponse<T, TName>;
    };
}

interface GetEndpoint<T, TName extends string> {
    @get
    @route("{id}")
    @doc("Get {TName} by id", {TName: TName})
    get(
        @path
        @doc("ID of the {TName}", {TName: TName})
        id: uuid,
    ): T;
}

interface DeleteEndpoint<T, TName extends string> {
    @delete
    @route("{id}")
    @doc("Delete {TName} by id", {TName: TName})
    delete(
        @path
        @doc("ID of the {TName}", {TName: TName})
        id: uuid,
    ): {
        @statusCode _: "202";

        @body
        @doc("Details of {TName} resource deleted along with ID", {TName: TName})
        body: ResourceDeletedResponse<T, TName>;
    };
}

interface ChildLimitOffsetPagination<
    T,
    TName extends string,
    P,
    PName extends string
> {
    @get
    @doc("List {TName} items of parent {PName}", {TName: TName, PName: PName})
    list(
        @path
        @doc("ID of parent {PName}", {PName: PName})
        id: uuid,
        
        ...PaginationOptions<TName>
    ): {results: T[]};
}

interface ChildCreateEndpoint<
    T,
    TName extends string,
    P,
    PName extends string,
    CreateT = T
> {
    @post
    @doc("Create new {TName}", {TName: TName})
    create(
        @header contentType: yaml | json;

        @path
        @doc("ID of parent {PName}", {PName: PName})
        id: uuid,

        ...CreateT,
    ): {
        @statusCode _: "201";

        @body
        @doc("Details of {TName} resource created along with ID", {TName: TName})
        body: ResourceCreatedResponse<T, TName>;
    };
}

interface ChildDeleteEndpoint<
    T,
    TName extends string,
    P,
    PName extends string
> {
    @post
    @doc("Delete {TName} of a {PName} by id", {TName: TName, PName: PName})
    delete(
        @path
        @doc("ID of parent {PName}", {PName: PName})
        parent_id: uuid,

        @path
        @doc("ID of the {TName}", {TName: TName})
        id: uuid,
    ): {
        @statusCode _: "202";

        @body
        @doc("Details of {TName} resource deleted along with ID", {TName: TName})
        body: ResourceDeletedResponse<T, TName>;
    };
}
