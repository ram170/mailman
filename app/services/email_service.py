import smtplib
from email.message import EmailMessage

from app.config import settings


class EmailService:

    def send_address_review_email(
        self,
        order_id: int,
        order_name: str | None,
        address: str,
        reason: str,
    ) -> None:
        message = EmailMessage()

        message["Subject"] = f"Address review required - {order_name or order_id}"
        message["From"] = settings.smtp_username
        message["To"] = settings.review_email

        message.set_content(
            f"""
Order requires manual address verification.

Order ID: {order_id}
Order: {order_name}

Address:
{address}

Reason:
{reason}
"""
        )

        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
        ) as smtp:
            smtp.starttls()

            smtp.login(
                settings.smtp_username,
                settings.smtp_password,
            )

            smtp.send_message(message)