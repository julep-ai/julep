import "../../common";
import "./contexts.tsp";
import "./extensions.tsp";
import "./sessions.tsp";

namespace Tools;

using Common;

alias BrowserbaseMethod = (
    /** Get live URLs from the browserbase context */
    | "get_live_urls"

    /** List the sessions in the browserbase context */
    | "list_sessions"

    /** Create a new session in the browserbase context */
    | "create_session"

    /** Get a session from the browserbase context */
    | "get_session"

    /** Update a session in the browserbase context */
    | "update_session"

    // TODO: Implement these
    /** Create a new browserbase context */
    | "create_context"

    /** Upload an extension to the browserbase context */
    | "upload_extension"

    /** Get an extension from the browserbase context */
    | "get_extension"

    /** Delete an extension from the browserbase context */
    | "delete_extension"

    /** Create session uploads in the browserbase context */
    | "create_session_uploads"

    /** Get session downloads from the browserbase context */
    | "get_session_downloads"

    /** Get logs from the browserbase context */
    | "get_logs"

    /** Get recordings from the browserbase context */
    | "get_recordings"
);

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

alias BrowserbaseIntegrationDef = (
    | BrowserbaseContextIntegrationDef
    // | BrowserbaseExtensionIntegrationDef
    | BrowserbaseSessionIntegrationDef
);

alias BrowserbaseArguments = (
    | BrowserbaseSessionArguments
    // TODO: Implement these
    // | BrowserbaseContextArguments
    // | BrowserbaseExtensionArguments
);

alias BrowserbaseOutput = (
    | BrowserbaseSessionOutput
    // TODO: Implement these
    // | BrowserbaseContextOutput
    // | BrowserbaseExtensionOutput
);

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
            method: "update_session",
            description: "Update a session in the browserbase context",
        },
        #{
            method: "get_session_live_urls",
            description: "Get live URLs from the browserbase context",
        }
    ];
}