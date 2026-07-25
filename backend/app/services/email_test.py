import smtplib
from email.message import EmailMessage

sender = "MediShield <from@example.com>"
receiver = "Test User <to@example.com>"

msg = EmailMessage()
msg["Subject"] = "MediShield OTP Test"
msg["From"] = sender
msg["To"] = receiver

msg.set_content("""
Welcome to MediShield!

Your OTP is: 123456
""")

with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
    server.starttls()

    server.login(
        "b83bb11059c12e",
        "8f1e1f714416f9"
    )

    server.send_message(msg)

print("Email sent successfully")