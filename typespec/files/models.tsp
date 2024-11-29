import "../common";

using Common;

namespace Files;

//
// FILE MODELS
//

model File {
    ...HasId;
    ...HasCreatedAt;

    /** Name of the file */
    name: identifierSafeUnicode;

    /** Description of the file */
    description: string = "";

    /** MIME type of the file */
    mime_type: mimeType | null = null;

    /** Base64 encoded content of the file */
    content: string;

    /** Size of the file in bytes */
    @visibility("read")
    @minValue(1)
    size: uint64;

    /** Hash of the file */
    @visibility("read")
    hash: string;
}

/** Payload for creating a file */
@withVisibility("create")
model CreateFileRequest {
    ...File;
}
