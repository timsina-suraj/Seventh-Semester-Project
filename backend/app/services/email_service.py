import smtplib
from email.message import EmailMessage

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _send_email(msg: EmailMessage):
    """Shared SMTP sender. Blocking (smtplib has no async API) — callers
    dispatch these functions via FastAPI BackgroundTasks so they run after
    the response is sent, in Starlette's threadpool, without blocking the
    event loop (Module 13: notify asynchronously, after the DB commit)."""
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


def _dispatch(msg: EmailMessage, label: str):
    try:
        _send_email(msg)
    except Exception:
        logger.exception("Failed to send %s email to %s", label, msg["To"])


def send_registration_email(to_email: str):
    """Sent immediately on account creation (staff by Admin, patient by
    Receptionist) — separate from the later first-login OTP email."""
    msg = EmailMessage()
    msg["Subject"] = "Your MediShield account has been created"
    msg["From"] = "noreply@medishield.local"
    msg["To"] = to_email
    msg.set_content(f"""
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                🏥  MediShield
              Account Created
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        Hello,

        Your MediShield account has been created for {to_email}.

        To complete your first login, sign in with this same email
        address — you'll receive a one-time code (OTP) to verify it's you
        and set your password.

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Thanks,
        MediShield Team
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    _dispatch(msg, "registration")


def send_otp_email(to_email: str, otp: str):
    """First-login OTP — sent when a not-yet-activated account attempts to
    log in for the first time."""
    msg = EmailMessage()
    msg["Subject"] = "Your MediShield Login Code"
    msg["From"] = "noreply@medishield.local"
    msg["To"] = to_email
    msg.set_content(f"""
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                🏥  MediShield
            First-Time Login Verification
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        Hello,

        To log in for the first time, use this one-time password (OTP):

                {otp}

        This code is valid for {settings.otp_expire_minutes} minutes.

        After entering the OTP you will be asked to set a password.

        For your security:
        - Do not share this OTP with anyone.
        - MediShield staff will never ask for your OTP.
        - If you did not request this code, contact your system administrator.

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Thanks,
        MediShield Team
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    _dispatch(msg, "first-login OTP")


def send_appointment_booked_email(to_email: str, doctor_name: str, appointment_date: str, reason: str | None):
    """Module 13: sent right after AppointmentService.book() succeeds."""
    msg = EmailMessage()
    msg["Subject"] = "Your MediShield appointment is booked"
    msg["From"] = "noreply@medishield.local"
    msg["To"] = to_email
    msg.set_content(f"""
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                🏥  MediShield
              Appointment Booked
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        Hello,

        Your appointment with {doctor_name} has been booked for:

                {appointment_date}

        Reason: {reason or "Not specified"}
        Status: Pending confirmation

        You'll be notified again if the status changes.

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Thanks,
        MediShield Team
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    _dispatch(msg, "appointment booked")


def send_appointment_status_email(to_email: str, appointment_date: str, status: str):
    """Sent whenever an appointment's status changes (confirmed, completed,
    cancelled, no-show)."""
    msg = EmailMessage()
    msg["Subject"] = f"Your MediShield appointment is now {status}"
    msg["From"] = "noreply@medishield.local"
    msg["To"] = to_email
    msg.set_content(f"""
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                🏥  MediShield
              Appointment Update
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        Hello,

        Your appointment scheduled for {appointment_date} is now:

                {status}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Thanks,
        MediShield Team
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    _dispatch(msg, "appointment status update")


def send_lab_result_ready_email(to_email: str, test_name: str):
    """Sent once a lab technician uploads a result for a requested test."""
    msg = EmailMessage()
    msg["Subject"] = "Your MediShield lab result is ready"
    msg["From"] = "noreply@medishield.local"
    msg["To"] = to_email
    msg.set_content(f"""
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                🏥  MediShield
                Lab Result Ready
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        Hello,

        Your lab result for "{test_name}" is now available. Sign in to
        MediShield to view it, or ask your doctor for details.

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Thanks,
        MediShield Team
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    _dispatch(msg, "lab result ready")


def send_prescription_ready_email(to_email: str, doctor_name: str, medicine_count: int):
    """Sent once a doctor creates a prescription for a patient."""
    msg = EmailMessage()
    msg["Subject"] = "A new MediShield prescription has been issued"
    msg["From"] = "noreply@medishield.local"
    msg["To"] = to_email
    msg.set_content(f"""
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                🏥  MediShield
              Prescription Issued
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        Hello,

        {doctor_name} has issued you a new prescription with
        {medicine_count} medicine(s). Sign in to MediShield to view the
        full details.

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Thanks,
        MediShield Team
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    _dispatch(msg, "prescription ready")


def send_password_reset_otp_email(to_email: str, otp: str):
    """Sent via the Forgot Password flow (purpose='password_reset')."""
    msg = EmailMessage()
    msg["Subject"] = "Your MediShield Password Reset Code"
    msg["From"] = "noreply@medishield.local"
    msg["To"] = to_email
    msg.set_content(f"""
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                🏥  MediShield
              Password Reset Request
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        Hello,

        We received a request to reset your MediShield password.
        Your password reset code is:

                {otp}

        This code is valid for {settings.otp_expire_minutes} minutes.

        If you did not request a password reset, please ignore this email.
        Your password will remain unchanged.

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Thanks,
        MediShield Team
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    _dispatch(msg, "password reset OTP")
