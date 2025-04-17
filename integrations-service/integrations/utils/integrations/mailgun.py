import aiohttp
from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import MailgunSendEmailArguments, MailgunSetup
from ...env import mailgun_api_key  # Import env to access environment variables
from ...models import MailgunSendEmailOutput


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

    try:
        domain = arguments.from_.split("@")[-1]
    except Exception as e:
        raise Exception(f"Error splitting email domain: {e}")

    # Extract domain from from_ address (e.g. "test@example.com" -> "email.example.com")
    if not domain.startswith("email."):
        domain = "email." + domain

    # Use API key from env or from setup
    api_key = mailgun_api_key if setup.api_key == "DEMO_API_KEY" else setup.api_key

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
    if hasattr(arguments, "cc") and arguments.cc:
        data["cc"] = arguments.cc

    if hasattr(arguments, "bcc") and arguments.bcc:
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
