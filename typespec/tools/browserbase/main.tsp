import "../../common";
import "./contexts.tsp";
import "./extensions.tsp";
import "./sessions.tsp";

namespace Tools;

using Common;

alias BrowserbaseMethod =
    | /** Get live URLs from the browserbase context */
      "get_live_urls"
    | /** List the sessions in the browserbase context */
      "list_sessions"
    | /** Create a new session in the browserbase context */
      "create_session"
    | /** Get a session from the browserbase context */
      "get_session"
    | /** Complete a session in the browserbase context */
      "complete_session"
    | /** Get the connection URL for a session */
      "get_connect_url"
    | /** Install an extension from GitHub to the browserbase context */
      "install_extension_from_github"
    | // TODO: Implement these
      /** Create a new browserbase context */
      "create_context"
    | /** Get session downloads from the browserbase context */
      "get_session_downloads"
    | /** Get logs from the browserbase context */
      "get_logs"
    | /** Get recordings from the browserbase context */
      "get_recordings";

/** The setup parameters for the browserbase integration */
model BrowserbaseSetup {
    /** API key for the browserbase integration */
    api_key: string;
}

/** The base definition for a browserbase integration */
model BaseBrowserbaseIntegrationDef extends BaseIntegrationDef {
    provider: "browserbase" = "browserbase";
    setup?: BrowserbaseSetup;
    method?: BrowserbaseMethod;
    arguments?: unknown;
}

alias BrowserbaseIntegrationDef = BrowserbaseContextIntegrationDef | BrowserbaseExtensionIntegrationDef | BrowserbaseSessionIntegrationDef;

alias BrowserbaseArguments = BrowserbaseSessionArguments | BrowserbaseContextArguments | BrowserbaseExtensionArguments;

alias BrowserbaseOutput = BrowserbaseSessionOutput | BrowserbaseContextOutput | BrowserbaseExtensionOutput;

model BrowserbaseProviderCard extends BaseProviderCard {
    provider: "browserbase" = "browserbase";
    setup: BrowserbaseSetup;
    methods: ProviderMethod<BrowserbaseArguments, BrowserbaseOutput>[] = #[
        #{
            method: "list_sessions",
            description: "List the sessions in the browserbase context",
        },
        #{
            method: "create_session",
            description: "Create a new session in the browserbase context",
        },
        #{
            method: "get_session",
            description: "Get a session from the browserbase context",
        },
        #{
            method: "complete_session",
            description: "Complete a session in the browserbase context",
        },
        #{
            method: "get_live_urls",
            description: "Get live URLs from the browserbase context",
        },
        #{
            method: "install_extension_from_github",
            description: "Install an extension from GitHub to the browserbase context",
        },
        #{
            method: "get_connect_url",
            description: "Get the connection URL for a session",
        }
    ];
}
