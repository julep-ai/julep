import "@typespec/http";

import "../common";

using TypeSpec.Http;

using Common;

namespace Users;

//
// USER MODELS
//

model User {
    ...HasId;
    ...HasMetadata;
    ...HasTimestamps;

    /** Name of the user */
    @maxLength(120)
    name: identifierSafeUnicode = "";

    /** About the user */
    about: string = "";
}

/** Payload for updating a user */
@withVisibility("create", "update")
model UpdateUserRequest {
    ...User;
}

/** Payload for patching a user */
model PatchUserRequest is UpdateUserRequest {}

/** Payload for creating a user (and associated documents) */
model CreateUserRequest {
    ...UpdateUserRequest;

    /** Documents to index for this user. (Max: 100 items) */
    @maxItems(100)
    docs: unknown[] = #[];
}

model CreateOrUpdateUserRequest {
    @path
    id: uuid;
    ...UpdateUserRequest;
}