import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Document data for creating a document */
model DocData {
    /** The title of the document */
    title: string;

    /** The content of the document */
    content: string;
    
    /** Optional metadata for the document */
    metadata?: Record<unknown>;
}

/** Create Doc System Definition Arguments */
model CreateDocSystemDefArguments {
    /** The document name */
    name: string;
    
    /** The document content */
    content: string;
    
    /** Optional metadata for the document */
    metadata?: Record<unknown>;
}

/** Create Doc System Definition */
model CreateDocSystemDef extends SystemDef {
    system_def_type: "CreateDocSystemDef" = "CreateDocSystemDef";
    resource: "doc";
    operation: "create";
    arguments?: CreateDocSystemDefArguments;
}

/** Create Owner Doc System Definition Arguments */
model CreateOwnerDocSystemDefArguments {
    /** The resource ID (if applicable) */
    resource_id: uuid;
    
    /** The document data to create */
    ...DocData;
}

/** Create Owner Doc System Definition */
model CreateOwnerDocSystemDef extends SystemDef {
    system_def_type: "CreateOwnerDocSystemDef" = "CreateOwnerDocSystemDef";
    resource: "agent" | "user";
    operation: "create";
    subresource: "doc";
    arguments?: CreateOwnerDocSystemDefArguments;
}

/** Embed Doc System Definition Arguments */
model EmbedDocSystemDefArguments {
    /** The resource ID to embed */
    resource_id: uuid;
}

/** Embed Doc System Definition */
model EmbedDocSystemDef extends SystemDef {
    system_def_type: "EmbedDocSystemDef" = "EmbedDocSystemDef";
    resource: "doc";
    operation: "embed";
    arguments?: EmbedDocSystemDefArguments;
}

/** Get Doc System Definition Arguments */
model GetDocSystemDefArguments {
    /** The resource ID to get */
    resource_id: uuid;
}

/** Get Doc System Definition */
model GetDocSystemDef extends SystemDef {
    system_def_type: "GetDocSystemDef" = "GetDocSystemDef";
    resource: "doc";
    operation: "get";
    arguments?: GetDocSystemDefArguments;
}

/** List Docs System Definition Arguments */
model ListDocsSystemDefArguments {
    /** Filter string */
    filter?: string;
    
    /** Maximum number of results */
    limit?: int32;
    
    /** Offset for pagination */
    offset?: int32;
}

/** List Docs System Definition */
model ListDocsSystemDef extends SystemDef {
    system_def_type: "ListDocsSystemDef" = "ListDocsSystemDef";
    resource: "doc";
    operation: "list";
    arguments?: ListDocsSystemDefArguments;
}

/** Delete Doc System Definition Arguments */
model DeleteDocSystemDefArguments {
    /** The resource ID to delete */
    resource_id: uuid;
}

/** Delete Doc System Definition */
model DeleteDocSystemDef extends SystemDef {
    system_def_type: "DeleteDocSystemDef" = "DeleteDocSystemDef";
    resource: "doc";
    operation: "delete";
    arguments?: DeleteDocSystemDefArguments;
}

/** Simple Search Docs System Definition Arguments */
model SimpleSearchDocsSystemDefArguments {
    /** The search query */
    query: string;
    
    /** Maximum number of results */
    limit?: int32;
    
    /** Type of search to perform */
    search_type?: "text" | "embedding" | "hybrid";
}

/** Search Docs System Definition - Simple query */
model SimpleSearchDocsSystemDef extends SystemDef {
    system_def_type: "SimpleSearchDocsSystemDef" = "SimpleSearchDocsSystemDef";
    resource: "doc";
    operation: "search";
    arguments?: SimpleSearchDocsSystemDefArguments;
}

/** Text Search Owner Docs System Definition Arguments */
model TextSearchOwnerDocsSystemDefArguments {
    /** The resource ID to search within */
    resource_id: uuid;
    
    /** Text to search for */
    text: string;
    
    /** Maximal Marginal Relevance strength (0-1) */
    mmr_strength?: float32;
    
    /** Maximum number of results to return */
    limit?: int32;
}

/** Text Search Documents System Definition - For owner resources */
model TextSearchOwnerDocsSystemDef extends SystemDef {
    system_def_type: "TextSearchOwnerDocsSystemDef" = "TextSearchOwnerDocsSystemDef";
    resource: "agent" | "user";
    operation: "search";
    subresource: "doc";
    arguments?: TextSearchOwnerDocsSystemDefArguments;
}

/** Vector Search Owner Docs System Definition Arguments */
model VectorSearchOwnerDocsSystemDefArguments {
    /** The resource ID to search within */
    resource_id: uuid;
    
    /** Vector to search for similarity - should be 1024-dimensional vector */
    vector: float32[];
    
    /** Maximal Marginal Relevance strength (0-1) */
    mmr_strength?: float32;
    
    /** Confidence threshold (0-1) */
    confidence?: float32;
    
    /** Maximum number of results to return */
    limit?: int32;
}

/** Vector Search Documents System Definition - For owner resources */
model VectorSearchOwnerDocsSystemDef extends SystemDef {
    system_def_type: "VectorSearchOwnerDocsSystemDef" = "VectorSearchOwnerDocsSystemDef";
    resource: "agent" | "user";
    operation: "search";
    subresource: "doc";
    arguments?: VectorSearchOwnerDocsSystemDefArguments;
}

/** Hybrid Search Owner Docs System Definition Arguments */
model HybridSearchOwnerDocsSystemDefArguments {
    /** The resource ID to search within */
    resource_id: uuid;
    
    /** Text to search for */
    text: string;
    
    /** Vector to search for similarity - should be 1024-dimensional vector */
    vector: float32[];
    
    /** Alpha parameter controlling blend of text vs vector search (0-1) */
    alpha?: float32;
    
    /** Confidence threshold (0-1) */
    confidence?: float32;
    
    /** Maximal Marginal Relevance strength (0-1) */
    mmr_strength?: float32;
    
    /** Maximum number of results to return */
    limit?: int32;
}

/** Hybrid Search Documents System Definition - For owner resources */
model HybridSearchOwnerDocsSystemDef extends SystemDef {
    system_def_type: "HybridSearchOwnerDocsSystemDef" = "HybridSearchOwnerDocsSystemDef";
    resource: "agent" | "user";
    operation: "search";
    subresource: "doc";
    arguments?: HybridSearchOwnerDocsSystemDefArguments;
}