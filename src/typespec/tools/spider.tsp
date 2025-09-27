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

    /** The content type to return */
    content_type?: "application/json" | "text/csv" | "application/xml" | "application/jsonl" = "application/json";

    /** Additional parameters for the Spider API */
    params?: Record<unknown>;
}

alias SpiderMethod =
    | /** Crawl a website and extract data */
      "crawl"
    | /** Retrieve links from the specified URL. */
      "links"
    | /** Take a screenshot of the specified URL. */
      "screenshot"
    | /** Perform a search and gather a list of websites to start crawling and collect resources. */
      "search";

/** Spider integration definition */
model SpiderIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "spider" */
    provider: "spider" = "spider";
    
    /** The specific method of the integration to call */
    method?: SpiderMethod;
    
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