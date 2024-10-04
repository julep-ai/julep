namespace Tools;

//
// INTEGRATION MODELS
//

/** Integration provider name */
alias integrationProvider = (
    | "dummy"
    | "hacker_news"
    | "weather"
    | "wikipedia"
    | "spider"
    | "brave"
    | "browserbase"
);

/** The setup parameters the integration accepts */
alias IntegrationSetup = Record<unknown>;

/** The arguments to pre-apply to the integration call */
alias IntegrationArguments = Record<unknown>;

// TODO: Add integration types in detail

/** Integration definition */
model IntegrationDef {
    /** The provider of the integration */
    provider: integrationProvider | string;

    /** The specific method of the integration to call */
    method?: string;

    /** The setup parameters the integration accepts */
    setup?: IntegrationSetup;

    /** The arguments to pre-apply to the integration call */
    arguments?: IntegrationArguments;
}
