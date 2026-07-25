import smtplib
from email.message import EmailMessage

from app.config import settings

def send_otp_email(to_email: str, otp: str):
    """
    Sends an OTP to the given email address using Mailtrap.
    """
    msg = EmailMessage()
    msg['Subject'] = 'Your MediShield Temporary Password / OTP'
    msg['From'] = 'noreply@medishield.local'
    msg['To'] = to_email

    content = f"""
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    🏥  MediShield
                Secure Verification Code
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

            Hello,

            Your One-Time Password (OTP) is:

                    {otp}

            This code can be used to:

            • Sign in to your MediShield account for the first time.
            • Reset your account password if you requested a password reset.

            ⏳ Validity: 5 minutes

            For your security:
            • Do not share this OTP with anyone.
            • MediShield staff will never ask for your OTP.
            • If you did not request this code, you can safely ignore this email.

            Thank you,

            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            MediShield
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    msg.set_content(content)

    try:
        with smtplib.SMTP(settings.mailtrap_host, settings.mailtrap_port) as server:
            server.starttls()
            server.login(settings.mailtrap_user, settings.mailtrap_password)
            server.send_message(msg)
    except Exception as e:
        print("EMAIL ERROR:", e)
        raise e

def send_password_reset_otp_email(to_email: str, otp: str):
    """
    Sends a password reset OTP to the given email address.
    """
    msg = EmailMessage()
    msg['Subject'] = 'Your MediShield Password Reset Code'
    msg['From'] = 'noreply@medishield.local'
    msg['To'] = to_email

    content = f"""
    You requested a password reset for your MediShield account.
    
    Your password reset OTP is:
    {otp}
    
    This code is valid for 15 minutes. If you did not request a password reset, please ignore this email.
    """
    msg.set_content(content)

    try:
        with smtplib.SMTP(settings.mailtrap_host, settings.mailtrap_port) as server:
            server.starttls()
            server.login(settings.mailtrap_user, settings.mailtrap_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send reset email via Mailtrap: {e}")
