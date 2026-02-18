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

    def send_email(self, to_email: str, subject: str, body: str, from_email: str = None):
        sender = from_email or self.username
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            logger.info(f"Connecting to {self.server}:{self.port}...")
            # Office 365 / StartTLS flow
            with smtplib.SMTP(self.server, self.port) as server:
                server.ehlo()
                if server.has_extn('STARTTLS'):
                    logger.info("Starting TLS...")
                    server.starttls()
                    server.ehlo()
                
                logger.info(f"Authenticating as {self.username}...")
                server.login(self.username, self.password)
                
                logger.info(f"Sending email to {to_email}...")
                server.sendmail(sender, to_email, msg.as_string())
                logger.info("Email sent successfully.")
                return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise e
