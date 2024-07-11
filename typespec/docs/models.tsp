import "../common";

using Common;

namespace Docs;

//
// DOCS MODELS
//

model Doc {
    ...HasId;
    ...HasMetadata;
    ...HasCreatedAt;

    /** Title describing what this document contains */
    @maxLength(800)
    title: identifierSafeUnicode;

    /** Contents of the document */
    content: string | string[];
}

/** Payload for creating a doc */
@withVisibility("create")
model CreateDocRequest {
    ...Doc;
}

model DocOwner {
    id: uuid;
    role: "user" | "agent";
}

model DocReference {
    /** The owner of this document. */
    owner: DocOwner;

    /** ID of the document */
    id: uuid;

    /** Snippets referred to of the document */
    snippet_index: uint16[];
}