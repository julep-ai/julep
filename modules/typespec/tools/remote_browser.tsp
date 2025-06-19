import "../common";

using Common;

namespace Tools;

alias RemoteBrowserAction = 
    | /** Press a key */
      "key"
    | /** Type text */
      "type"
    | /** Move the mouse to a coordinate */
      "mouse_move"
    | /** Left click */
      "left_click"
    | /** Left click and drag */
      "left_click_drag"
    | /** Right click */
      "right_click"
    | /** Middle click */
      "middle_click"
    | /** Double click */
      "double_click"
    | /** Take a screenshot */
      "screenshot"
    | /** Get the cursor position */
      "cursor_position"
    | /** Navigate to a URL */
      "navigate"
    | /** Refresh the page */
      "refresh";

/** The setup parameters for the remote browser */
model RemoteBrowserSetup {
    /** The connection URL for the remote browser */
    connect_url?: string;

    /** The width of the browser */
    width?: uint16;

    /** The height of the browser */
    height?: uint16;
}

/** The arguments for the remote browser */
model RemoteBrowserArguments {
    /** The connection URL for the remote browser */
    connect_url?: string;
    
    /** The action to perform */
    action: RemoteBrowserAction;

    /** The text */
    text?: string;

    /** The coordinate to move the mouse to */
    coordinate?: [uint16, uint16];
}

/** The output of the remote browser */
model RemoteBrowserOutput {
    /** The output of the action */
    output: string | null = null;

    /** The error of the action */
    error: string | null = null;

    /** The base64 encoded image of the action */
    base64_image: string | null = null;

    /** The system output of the action */
    system: string | null = null;
}

/** The integration definition for the remote browser */
model RemoteBrowserIntegrationDef extends BaseIntegrationDef {
    provider: "remote_browser" = "remote_browser";
    setup: RemoteBrowserSetup;
    method: "perform_action" = "perform_action";
    arguments?: RemoteBrowserArguments;
}

model RemoteBrowserProviderCard extends BaseProviderCard {
    provider: "remote_browser" = "remote_browser";
    setup: RemoteBrowserSetup;
    methods: ProviderMethod<RemoteBrowserArguments, RemoteBrowserOutput>[] = #[
        #{
            method: "perform_action",
            description: "Perform an action in the remote browser",
        }
    ];
    info: ProviderInfo = #{
        url: "https://playwright.dev/",
        docs: "https://playwright.dev/docs/api/class-page",
        icon: "https://playwright.dev/favicon.ico",
        friendly_name: "Playwright",
    };
}
