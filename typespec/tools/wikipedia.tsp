import "../common";

using Common;

namespace Tools;

/** Integration setup for Wikipedia */
model WikipediaSearchSetup {
    // Wikipedia doesn't require any setup parameters
}

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
    setup?: WikipediaSearchSetup;
    
    /** The arguments for Wikipedia Search */
    arguments?: WikipediaSearchArguments;
} 