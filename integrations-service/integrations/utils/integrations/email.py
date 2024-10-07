from email.message import EmailMessage
from smtplib import SMTP

from beartype import beartype

from ...models import EmailArguments, EmailOutput, EmailSetup


# @beartype
async def send(
    setup: EmailSetup, arguments: EmailArguments
) -> EmailOutput:
    """
    Sends an email with the provided details.
    """

    message = EmailMessage()
    message.set_content(arguments.body)
    message["Subject"] = arguments.subject
    message["From"] = arguments.from_
    message["To"] = arguments.to

    with SMTP(setup.host, setup.port) as server:
        server.login(setup.user, setup.password)
        server.send_message(message)

    return EmailOutput(success=True)
