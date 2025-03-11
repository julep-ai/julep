import "@typespec/events";
import "@typespec/http";
import "@typespec/openapi";
import "@typespec/rest";

using TypeSpec.Events;
using TypeSpec.Http;
using TypeSpec.OpenAPI;
using TypeSpec.Rest;

namespace Common;

//
// COMMON TYPES
//

alias Metadata = Record<unknown>;
alias MetadataFilter = Record<unknown>;

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

    /** Object to filter results by metadata */
    @query metadata_filter: Record<unknown> = #{},
}

@events
union StreamEvent<T> {
    T;
}
