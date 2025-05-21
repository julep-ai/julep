import "../common";

using Common;

namespace Tools;

/** Integration definition for Algolia */
model AlgoliaSetup {
    /** The Algolia Application ID */
    algolia_application_id: string;
    
    /** The Algolia API Key */
    algolia_api_key: string;
}

/** Arguments for Algolia Search */
model AlgoliaSearchArguments {
    /** The index name to search */
    index_name: string;
    
    /** The query to search for */
    query: string;
    
    /** Optional attributes to retrieve */
    attributes_to_retrieve?: string[];
    
    /** Maximum number of hits to return */
    @minValue(1)
    @maxValue(1000)
    hits_per_page?: int32 = 10;
}

/** Algolia integration definition */
model AlgoliaIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "algolia" */
    provider: "algolia" = "algolia";
    
    /** The specific method of the integration to call */
    method?: string;
    
    /** The setup parameters for Algolia */
    setup?: AlgoliaSetup;
    
    /** The arguments for Algolia */
    arguments?: AlgoliaSearchArguments;
}

/** Algolia Provider Card */
model AlgoliaProviderCard extends BaseProviderCard {
    provider: "algolia" = "algolia";
    setup: AlgoliaSetup;
    methods: ProviderMethod<AlgoliaSearchArguments, AlgoliaSearchOutput>[] = [
        {
            method: "search",
            description: "Search for content in an Algolia index",
        }
    ];
    info: ProviderInfo = {
        url: "https://www.algolia.com/",
        docs: "https://www.algolia.com/doc/",
        icon: "https://www.algolia.com/favicon.ico",
        friendly_name: "Algolia Search",
    };
}

/** Algolia Search Output */
model AlgoliaSearchOutput {
    /** The search results */
    hits: unknown[];
    
    /** Additional metadata from the search */
    metadata: unknown;
} 