import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger("er-mailtool")

class EmailService:
    def __init__(self, server: str, port: int, username: str, password: str):
        self.server = server
        self.port = port
        self.username = username
        self.password = password

    def send_email(self, to_email: str, subject: str, body: str, from_email: str = None, callback=None):
        sender = from_email or self.username
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        def log(message: str, level: str = "INFO"):
            logger.log(getattr(logging, level), message)
            if callback:
                callback(f"[{level}] {message}")

        try:
            log(f"Connecting to {self.server}:{self.port}...")
            # Office 365 / StartTLS flow
            with smtplib.SMTP(self.server, self.port) as server:
                server.ehlo()
                if server.has_extn('STARTTLS'):
                    log("Starting TLS...")
                    server.starttls()
                    server.ehlo()
                
                log(f"Authenticating as {self.username}...")
                server.login(self.username, self.password)
                
                log(f"Sending email to {to_email}...")
                server.sendmail(sender, to_email, msg.as_string())
                log("Email sent successfully.")
                return True
        except Exception as e:
            log(f"Failed to send email: {e}", "ERROR")
            raise e
