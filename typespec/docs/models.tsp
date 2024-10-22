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
    title: string;

    /** Contents of the document */
    content: string | string[];

    /** Embeddings for the document */
    @visibility("read")
    embeddings?: float32[] | float32[][];
}

/** Payload for creating a doc */
@withVisibility("create")
model CreateDocRequest {
    ...Doc;

    /** Instruction for the embedding model. */
    embed_instruction: string | null = null;
}

model DocOwner {
    id: User.id | Agent.id;
    role: "user" | "agent";
}

model Snippet {
    index: uint16;
    content: string;
}

model DocReference {
    /** The owner of this document. */
    owner: DocOwner;

    /** ID of the document */
    id: Doc.id;

    title?: string;
    
    @minItems(1)
    snippets: Snippet[];
    distance: float | null = null;
}

model EmbedQueryRequest {
    /** Text or texts to embed */
    text: string | string[];

    /** Instruction for the embedding model. */
    embed_instruction: string = "";
}

model EmbedQueryResponse {
    /** The embedded vectors */
    vectors: float[][];
}

model BaseDocSearchRequest {
    @minValue(1)
    @maxValue(100)
    limit: uint16 = 10;

    /** The language to be used for text-only search. Support for other languages coming soon. */
    lang: "en-US" = "en-US";
}

model VectorDocSearchRequest extends BaseDocSearchRequest {
    /** The confidence cutoff level */
    @minValue(0)
    @maxValue(1)
    confidence: float = 0.5;

    /** Vector to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown. */
    vector: float[];

    text?: never;
}

model TextOnlyDocSearchRequest extends BaseDocSearchRequest {
    /** Text to use in the search. */
    text: string;

    vector?: never;
}

model HybridDocSearchRequest extends BaseDocSearchRequest {
    /** The confidence cutoff level */
    @minValue(0)
    @maxValue(1)
    confidence: float = 0.5;

    /** The weight to apply to BM25 vs Vector search results. 0 => pure BM25; 1 => pure vector; */
    @minValue(0)
    @maxValue(1)
    alpha: float = 0.75;

    /** Text to use in the search. In `hybrid` search mode, either `text` or both `text` and `vector` fields are required. */
    text: string;

    /** Vector to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown. */
    vector: float[];
}

alias DocSearchRequest = VectorDocSearchRequest | TextOnlyDocSearchRequest | HybridDocSearchRequest;

model DocSearchResponse {
    /** The documents that were found */
    docs: DocReference[];

    /** The time taken to search in seconds */
    @minValueExclusive(0)
    time: float;
}