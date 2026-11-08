import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class GmailDeliveryError(Exception):
    pass


def send_email(
    recipient: str,
    subject: str,
    body: str,
    html_body: str | None = None,
    logo_path: str | None = None,
) -> None:
    username = os.getenv("CAREERFORGE_SMTP_USER", "").strip()
    password = os.getenv("CAREERFORGE_SMTP_APP_PASSWORD", "").replace(" ", "")

    if not username or not password:
        raise GmailDeliveryError("CareerForge SMTP is not configured.")

    message = EmailMessage()
    message["From"] = formataddr(("CareerForge", username))
    message["To"] = recipient
    message["Subject"] = subject
    message["Auto-Submitted"] = "auto-generated"
    message.set_content(body)

    
    if html_body:
        message.add_alternative(html_body, subtype="html")

        if logo_path:
            path = Path(logo_path)

            if not path.is_absolute():
                path = Path(__file__).resolve().parents[4] / path

            if not path.is_file():
                raise GmailDeliveryError("Email logo file not found.")

            subtype = {
                ".png": "png",
                ".jpg": "jpeg",
                ".jpeg": "jpeg",
            }.get(path.suffix.lower())

            if subtype is None:
                raise GmailDeliveryError("Email logo must be PNG or JPEG.")

            if path.stat().st_size > 500_000:
                raise GmailDeliveryError("Email logo exceeds 500 KB.")

            message.get_payload()[-1].add_related(
                path.read_bytes(),
                maintype="image",
                subtype=subtype,
                cid="<careerforge-logo>",
                disposition="inline",
            )

    try:
        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=20,
            context=ssl.create_default_context(),
        ) as smtp:
            smtp.login(username, password)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise GmailDeliveryError(
            "CareerForge could not deliver the email."
        ) from exc
