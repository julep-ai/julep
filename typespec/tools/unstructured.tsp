import "../common";

using Common;

namespace Tools;

/** Setup parameters for Unstructured integration */
model UnstructuredSetup {
    /** The API key for Unstructured.io */
    unstructured_api_key: string;

    /** Optional server endpoint URL */
    server_url?: string;

    /** The server by name to use for all methods */
    server?: string;

    /** Parameters to optionally template the server URL with */
    url_params?: Record<unknown>;

    /** The retry configuration to use for all supported methods */
    retry_config?: Record<unknown>;

    /** Optional request timeout applied to each operation in milliseconds */
    timeout_ms?: int16;
}

/** Arguments for Unstructured partition integration */
model UnstructuredPartitionArguments {
    /** File Name. If not provided, a random name will be generated. */
    filename?: string;

    /** The base64 string of the file, which can be a single string or a list of strings */
    file: string | Array<string>;

    /** Additional partition parameters */
    partition_params?: Record<unknown>;
}

/** Unstructured integration definition */
model UnstructuredIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "unstructured" */
    provider: "unstructured" = "unstructured";
    
    /** The specific method of the integration to call */
    method?: string;
    
    /** The setup parameters for Unstructured */
    setup?: UnstructuredSetup;
    
    /** The arguments for Unstructured */
    arguments?: UnstructuredPartitionArguments;
}

/** Unstructured Provider Card */
model UnstructuredProviderCard extends BaseProviderCard {
    provider: "unstructured" = "unstructured";
    setup: UnstructuredSetup;
    methods: ProviderMethod<UnstructuredPartitionArguments, UnstructuredPartitionOutput>[] = #[
        #{
            method: "partition",
            description: "Partition documents into structured elements",
        }
    ];
    info: ProviderInfo = #{
        url: "https://unstructured.io/",
        docs: "https://docs.unstructured.io/",
        icon: "https://unstructured.io/favicon.ico",
        friendly_name: "Unstructured.io",
    };
}

/** Represents a document element from Unstructured */
model UnstructuredElement {
    /** The type of element */
    element_type: string;
    
    /** The text content of the element */
    text: string;
    
    /** Metadata about the element */
    metadata: Record<unknown>;
}

/** Unstructured Partition Output */
model UnstructuredPartitionOutput {
    /** The elements returned from Unstructured */
    elements: UnstructuredElement[];
} 