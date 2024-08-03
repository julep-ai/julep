import "../agents";
import "../common";
import "../users";

using Agents;
using Common;
using Users;

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
    id: User.id | Agent.id;
    role: "user" | "agent";
}

model DocReference {
    /** The owner of this document. */
    owner: DocOwner;

    /** ID of the document */
    id: Doc.id;

    /** Snippets referred to of the document */
    snippet_index: uint16[];

    title?: string;
    snippet?: string;
}

model EmbedQueryRequest {
    /** Text or texts to embed */
    text: string | string[];
}

model EmbedQueryResponse {
    /** The embedded vectors */
    vectors: float[][];
}

model BaseDocSearchRequest {
    /** The confidence cutoff level */
    @minValue(0)
    @maxValue(1)
    confidence: float = 0.5;

    /** The weight to apply to BM25 vs Vector search results. 0 => pure BM25; 1 => pure vector; */
    @minValue(0)
    @maxValue(1)
    alpha: float = 0.75;

    /** Whether to include the MMR algorithm in the search. Optimizes for diversity in search results. */
    mmr: boolean = false;

    /** The language to be used for text-only search. Support for other languages coming soon. */
    lang: "en-US" = "en-US";
}

model VectorDocSearchRequest extends BaseDocSearchRequest {
    /** Vector or vectors to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown. */
    vector: float[] | float[][];

    text?: never;
}

model TextOnlyDocSearchRequest extends BaseDocSearchRequest {
    /** Text or texts to use in the search. */
    text: string | string[];

    vector?: never;
}

model HybridDocSearchRequest extends BaseDocSearchRequest {
    /** Text or texts to use in the search. In `hybrid` search mode, either `text` or both `text` and `vector` fields are required. */
    text: string | string[];

    /** Vector or vectors to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown. */
    vector: float[] | float[][];
}

alias DocSearchRequest = VectorDocSearchRequest | TextOnlyDocSearchRequest | HybridDocSearchRequest;