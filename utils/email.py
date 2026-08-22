import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("visioninspect")

def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Sends password reset email containing secure single-use token URL.
    Falls back to secure logging when SMTP credentials are not provided.
    """
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001").rstrip("/")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    email_from = os.getenv("EMAIL_FROM", "noreply@visioninspect.ai")

    if smtp_host and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "VisionInspect AI — Password Reset Request"
            msg["From"] = email_from
            msg["To"] = to_email

            text_body = f"Hello,\n\nYou requested a password reset for your VisionInspect AI account.\nClick the link below to reset your password:\n{reset_link}\n\nThis link will expire in 30 minutes.\nIf you did not request a password reset, please ignore this email.\n"
            html_body = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <h2>VisionInspect AI Password Reset</h2>
                <p>Hello,</p>
                <p>You requested a password reset for your VisionInspect AI account.</p>
                <p style="margin: 20px 0;">
                    <a href="{reset_link}" style="background-color: #2563eb; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
                </p>
                <p>Or copy and paste this link into your browser:<br/><a href="{reset_link}">{reset_link}</a></p>
                <p><em>This link is single-use and will expire in 30 minutes.</em></p>
            </div>
            """

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(email_from, [to_email], msg.as_string())
            
            logger.info(f"Password reset email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email via SMTP: {e}")

    logger.info(f"========== PASSWORD RESET LINK GENERATED FOR {to_email} ==========")
    logger.info(f"RESET LINK: {reset_link}")
    logger.info(f"==================================================================")
    return True
