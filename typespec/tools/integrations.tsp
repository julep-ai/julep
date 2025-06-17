import "./base.tsp";

using Tools;

namespace Tools;

// AIDEV-NOTE: Integration provider definitions extracted from models.tsp.

@discriminator("provider")
model BaseIntegrationDef {
    /** The provider of the integration */
    provider: integrationProvider;

    /** The specific method of the integration to call */
    method?: string;

    /** The setup parameters the integration accepts */
    setup?: unknown;

    /** The arguments to pre-apply to the integration call */
    arguments?: unknown;
}

model DummyIntegrationDef extends BaseIntegrationDef {
    provider: "dummy" = "dummy";
}

model BaseProviderCard {
    provider: integrationProvider;
    setup: unknown;
    methods: ProviderMethod<unknown, unknown>[];
    info: ProviderInfo;
}

model ProviderMethod<Arguments, Output> {
    method: string;
    description?: string;
    arguments?: Arguments;
    output?: Output;
}

model ProviderInfo {
    url?: url;
    docs?: url;
    icon?: url;
    friendly_name?: string;
}

alias IntegrationDef = (
    | DummyIntegrationDef
    | BraveIntegrationDef
    | EmailIntegrationDef
    | SpiderIntegrationDef
    | WikipediaIntegrationDef
    | WeatherIntegrationDef
    | MailgunIntegrationDef
    | BrowserbaseIntegrationDef
    | RemoteBrowserIntegrationDef
    | LlamaParseIntegrationDef
    | FfmpegIntegrationDef
    | CloudinaryIntegrationDef
    | ArxivIntegrationDef
    | UnstructuredIntegrationDef
    | AlgoliaIntegrationDef
);
