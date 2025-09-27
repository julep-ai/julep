import asyncio
from email.message import EmailMessage
from smtplib import SMTP

import aiosmtplib
from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import EmailArguments, EmailSetup
from ...models import EmailOutput


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def send(setup: EmailSetup, arguments: EmailArguments) -> EmailOutput:
    """
    Sends an email with the provided details using async SMTP.
    """
    # AIDEV-NOTE: Using aiosmtplib for async email sending to prevent timeout issues

    message = EmailMessage()
    # AIDEV-NOTE: Enhanced HTML detection and proper charset setting for HTML emails
    # Check if body contains HTML tags to determine content type
    html_indicators = [
        "<html",
        "<body",
        "<div",
        "<p>",
        "<br",
        "<table",
        "<h1",
        "<h2",
        "<h3",
        "<h4",
        "<h5",
        "<h6",
        "<span",
        "<a href=",
    ]
    is_html = arguments.body and any(
        indicator in arguments.body.lower() for indicator in html_indicators
    )

    if is_html:
        # Set HTML content with UTF-8 charset for better international character support
        message.set_content(arguments.body, subtype="html", charset="utf-8")
    else:
        # Plain text content with UTF-8 charset
        message.set_content(arguments.body, charset="utf-8")

    message["Subject"] = arguments.subject
    message["From"] = arguments.from_
    message["To"] = arguments.to

    try:
        # Use aiosmtplib for async SMTP operations
        await aiosmtplib.send(
            message,
            hostname=setup.host,
            port=setup.port,
            username=setup.user,
            password=setup.password,
            start_tls=True,  # Use STARTTLS for port 587
        )
        return EmailOutput(success=True)
    except Exception:
        # If aiosmtplib fails, fall back to sync SMTP in thread pool
        loop = asyncio.get_event_loop()

        def send_sync():
            with SMTP(setup.host, setup.port) as server:
                server.starttls()  # Enable TLS for port 587
                server.login(setup.user, setup.password)
                server.send_message(message)

        await loop.run_in_executor(None, send_sync)
        return EmailOutput(success=True)
