import "../common";

using Common;

namespace Tools;

/** Setup parameters for Spider integration */
model SpiderSetup {
    /** The API key for Spider */
    spider_api_key: string;
}

/** Arguments for Spider integration */
model SpiderFetchArguments {
    /** The URL to fetch data from */
    url: url;

    /** The type of crawler to use */
    mode?: "scrape" = "scrape";

    /** Additional parameters for the Spider API */
    params?: Record<unknown>;
}

/** Spider integration definition */
model SpiderIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "spider" */
    provider: "spider" = "spider";
    
    /** The specific method of the integration to call */
    method?: string;
    
    /** The setup parameters for Spider */
    setup?: SpiderSetup;
    
    /** The arguments for Spider */
    arguments?: SpiderFetchArguments;
}

/** Spider Provider Card */
model SpiderProviderCard extends BaseProviderCard {
    provider: "spider" = "spider";
    setup: SpiderSetup;
    methods: ProviderMethod<SpiderFetchArguments, SpiderFetchOutput>[] = #[
        #{
            method: "crawl",
            description: "Crawl a website and extract data",
        }
    ];
    info: ProviderInfo = #{
        url: "https://spider.com/",
        docs: "https://spider.com/docs/",
        icon: "https://spider.com/favicon.ico",
        friendly_name: "Spider",
    };
}

/** Spider Fetch Output */
model SpiderFetchOutput {
    /** The documents returned from the spider */
    documents: SpiderDocument[];
}

/** Represents a document with text content */
model SpiderDocument {
    // Using string for now since we need to represent langchain Document
    page_content: string;
    metadata: Record<unknown>;
} 