import "./scalars.tsp";
import "./types.tsp";

namespace Common;

//
// COMMON MIXINS
//

model HasCreatedAtOptional {
    /** When this resource was created as UTC date-time */
    @visibility("read")
    created_at?: utcDateTime;
}

model HasCreatedAt {
    /** When this resource was created as UTC date-time */
    @visibility("read")
    created_at: utcDateTime;
}

model HasUpdatedAt {
    /** When this resource was updated as UTC date-time */
    @visibility("read")
    updated_at: utcDateTime;
}

model HasDeletedAt {
    /** When this resource was deleted as UTC date-time */
    @visibility("read")
    deleted_at: utcDateTime;
}

model HasTimestamps {
    ...HasCreatedAt;
    ...HasUpdatedAt;
}

model HasIdOptional {
    @visibility("read")
    id?: uuid;
}

model HasId {
    @visibility("read")
    @key
    id: uuid;
}

/** (Optional) Metadata for a resource */
model HasMetadata {
    metadata?: Metadata;
}

model HasJobs {
    /** IDs (if any) of jobs created as part of this request */
    @visibility("read")
    jobs: uuid[] = #[];
}
