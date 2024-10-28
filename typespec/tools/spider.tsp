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