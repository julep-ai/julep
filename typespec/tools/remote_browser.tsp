import "../common";

using Common;

namespace Tools;

/*
async def perform_action(
    self,
    action: str,
    coordinate: tuple[int, int] | None = None,
    text: str | None = None,
) -> tuple[int, int] | str | None:
    """Perform a specified automation action"""

    actions = {
        # Anthropic
        "key": lambda: text and self.press_key(text),
        "type": lambda: text and self.type_text(text),
        "mouse_move": lambda: coordinate and self.mouse_move(*coordinate),
        "left_click": self.left_click,
        "left_click_drag": lambda: coordinate
        and self.left_click_drag(*coordinate),
        "right_click": self.right_click,
        "middle_click": self.middle_click,
        "double_click": self.double_click,
        "screenshot": self.take_screenshot,
        "cursor_position": self.get_mouse_coordinates,
        # Additional
        "navigate": lambda: text and self.navigate(text),
        "refresh": self.refresh,
        "wait_for_load": self.wait_for_load,
    }

    ...

*/

alias RemoteBrowserAction = /** Press a key */

    | "key"
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
      "refresh"
    | /** Wait for the page to load */
      "wait_for_load";

/** The setup parameters for the remote browser */
model RemoteBrowserSetup {
    /** The connection URL for the remote browser */
    connect_url: string | null;

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
    /** The result of the action */
    result: unknown;
}

/** The integration definition for the remote browser */
model RemoteBrowserIntegrationDef extends BaseIntegrationDef {
    provider: "remote_browser" = "remote_browser";
    setup: RemoteBrowserSetup;
    method: "perform_action" = "perform_action";
    arguments: RemoteBrowserArguments;
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
