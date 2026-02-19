import customtkinter as ctk
import threading
import smtplib
from email.mime.text import MIMEText
from src.mailer import EmailService # Reusing logging logic if possible, or implementing simple send

class AnonymousSMTPTester(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        # Header
        self.header = ctk.CTkLabel(self, text="Anonymous SMTP Test", font=("Roboto", 20, "bold"))
        self.header.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        # Warning
        self.warning = ctk.CTkLabel(self, text="⚠️ CAUTION: Only perform this test against your own servers.\nDo not use this to scan unauthorized open relays.", text_color="orange", font=("Roboto", 12))
        self.warning.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")

        # Configuration Frame
        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.config_frame.grid_columnconfigure((0, 1), weight=1)

        # Config Inputs (No User/Pass)
        self.server_entry = self.create_input(self.config_frame, "SMTP Server", "127.0.0.1", 0, 0)
        self.port_entry = self.create_input(self.config_frame, "Port", "25", 0, 1)

        # Email Content Frame
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.content_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.content_frame, text="From:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.from_entry = ctk.CTkEntry(self.content_frame, placeholder_text="sender@example.com")
        self.from_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.content_frame, text="To:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.to_entry = ctk.CTkEntry(self.content_frame, placeholder_text="recipient@example.com")
        self.to_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.content_frame, text="Subject:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.subject_entry = ctk.CTkEntry(self.content_frame, placeholder_text="Open Relay Test")
        self.subject_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.content_frame, text="Body:").grid(row=3, column=0, padx=10, pady=5, sticky="nw")
        self.body_entry = ctk.CTkTextbox(self.content_frame, height=100)
        self.body_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        self.body_entry.insert("0.0", "This is an anonymous SMTP test.")

        # Action Buttons
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.send_button = ctk.CTkButton(self.button_frame, text="Send Anonymous Email", command=self.start_send_thread, fg_color="#cc0000", hover_color="#a30000")
        self.send_button.pack(side="right")

        # Log Console
        self.log_label = ctk.CTkLabel(self, text="Execution Logs", anchor="w")
        self.log_label.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.log_console = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.log_console.grid(row=6, column=0, padx=20, pady=(5, 20), sticky="nsew")

    def create_input(self, parent, label_text, default_val, row, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text=label_text).pack(anchor="w")
        entry = ctk.CTkEntry(frame)
        entry.pack(fill="x")
        entry.insert(0, default_val)
        return entry

    def log(self, message):
        self.log_console.configure(state="normal")
        self.log_console.insert("end", message + "\n")
        self.log_console.see("end")
        self.log_console.configure(state="disabled")

    def start_send_thread(self):
        self.send_button.configure(state="disabled", text="Sending...")
        threading.Thread(target=self.send_email, daemon=True).start()

    def send_email(self):
        server = self.server_entry.get()
        try:
            port = int(self.port_entry.get())
        except ValueError:
             self.log("Error: Port must be a number.")
             self.send_button.configure(state="normal", text="Send Anonymous Email")
             return

        sender = self.from_entry.get()
        to_addr = self.to_entry.get()
        subject = self.subject_entry.get()
        body = self.body_entry.get("0.0", "end")

        self.log("-" * 40)
        self.log(f"Connecting to {server}:{port}...")

        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = to_addr

            # Direct SMTPlib usage for manual control
            with smtplib.SMTP(server, port, timeout=10) as smtp:
                smtp.set_debuglevel(0) # We handle logging
                self.log(f"Connected. EHLO response: {smtp.ehlo()}")
                
                # Check if TLS is available but don't force it? 
                # For anonymous tests, often we just want to see if it accepts
                if smtp.has_extn("STARTTLS"):
                     self.log("STARTTLS available, attempting switch...")
                     smtp.starttls()
                     self.log(f"TLS established. EHLO: {smtp.ehlo()}")
                else:
                    self.log("STARTTLS not supported by server.")

                self.log(f"Attempting to send mail from {sender} to {to_addr}...")
                smtp.sendmail(sender, [to_addr], msg.as_string())
                self.log("Success: Email accepted by server.")
                
        except Exception as e:
            self.log(f"Error: {str(e)}")
        finally:
            self.log("-" * 40)
            self.send_button.configure(state="normal", text="Send Anonymous Email")
