import re

import aiohttp
from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import MailgunSendEmailArguments, MailgunSetup
from ...models import MailgunSendEmailOutput


def validate_email(email: str) -> bool:
    """
    Validates an email address using a regex pattern.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_email_list(emails: str) -> bool:
    """
    Validates a comma-separated list of email addresses.
    """
    if not emails:
        return True

    for email in emails.split(","):
        email = email.strip()
        if email and not validate_email(email):
            return False
    return True


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(3),
)
async def send_email(
    setup: MailgunSetup, arguments: MailgunSendEmailArguments
) -> MailgunSendEmailOutput:
    """
    Sends an email with the provided details using the Mailgun API.
    """

    # Validate email addresses
    if not validate_email(arguments.from_):
        return MailgunSendEmailOutput(
            success=False, error=f"Invalid sender email address: {arguments.from_}"
        )

    if not validate_email(arguments.to):
        return MailgunSendEmailOutput(
            success=False, error=f"Invalid recipient email address: {arguments.to}"
        )

    if arguments.cc and not validate_email_list(arguments.cc):
        return MailgunSendEmailOutput(
            success=False, error=f"Invalid CC email address(es): {arguments.cc}"
        )

    if arguments.bcc and not validate_email_list(arguments.bcc):
        return MailgunSendEmailOutput(
            success=False, error=f"Invalid BCC email address(es): {arguments.bcc}"
        )

    domain = arguments.from_.split("@")[-1]

    # Extract domain from from_ address (e.g. "test@example.com" -> "email.example.com")
    if not domain.startswith("email."):
        domain = "email." + domain

    # Use API key from setup
    api_key = setup.api_key

    # API URL
    url = f"https://api.mailgun.net/v3/{domain}/messages"

    # Prepare payload
    data = {
        "from": arguments.from_,
        "to": arguments.to,
        "subject": arguments.subject,
        "text": arguments.body,
    }

    # Add CC and BCC if provided
    if arguments.cc:
        data["cc"] = arguments.cc

    if arguments.bcc:
        data["bcc"] = arguments.bcc

    # Make API request
    async with aiohttp.ClientSession() as session:
        auth = aiohttp.BasicAuth("api", api_key)
        async with session.post(url, data=data, auth=auth) as response:
            if response.status in (200, 201, 202):
                return MailgunSendEmailOutput(success=True)
            error_text = await response.text()
            return MailgunSendEmailOutput(
                success=False, error=f"Email was not sent successfully: {error_text}"
            )
