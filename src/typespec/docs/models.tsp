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
    embeddings: float32[] | float32[][] | null = null;

    @visibility("read")
    /** Modality of the document */
    modality?: string;

    @visibility("read")
    /** Language of the document */
    language?: string;

    @visibility("read")
    /** Embedding model used for the document */
    embedding_model?: string;

    @visibility("read")
    /** Dimensions of the embedding model */
    embedding_dimensions?: uint16;
}

/** Payload for creating a doc */
@withVisibility("create")
model CreateDocRequest {
    ...HasId;
    ...HasMetadata;
    ...HasCreatedAt;

    /** Title describing what this document contains */
    @maxLength(800)
    title: string;

    /** Contents of the document. Each string is limited to 30k characters. */
    content: content | content[];

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
    embedding?: float[];
}

model DocReference {
    ...HasMetadata;

    /** The owner of this document. */
    owner: DocOwner;

    /** ID of the document */
    id: Doc.id;

    title?: string;

    snippet: Snippet;
    distance: float | null = null;
}

model SingleEmbedQueryRequest {
    /** Text to embed */
    text: string;

    /** Instruction for the embedding model. */
    embed_instruction: string = "";
}

model MultipleEmbedQueryRequest {
    /** Texts to embed */
    @minItems(1)
    @maxItems(100)
    text: string[];

    /** Instruction for the embedding model. */
    embed_instruction: string = "";
}

alias EmbedQueryRequest = SingleEmbedQueryRequest | MultipleEmbedQueryRequest;

model EmbedQueryResponse {
    /** The embedded vectors */
    vectors: float[][];
}

// Base search parameters common to all search types
model BaseSearchParams {
    /** The limit of documents to return */
    @minValue(1)
    @maxValue(50)
    limit: uint16 = 10;
    
    /** Metadata filter to apply to the search */
    metadata_filter: MetadataFilter = #{};

    /** Whether to include embeddings in the response */
    include_embeddings: boolean = true;
}

// Text search specific parameters
model TextSearchParams {
    /** Text to use in the search */
    text: string;
    
    /** The language to be used for text search. Support for other languages coming soon. */
    lang: string = "en-US";
    
    /** Trigram similarity threshold for fuzzy matching. Set to null to disable trigram search. */
    @minValue(0)
    @maxValue(1)
    trigram_similarity_threshold: float | null = null;
}

// Vector search specific parameters  
model VectorSearchParams {
    /** Vector to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown. */
    vector: float[];
    
    /** The confidence cutoff level */
    @minValue(-1)
    @maxValue(1)
    confidence: float = 0.5;
    
    /** MMR Strength (mmr_strength = 1 - mmr_lambda) */
    @minValue(0)
    @maxValueExclusive(1)
    mmr_strength?: float = 0.5;
}

// Hybrid search parameters
model HybridSearchParams {
    /** The weight to apply to BM25 vs Vector search results. 0 => pure BM25; 1 => pure vector; */
    @minValue(0)
    @maxValue(1)
    alpha: float = 0.5;
    
    /** The k_multiplier to control how many intermediate results to fetch before final scoring */
    @minValue(1)
    @maxValue(10)
    k_multiplier: int8 = 5;
}

// Composed search request models
model TextOnlyDocSearchRequest {
    ...BaseSearchParams;
    ...TextSearchParams;
    vector?: never;
}

model VectorDocSearchRequest {
    ...BaseSearchParams;
    ...VectorSearchParams;
    text?: never;
}

model HybridDocSearchRequest {
    ...BaseSearchParams;
    ...TextSearchParams;
    ...VectorSearchParams;
    ...HybridSearchParams;
}

alias DocSearchRequest = VectorDocSearchRequest | TextOnlyDocSearchRequest | HybridDocSearchRequest;

model DocSearchResponse {
    /** The documents that were found */
    docs: DocReference[];

    /** The time taken to search in seconds */
    @minValueExclusive(0)
    time: float;
}

model BulkDeleteDocsRequest {
    /** Metadata filter to apply to the search */
    metadata_filter: MetadataFilter = #{};

    /** Delete all docs */
    delete_all: boolean = false;
}
