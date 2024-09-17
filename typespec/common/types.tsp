import "@typespec/http";
import "@typespec/openapi";

using TypeSpec.Http;
using TypeSpec.OpenAPI;

namespace Common;

//
// COMMON TYPES
//

alias Metadata = Record<unknown>;

model ResourceCreatedResponse {
    @doc("ID of created resource")
    id: uuid;
    ...HasCreatedAt;
    ...HasJobs;
}

model ResourceUpdatedResponse {
    @doc("ID of updated resource")
    id: uuid;
    ...HasUpdatedAt;
    ...HasJobs;
}

model ResourceDeletedResponse {
    @doc("ID of deleted resource")
    id: uuid;
    ...HasDeletedAt;
    ...HasJobs;
}

model PaginationOptions {
    @query
    @doc("Limit the number of items returned")
    limit: limit = 100,

    @query
    @doc("Offset the items returned")
    offset: offset = 0,

    /** Sort by a field */
    @query sort_by: sortBy = "created_at",

    /** Sort direction */
    @query direction: sortDirection = "asc",

    /** JSON string of object that should be used to filter objects by metadata */
    @query metadata_filter: string = "{}",
}