import "../../common";
import "./main.tsp";

using Common;

namespace Tools;

/** Create Doc System Definition */
model CreateDocSystemDef extends SystemDef {
    systemDefType: "CreateDocSystemDef";
    resource: "doc";
    operation: "create";
    arguments: {
        name: string;
        content: string;
        metadata?: Record<unknown>;
    };
}

/** Embed Doc System Definition */
model EmbedDocSystemDef extends SystemDef {
    systemDefType: "EmbedDocSystemDef";
    resource: "doc";
    operation: "embed";
    resource_id: uuid;
}

/** Get Doc System Definition */
model GetDocSystemDef extends SystemDef {
    systemDefType: "GetDocSystemDef";
    resource: "doc";
    operation: "get";
    resource_id: uuid;
}

/** List Docs System Definition */
model ListDocsSystemDef extends SystemDef {
    systemDefType: "ListDocsSystemDef";
    resource: "doc";
    operation: "list";
    arguments?: {
        filter?: string;
        limit?: int32;
        offset?: int32;
    };
}

/** Delete Doc System Definition */
model DeleteDocSystemDef extends SystemDef {
    systemDefType: "DeleteDocSystemDef";
    resource: "doc";
    operation: "delete";
    resource_id: uuid;
}

/** Search Docs System Definition */
model SearchDocsSystemDef extends SystemDef {
    systemDefType: "SearchDocsSystemDef";
    resource: "doc";
    operation: "search";
    arguments: {
        query: string;
        limit?: int32;
        search_type?: "text" | "embedding" | "hybrid";
    };
}