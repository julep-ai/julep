from email.message import EmailMessage
from smtplib import SMTP

from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import EmailArguments, EmailSetup
from ...env import mailgun_password  # Import env to access environment variables
from ...models import EmailOutput


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def send(setup: EmailSetup, arguments: EmailArguments) -> EmailOutput:
    """
    Sends an email with the provided details.
    """

    message = EmailMessage()
    message.set_content(arguments.body)
    message["Subject"] = arguments.subject
    message["From"] = arguments.from_
    message["To"] = arguments.to

    if setup.password == "DEMO_PASSWORD":
        setup.password = mailgun_password

    with SMTP(setup.host, setup.port) as server:
        server.login(setup.user, setup.password)
        server.send_message(message)

    return EmailOutput(success=True)
