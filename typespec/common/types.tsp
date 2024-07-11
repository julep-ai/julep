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