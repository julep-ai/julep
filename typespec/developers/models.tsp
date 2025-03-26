import "../common";

using TypeSpec.Http;
using TypeSpec.OpenAPI;
using TypeSpec.Versioning;
using Common;

namespace Developers;

/** Developer model representing a platform developer account */
model Developer {
    /** The developer's unique identifier */
    @visibility("read")
    id: uuid;

    /** The developer's email address */
    email: string;
    
    /** Whether the developer account is active */
    active: boolean;
    
    /** Tags associated with the developer */
    tags: string[];
    
    /** Developer settings */
    settings: Record<unknown>;
    
    ...HasTimestamps;
}

/** Payload for creating a developer */
@withVisibility("create")
model CreateDeveloperRequest {
    ...Developer;
}

/** Payload for updating a developer */
@withVisibility("update")
model UpdateDeveloperRequest {
    ...Developer;
}

/** Payload for patching a developer */
model PatchDeveloperRequest is UpdateDeveloperRequest {}