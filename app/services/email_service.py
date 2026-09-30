import smtplib
from email.message import EmailMessage

from app.config import settings


class EmailService:

    def send_address_validation_email(
        self,
        order_id: int,
        order_name: str | None,
        original_address: str,
        validation_result: dict,
    ) -> None:
        status = validation_result.get("status", "unknown")
        validated_address = validation_result.get("validated_address")
        failed_checks = validation_result.get("failed_checks", [])

        failed_checks_text = (
            "\n".join(f"- {check}" for check in failed_checks)
            if failed_checks
            else "None"
        )

        message = EmailMessage()

        message["Subject"] = (
            f"Address validation {status.upper()} - "
            f"{order_name or order_id}"
        )

        recipients = [
                    email.strip()
                    for email in settings.review_emails.split(",")
                    if email.strip()
                ]

        message["From"] = settings.smtp_username
        message["To"] = ", ".join(recipients)

        message.set_content(
            f"""
Order ID: {order_id}
Order: {order_name}

Original address:
{original_address}

Validated address:
{validated_address or "Not available"}

Decision:
{status.upper()}

Failed checks:
{failed_checks_text}
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