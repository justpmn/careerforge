
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.backend.app.core.config import settings


class EmailDeliveryError(RuntimeError):
    pass


def send_email(
    recipient: str,
    subject: str,
    content: str,
) -> None:
    mode = settings.email_delivery_mode.lower()

    if mode == "console":
        if not settings.debug:
            raise EmailDeliveryError(
                "Console email delivery requires debug mode."
            )

        print(
            f"\n--- CAREERFORGE DEVELOPMENT EMAIL ---\n"
            f"To: {recipient}\n"
            f"Subject: {subject}\n\n"
            f"{content}\n"
            f"--- END EMAIL ---\n",
            flush=True,
        )
        return

    if mode != "brevo":
        raise EmailDeliveryError("Unsupported email delivery mode.")

    if not settings.brevo_api_key or not settings.email_sender_address:
        raise EmailDeliveryError(
            "Brevo email configuration is incomplete."
        )

    payload = {
        "sender": {
            "name": settings.email_sender_name,
            "email": settings.email_sender_address,
        },
        "to": [{"email": recipient}],
        "subject": subject,
        "textContent": content,
    }

    request = Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-key": settings.brevo_api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            if response.status not in (200, 201, 202):
                raise EmailDeliveryError(
                    "Email provider rejected the message."
                )
    except (HTTPError, URLError, TimeoutError) as exc:
        raise EmailDeliveryError(
            "Could not submit email to the delivery provider."
        ) from exc


def send_verification_email(
    recipient: str,
    token: str,
) -> None:
    origin = settings.frontend_public_origin.rstrip("/")

    verification_url = (
        f"{origin}/verify-email?"
        f"{urlencode({'token': token})}"
    )

    content = (
        "Welcome to CareerForge!\n\n"
        "Verify your email address using the link below:\n\n"
        f"{verification_url}\n\n"
        "This link expires in 24 hours and can only be used once.\n\n"
        "If you did not create a CareerForge account, "
        "you can ignore this message."
    )

    send_email(
        recipient,
        "Verify your CareerForge email",
        content,
    )
