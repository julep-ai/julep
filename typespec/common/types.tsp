import "@typespec/http";
import "@typespec/openapi";

using TypeSpec.Http;
using TypeSpec.OpenAPI;

namespace Common;

//
// COMMON TYPES
//

alias Metadata = Record<unknown>;

model ResourceCreatedResponse<T, TName extends string> {
    @doc("ID of created {TName}", {TName: TName})
    id: uuid;
    ...HasCreatedAt;
    ...HasJobs;
}

model ResourceUpdatedResponse<T, TName extends string> {
    @doc("ID of updated {TName}", {TName: TName})
    id: uuid;
    ...HasUpdatedAt;
    ...HasJobs;
}

model ResourceDeletedResponse<T, TName extends string> {
    @doc("ID of deleted {TName}", {TName: TName})
    id: uuid;
    ...HasDeletedAt;
    ...HasJobs;
}

model PaginationOptions<TName extends string> {
    @query
    @doc("Limit the number of {TName} items returned", {TName: TName})
    limit: limit = 100,

    @query
    @doc("Offset the {TName} items returned", {TName: TName})
    offset: offset = 0,

    /** Sort by a field */
    @query sort_by: sortBy = "created_at",

    /** Sort direction */
    @query direction: sortDirection = "asc",

    /** JSON string of object that should be used to filter objects by metadata */
    @query metadata_filter: string = "{}",
}