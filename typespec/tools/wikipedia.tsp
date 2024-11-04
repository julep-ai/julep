import "../common";

using Common;

namespace Tools;

/** Arguments for Wikipedia Search */
model WikipediaSearchArguments {
    /** The search query string */
    query: string;

    /** Maximum number of documents to load */
    @minValue(1)
    @maxValue(10)
    load_max_docs: uint8 = 2;
}

/** Wikipedia integration definition */
model WikipediaIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "wikipedia" */
    provider: "wikipedia" = "wikipedia";
    
    /** The specific method of the integration to call */
    method?: string;
    
    /** The setup parameters for Wikipedia */
    setup?: null = null;
    
    /** The arguments for Wikipedia Search */
    arguments?: WikipediaSearchArguments;
}

/** Wikipedia Provider Card */
model WikipediaProviderCard extends BaseProviderCard {
    provider: "wikipedia" = "wikipedia";
    setup: null = null;
    methods: ProviderMethod<WikipediaSearchArguments, WikipediaSearchOutput>[] = #[
        #{
            method: "search",
            description: "Search for a page on Wikipedia",
        }
    ];
    info: ProviderInfo = #{
        url: "https://www.wikipedia.org/",
        docs: "https://www.wikipedia.org/wiki/Main_Page",
        icon: "https://www.wikipedia.org/static/favicon/wikipedia.ico",
        friendly_name: "Wikipedia",
    };
}

/** Represents a document with text content */
model WikipediaDocument {
    // Using string for now since we need to represent langchain Document
    page_content: string;
    metadata: Record<unknown>;
} 

/** Wikipedia Search Output */
model WikipediaSearchOutput {
    /** The documents returned from the Wikipedia search */
    documents: WikipediaDocument[];
}