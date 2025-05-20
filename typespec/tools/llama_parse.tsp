import "../common";

using Common;

namespace Tools;

/** Setup parameters for LlamaParse integration */
model LlamaParseSetup {
    /** The API key for LlamaParse */
    llamaparse_api_key: string;

    /** Optional upload parameters */
    params?: Record<unknown>;
}

/** Arguments for LlamaParse integration */
model LlamaParseFetchArguments {
    /** File Name. If not provided, a random name will be generated. */
    filename?: string;

    /** The base64 string of the file, which can be a single string or a list of strings */
    file: string | Array<string>;

    /** Optional upload parameters */
    params?: Record<unknown>;

     /** The input file is base64 */
    base64?: boolean = false;
}

/** LlamaParse integration definition */
model LlamaParseIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "LlamaParseSetup" */
    provider: "llama_parse" = "llama_parse";
    
    /** The specific method of the integration to call */
    method?: string;
    
    /** The setup parameters for LlamaParse */
    setup?: LlamaParseSetup;
    
    /** The arguments for LlamaParse */
    arguments?: LlamaParseFetchArguments;
}

/** LlamaParse Provider Card */
model LlamaParseProviderCard extends BaseProviderCard {
    provider: "llama_parse" = "llama_parse";
    setup: LlamaParseSetup;
    methods: ProviderMethod<LlamaParseFetchArguments, LlamaParseFetchOutput>[] = [
        {
            method: "parse",
            description: "Parse and Extract the Files",
        }
    ];
    info: ProviderInfo = {
        url: "https://www.llamaindex.ai/",
        docs: "https://docs.cloud.llamaindex.ai/llamaparse/getting_started",
        icon: "https://www.llamaindex.ai/favicon.ico",
        friendly_name: "LlamaParse",
    };
}

/** Represents a document with text content */
model LlamaParseDocument {
    // Using string for now since we need to represent langchain Document
    text: string;
    metadata: Record<unknown>;
} 

/** LlamaParse Fetch Output */
model LlamaParseFetchOutput {
    /** The documents returned from the LlamaParse */
    documents: LlamaParseDocument[];
}