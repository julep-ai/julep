import base64
import json
from functools import partial
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
    current_x: int
    current_y: int
    width: int | None
    height: int | None

    def __init__(
        self, browser: Browser, width: int | None = None, height: int | None = None
    ) -> None:
        self.browser = browser
        self.page = None
        self.context = None
        self.page = None
        self.current_x: int = 0
        self.current_y: int = 0
        self.mouse = None
        self.keyboard = None
        self.width, self.height = width, height

    async def initialize(self) -> None:
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0]
        self.mouse = self.page.mouse
        self.keyboard = self.page.keyboard

        if self.width and self.height:
            await self.set_screen_size(self.width, self.height)

        # Move mouse to center of screen
        await self.mouse_move(coordinate=(self.width // 2, self.height // 2))

    async def navigate(self, url: str) -> None:
        """Navigate to a specific URL"""
        await self.page.goto(url)

    async def refresh(self) -> None:
        """Refresh the current page"""
        await self.page.reload()

    async def wait_for_load(self, timeout: int = 30000) -> None:
        """Wait for document to be fully loaded"""
        await self.page.wait_for_load_state("domcontentloaded", timeout=timeout)

    async def execute_javascript(self, script: str, *args) -> Any:
        """Execute JavaScript code and return the result"""
        return await self.page.evaluate(script, *args)

    async def set_window_vars(self, variables: dict[str, Any]) -> None:
        """Set variables in the window scope"""
        json_str = json.dumps(variables)
        script = """
        const vars = JSON.parse(arguments[0]);
        for (const [key, value] of Object.entries(vars)) {
            window[key] = value;
        }
        """
        await self.execute_javascript(script, json_str)

    async def get_screen_size(self) -> tuple[int, int]:
        """Get the current browser viewport size"""

        viewport = self.page.viewport_size
        return (viewport["width"], viewport["height"])

    async def set_screen_size(self, width: int, height: int) -> None:
        """Set the current browser viewport size"""

        await self.page.set_viewport_size(dict(width=width, height=height))
        self.width, self.height = width, height

    async def get_element_coordinates(self, selector: str) -> tuple[int, int]:
        """Get the coordinates of an element"""
        element = await self.page.query_selector(selector)
        if element:
            box = await element.bounding_box()
            return (box["x"], box["y"])
        raise Exception(f"Element not found: {selector}")

    async def get_mouse_coordinates(self) -> tuple[int, int]:
        """Get current mouse coordinates"""
        return (self.current_x, self.current_y)

    async def press_key(self, key_combination: str) -> None:
        """Press a key or key combination"""
        # Split combination into individual keys
        keys = key_combination.split("+")

        # Press modifier keys first
        for key in keys[:-1]:
            await self.page.keyboard.down(key)

        # Press and release the last key
        await self.page.keyboard.press(keys[-1])

        # Release modifier keys in reverse order
        for key in reversed(keys[:-1]):
            await self.page.keyboard.up(key)

    async def type_text(self, text: str) -> None:
        """Type a string of text"""
        await self.page.keyboard.type(text)

    async def mouse_move(self, coordinate: tuple[int, int]) -> None:
        """Move mouse to specified coordinates"""
        await self.mouse.move(*coordinate)
        self.current_x, self.current_y = coordinate

    async def left_click(self) -> None:
        """Perform left mouse click"""
        await self.mouse.click(self.current_x, self.current_y)

    async def left_click_drag(self, coordinate: tuple[int, int]) -> None:
        """Click and drag to specified coordinates"""
        await self.mouse.down()
        await self.mouse.move(*coordinate)
        await self.mouse.up()

        self.current_x, self.current_y = coordinate

    async def right_click(self) -> None:
        """Perform right mouse click"""
        await self.mouse.click(self.current_x, self.current_y, button="right")

    async def middle_click(self) -> None:
        """Perform middle mouse click"""
        await self.mouse.click(self.current_x, self.current_y, button="middle")

    async def double_click(self) -> None:
        """Perform double click"""
        await self.mouse.dblclick(self.current_x, self.current_y)

    async def take_screenshot(self, filename: str | None = None) -> str | None:
        """Take a screenshot of the current browser window"""
        screenshot = await self.page.screenshot()

        x, y = await self.get_mouse_coordinates()
        screenshot = self.overlay_cursor(screenshot, x, y)

        if filename:
            with open(filename, "wb") as f:
                f.write(screenshot)
            return None

        encoded = base64.b64encode(screenshot).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    async def perform_action(
        self,
        action: str,
        coordinate: tuple[int, int] | None = None,
        text: str | None = None,
    ) -> tuple[int, int] | str | None:
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
                "cursor_position": self.get_mouse_coordinates,
                #
                # Additional
                "navigate": partial(self.navigate, text),
                "refresh": self.refresh,
                "wait_for_load": self.wait_for_load,
            }

            if action not in actions:
                raise ValueError(f"Invalid action: {action}")

            return await actions[action]()

        except Exception as e:
            raise Exception(f"Error performing action {action}: {str(e)}")

    def overlay_cursor(self, screenshot_bytes: bytes, x: int, y: int) -> bytes:
        """Overlay the cursor image on the screenshot at the specified coordinates."""
        # Load the screenshot from bytes
        screenshot = Image.open(BytesIO(screenshot_bytes)).convert("RGBA")

        # Load the cursor image
        cursor = Image.open(CURSOR_PATH.absolute()).convert("RGBA")

        # Create a copy of the screenshot to overlay the cursor
        combined = screenshot.copy()
        combined.paste(cursor, (x, y), cursor)

        # Save the combined image to bytes
        output = BytesIO()
        combined.save(output, format="PNG")
        return output.getvalue()


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def perform_action(
    setup: RemoteBrowserSetup, arguments: RemoteBrowserArguments
) -> RemoteBrowserOutput:
    async with async_playwright() as p:
        connect_url = setup.connect_url if setup.connect_url else arguments.connect_url
        browser = await p.chromium.connect_over_cdp(connect_url)

        automation = PlaywrightActions(browser, width=setup.width, height=setup.height)

        await automation.initialize()

        result = await automation.perform_action(
            action=arguments.action,
            coordinate=arguments.coordinate,
            text=arguments.text,
        )

        return RemoteBrowserOutput(result=result)
