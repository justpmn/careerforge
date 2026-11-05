
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
import os
from src.backend.app.services.email_templates import render_email
from src.backend.app.services.gmail_sender import (GmailDeliveryError, send_email as gmail_send_email)
from src.backend.app.core.config import settings


class EmailDeliveryError(RuntimeError):
    pass



def send_branded_email(
    recipient: str,
    subject: str,
    body: str,
    html: str,
) -> None:
    try:
        gmail_send_email(
            recipient=recipient,
            subject=subject,
            body=body,
            html_body=html,
            logo_path=os.getenv("CAREERFORGE_EMAIL_LOGO_PATH") or None,
        )
    except GmailDeliveryError as exc:
        raise EmailDeliveryError(
            "CareerForge email delivery failed."
        ) from exc

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

    body = (
        "Welcome to CareerForge!\n\n"
        "Verify your email address:\n"
        f"{verification_url}\n\n"
        "If you didn't create this account, ignore this message."
    )

    html = render_email(
        title="One more step.",
        greeting="Welcome to CareerForge!",
        paragraphs=[
            "Thanks for joining CareerForge. Verify your email "
            "address to activate your account.",
            "If you didn't create this account, you can ignore this message.",
        ],
        button_label="Verify email address",
        button_url=verification_url,
        include_logo=bool(os.getenv("CAREERFORGE_EMAIL_LOGO_PATH")),
    )

    send_branded_email(
        recipient,
        "Verify your CareerForge account",
        body,
        html,
    )
def send_welcome_email(recipient: str, name: str) -> None:
    first_name = name.strip().split()[0] if name.strip() else "there"

    body = (
        f"Hey {first_name},\n\n"
        "Your CareerForge account is verified and ready.\n\n"
        "Build your profile, explore career recommendations, "
        "assess your skills, follow your roadmap and ask "
        "the AI Mentor for guidance.\n\n"
        "Make your next move count.\n\n"
        "The CareerForge Team"
    )

    html = render_email(
        title="Your next move starts here.",
        greeting=f"Hey {first_name},",
        paragraphs=[
            "Your email is verified. Welcome to CareerForge!",
            "Build your career profile, discover opportunities "
            "that match your skills, and follow a learning roadmap "
            "designed around your goals.",
            "Every career starts somewhere. Make your next move count.",
        ],
        include_logo=bool(os.getenv("CAREERFORGE_EMAIL_LOGO_PATH")),
    )

    send_branded_email(
        recipient,
        "Welcome to CareerForge!",
        body,
        html,
    )


def send_password_reset_email(recipient: str, token: str) -> None:
    from urllib.parse import quote

    origin = settings.frontend_public_origin.rstrip("/")
    link = f"{origin}/reset-password#token={quote(token, safe='')}"

    body = (
        "Reset your CareerForge password\n\n"
        "We received a request to reset your password.\n\n"
        f"Open this link to set a new password:\n{link}\n\n"
        "This link expires in 15 minutes and can only be used once.\n"
        "If you did not request this, ignore this message.\n\n"
        "The CareerForge Team"
    )

    html = render_email(
        title="Let's get you back in.",
        greeting="Forgot your password?",
        paragraphs=[
            "We received a request to reset your CareerForge password.",
            "Use the button below to choose a new password. "
            "This link expires in 15 minutes and can only be used once.",
            "If you did not request this, ignore the email.",
        ],
        button_label="Reset my password",
        button_url=link,
        include_logo=bool(os.getenv("CAREERFORGE_EMAIL_LOGO_PATH")),
    )

    send_branded_email(
        recipient,
        "Reset your CareerForge password",
        body,
        html,
    )


def send_password_changed_email(recipient: str) -> None:
    body = (
        "Your CareerForge password was changed successfully.\n\n"
        "If you made this change, no further action is needed.\n"
        "If you did not request it, secure your email account "
        "and contact CareerForge support.\n\n"
        "The CareerForge Team"
    )

    html = render_email(
        title="Your password was changed.",
        greeting="Account security update.",
        paragraphs=[
            "The password for your CareerForge account "
            "has been changed successfully.",
            "If you did not make this change, secure your email "
            "account and contact CareerForge support.",
        ],
        include_logo=bool(os.getenv("CAREERFORGE_EMAIL_LOGO_PATH")),
    )

    send_branded_email(
        recipient,
        "CareerForge password changed",
        body,
        html,
    )


def send_account_deletion_email(recipient: str, token: str) -> None:
    origin = settings.frontend_public_origin.rstrip("/")
    link = f"{origin}/delete-account#token={quote(token, safe='')}"

    body = (
        "CareerForge Account Deletion\n\n"
        "We received a request to permanently delete your account.\n\n"
        "Open this link to review and confirm deletion:\n"
        f"{link}\n\n"
        "This link expires in 10 minutes.\n"
        "Opening the link alone will not delete your account.\n\n"
        "If you did not request this, ignore this email.\n\n"
        "The CareerForge Team"
    )

    html = render_email(
        title="Confirm account deletion.",
        greeting="One last confirmation.",
        paragraphs=[
            "We received a request to permanently delete your "
            "CareerForge account.",
            "This link expires in 10 minutes. You must confirm "
            "the deletion on our website before anything is removed.",
            "If you did not request this, ignore this message.",
        ],
        button_label="Review deletion request",
        button_url=link,
        include_logo=bool(os.getenv("CAREERFORGE_EMAIL_LOGO_PATH")),
    )

    send_branded_email(
        recipient,
        "Confirm deletion of your CareerForge account",
        body,
        html,
    )
