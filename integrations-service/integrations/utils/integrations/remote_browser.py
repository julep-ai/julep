import base64
import json
from functools import partial, wraps
from io import BytesIO
from pathlib import Path
from typing import Any

from beartype import beartype
from PIL import Image
from playwright.async_api import (
    Browser,
    BrowserContext,
    Keyboard,
    Mouse,
    Page,
    PlaywrightContextManager,
    async_playwright,
)
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import RemoteBrowserArguments, RemoteBrowserSetup
from ...models import RemoteBrowserOutput

CURSOR_PATH = Path(__file__).parent / "assets" / "cursor-small.png"


class PlaywrightActions:
    """Class to handle browser automation actions using Playwright."""

    browser: Browser
    page: Page
    context: BrowserContext
    mouse: Mouse
    keyboard: Keyboard
    width: int | None
    height: int | None

    def __init__(
        self, browser: Browser, width: int | None = None, height: int | None = None
    ) -> None:
        self.browser = browser
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0]
        self.mouse = self.page.mouse
        self.keyboard = self.page.keyboard
        self.width, self.height = width, height

    async def _is_initialized(self) -> bool:
        """Check if the page is initialized"""
        result = bool(
            await self._execute_javascript("""
                window.$$julep$$_initialized
            """)
        )

        return result

    async def initialize(self, debug: bool = False) -> None:
        if debug:
            self.page.on("console", lambda msg: print(msg.text))

        if self.width and self.height:
            current_width, current_height = await self._get_screen_size()
            if current_width != self.width or current_height != self.height:
                await self._set_screen_size(self.width, self.height)

        # Install mouse move event listener
        init_script = """

        // Update mouse coordinates on mouse move
        // but only on the top document
        if (window === window.parent) 
            window.addEventListener(
                'DOMContentLoaded',
                () => {
                    const updateMouseCoordinates = (event) => {
                        window.mouseX = event.clientX;
                        window.mouseY = event.clientY;
                    };

                    if (!window.$$julep$$_mouseListenerInitialized) {
                        window.addEventListener('mousemove', updateMouseCoordinates);
                        window.addEventListener('mouseup', updateMouseCoordinates);
                        window.addEventListener('mousedown', updateMouseCoordinates);
                        window.addEventListener('click', updateMouseCoordinates);
                        window.addEventListener('dblclick', updateMouseCoordinates);

                        window.$$julep$$_mouseListenerInitialized = true;
                    }
                }
            );
        """
        await self.page.add_init_script(init_script)
        await self.page.evaluate(init_script)

        await self._reset_mouse()

    async def _reset_mouse(self) -> None:
        # Wait for the page to be fully loaded
        await self._wait_for_load()
        if not await self._is_initialized():
            await self.page.mouse.move(self.width // 2, self.height // 2)
            await self.page.evaluate("""
            window.$$julep$$_initialized = true;
            """)

    # @staticmethod
    # def _with_error_and_screenshot(f):
    #     @wraps(f)
    #     async def wrapper(self: "PlaywrightActions", *args, **kwargs):
    #         try:
    #             result: RemoteBrowserOutput = await f(self, *args, **kwargs)
    #             await self._wait_for_load()

    #             screenshot: RemoteBrowserOutput = await self.take_screenshot()

    #             return RemoteBrowserOutput(
    #                 output=result.output,
    #                 base64_image=screenshot.base64_image,
    #                 system=result.system or f.__name__,
    #             )

    #         except Exception as e:
    #             return RemoteBrowserOutput(error=str(e))

    #     return wrapper

    async def _get_screen_size(self) -> tuple[int, int]:
        """Get the current browser viewport size"""

        viewport: dict[str, int] | None = self.page.viewport_size
        if viewport is None:
            return (0, 0)

        return (viewport["width"], viewport["height"])

    async def _set_screen_size(self, width: int, height: int) -> None:
        """Set the current browser viewport size"""

        await self.page.set_viewport_size(dict(width=width, height=height))

    async def _wait_for_load(
        self, event: str = "domcontentloaded", timeout: int = 0
    ) -> None:
        """Wait for document to be fully loaded"""
        await self.page.wait_for_load_state(event, timeout=timeout)

    async def _execute_javascript(self, script: str, *args) -> Any:
        """Execute JavaScript code and return the result"""
        return await self.page.evaluate(script, *args)

    async def _set_window_vars(self, variables: dict[str, Any]) -> None:
        """Set variables in the window scope"""
        json_str = json.dumps(variables)
        script = """
        const vars = JSON.parse(arguments[0]);
        for (const [key, value] of Object.entries(vars)) {
            window[key] = value;
        }
        """
        await self._execute_javascript(script, json_str)

    async def _get_mouse_coordinates(self) -> tuple[int, int]:
        """Get current mouse coordinates"""
        result = await self._execute_javascript("""
        [window.mouseX, window.mouseY]
        """)

        return result[0], result[1]

    async def _get_element_coordinates(self, selector: str) -> tuple[int, int]:
        """Get the coordinates of an element"""
        element = await self.page.query_selector(selector)
        if element:
            box = await element.bounding_box()
            return (box["x"], box["y"])
        raise Exception(f"Element not found: {selector}")

    def _overlay_cursor(self, screenshot_bytes: bytes, x: int, y: int) -> bytes:
        """Overlay the cursor image on the screenshot at the specified coordinates."""
        # Load the screenshot from bytes
        screenshot = Image.open(BytesIO(screenshot_bytes)).convert("RGBA")

        # Load the cursor image
        cursor = Image.open(
            "./integrations/utils/integrations/assets/cursor-small.png"
        ).convert("RGBA")

        # Create a copy of the screenshot to overlay the cursor
        combined = screenshot.copy()
        combined.paste(cursor, (x, y), cursor)

        # Save the combined image to bytes
        output = BytesIO()
        combined.save(output, format="PNG")
        return output.getvalue()

    # ---
    # Actions

    async def navigate(self, url: str) -> RemoteBrowserOutput:
        """Navigate to a specific URL"""
        await self.page.goto(url)
        await self._reset_mouse()

        return RemoteBrowserOutput(
            output=url,
        )

    async def refresh(self) -> RemoteBrowserOutput:
        """Refresh the current page"""
        await self.page.reload()
        await self._reset_mouse()

        return RemoteBrowserOutput(
            output="Refreshed page",
        )

    async def cursor_position(self) -> RemoteBrowserOutput:
        """Get current mouse coordinates"""
        x, y = await self._get_mouse_coordinates()
        return RemoteBrowserOutput(
            output=f"X={x}, Y={y}",
        )

    async def press_key(self, key_combination: str) -> RemoteBrowserOutput:
        """Press a key or key combination"""
        # Split combination into individual keys
        keys = key_combination.split("+")
        keys = [
            "Enter"
            if k == "Return"
            else "Control"
            if k == "ctrl"
            else "PageDown"
            if k == "Page_Down"
            else k
            for k in keys
        ]

        # Press modifier keys first
        for key in keys[:-1]:
            await self.page.keyboard.down(key)

        # Press and release the last key
        await self.page.keyboard.press(keys[-1])

        # Release modifier keys in reverse order
        for key in reversed(keys[:-1]):
            await self.page.keyboard.up(key)

        return RemoteBrowserOutput(
            output=f"Pressed {key_combination}",
        )

    async def type_text(self, text: str) -> RemoteBrowserOutput:
        """Type a string of text"""
        await self.page.keyboard.type(text)

        return RemoteBrowserOutput(
            output=f"Typed {text}",
        )

    async def mouse_move(self, coordinate: tuple[int, int]) -> RemoteBrowserOutput:
        """Move mouse to specified coordinates"""
        await self.mouse.move(*coordinate)

        return RemoteBrowserOutput(
            output=f"Moved mouse to {coordinate}",
        )

    async def left_click(self) -> RemoteBrowserOutput:
        """Perform left mouse click"""
        x, y = await self._get_mouse_coordinates()
        await self.mouse.click(x, y)

        return RemoteBrowserOutput(
            output="Left clicked",
        )

    async def left_click_drag(self, coordinate: tuple[int, int]) -> RemoteBrowserOutput:
        """Click and drag to specified coordinates"""
        await self.mouse.down()
        await self.mouse.move(*coordinate)
        await self.mouse.up()

        return RemoteBrowserOutput(
            output=f"Left clicked and dragged to {coordinate}",
        )

    async def right_click(self) -> RemoteBrowserOutput:
        """Perform right mouse click"""
        x, y = await self._get_mouse_coordinates()
        await self.mouse.click(x, y, button="right")

        return RemoteBrowserOutput(
            output="Right clicked",
        )

    async def middle_click(self) -> RemoteBrowserOutput:
        """Perform middle mouse click"""
        x, y = await self._get_mouse_coordinates()
        await self.mouse.click(x, y, button="middle")

        return RemoteBrowserOutput(
            output="Middle clicked",
        )

    async def double_click(self) -> RemoteBrowserOutput:
        """Perform double click"""
        x, y = await self._get_mouse_coordinates()
        await self.mouse.dblclick(x, y)

        return RemoteBrowserOutput(
            output="Double clicked",
        )

    async def take_screenshot(self, filename: str | None = None) -> RemoteBrowserOutput:
        """Take a screenshot of the current browser window"""
        try:
            screenshot = await self.page.screenshot()
        except Exception as e:
            return RemoteBrowserOutput(error=str(e), system="take_screenshot")

        x, y = await self._get_mouse_coordinates()
        screenshot = self._overlay_cursor(screenshot, x, y)

        if filename:
            with open(filename, "wb") as f:
                f.write(screenshot)

        encoded = base64.b64encode(screenshot).decode("utf-8")

        return RemoteBrowserOutput(
            base64_image=f"data:image/png;base64,{encoded}",
            system="take_screenshot",
        )

    async def perform_action(
        self,
        action: str,
        coordinate: tuple[int, int] | None = None,
        text: str | None = None,
    ) -> RemoteBrowserOutput:
        """Perform a specified automation action"""
        try:
            actions = {
                # Anthropic
                "key": partial(self.press_key, text),
                "type": partial(self.type_text, text),
                "mouse_move": partial(self.mouse_move, coordinate),
                "left_click": self.left_click,
                "left_click_drag": partial(self.left_click_drag, coordinate),
                "right_click": self.right_click,
                "middle_click": self.middle_click,
                "double_click": self.double_click,
                "screenshot": self.take_screenshot,
                "cursor_position": self.cursor_position,
                #
                # Additional
                "navigate": partial(self.navigate, text),
                "refresh": self.refresh,
            }

            if action not in actions:
                raise ValueError(f"Invalid action: {action}")

            return await actions[action]()

        except Exception as e:
            raise Exception(f"Error performing action {action}: {str(e)}")


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def perform_action(
    setup: RemoteBrowserSetup, arguments: RemoteBrowserArguments
) -> RemoteBrowserOutput:
    p: PlaywrightContextManager = await async_playwright().start()
    connect_url = setup.connect_url if setup.connect_url else arguments.connect_url
    browser = await p.chromium.connect_over_cdp(connect_url)

    automation = PlaywrightActions(browser, width=setup.width, height=setup.height)

    await automation.initialize()

    return await automation.perform_action(
        action=arguments.action,
        coordinate=arguments.coordinate,
        text=arguments.text,
    )
