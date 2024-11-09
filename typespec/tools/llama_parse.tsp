import "../common";

using Common;

namespace Tools;

/** Setup parameters for LlamaParse integration */
model LlamaParseSetup {
    /** The API key for LlamaParse */
    llamaparse_api_key: string;
}

/** Arguments for LlamaParse integration */
model LlamaParseFetchArguments {
    /** The format of the result. Can be "text" or "markdown". Default is "text". */
    result_format?: "text" | "markdown" = "text";

    /** Number of workers for parallel processing. Default is 2, but can be set between 1 and 10. */
    @minValue(1)
    @maxValue(10)
    num_workers?: uint8 = 2;

    /** Verbose mode for detailed logging. Default is true. */
    verbose?: boolean = true;

    /** Language of the text. Default is English.*/
    language?: string = "en";

    /** File Name. If not provided, a random name will be generated. */
    filename?: string;

    /** The base64 string of the file*/
    file: string;
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
    methods: ProviderMethod<LlamaParseFetchArguments, LlamaParseFetchOutput>[] = #[
        #{
            method: "parse",
            description: "Parse and Extract the Files",
        }
    ];
    info: ProviderInfo = #{
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