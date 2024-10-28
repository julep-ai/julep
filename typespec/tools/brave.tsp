import "../common";

using Common;

namespace Tools;

/** Integration definition for Brave Search */
model BraveSearchSetup {
    /** The api key for Brave Search */
    api_key: string;
}

/** Arguments for Brave Search */
model BraveSearchArguments {
    /** The search query for searching with Brave */
    query: string;
}

/** Brave integration definition */
model BraveIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "brave" */
    provider: "brave" = "brave";
    
    /** The specific method of the integration to call */
    method?: string;
    
    /** The setup parameters for Brave */
    setup?: BraveSearchSetup;
    
    /** The arguments for Brave Search */
    arguments?: BraveSearchArguments;
} 