import customtkinter as ctk
import threading
import os
from src.mailer import EmailService

class SMTPTester(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # Header
        self.header = ctk.CTkLabel(self, text="SMTP Tester", font=("Roboto", 20, "bold"))
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Configuration Frame
        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.config_frame.grid_columnconfigure((0, 1), weight=1)

        # Config Inputs
        self.server_entry = self.create_input(self.config_frame, "SMTP Server", "smtp.office365.com", 0, 0)
        self.port_entry = self.create_input(self.config_frame, "Port", "587", 0, 1)
        # Use existing env logic
        self.user_entry = self.create_input(self.config_frame, "Username (Email)", os.getenv("SMTP_USERNAME", ""), 1, 0)
        self.pass_entry = self.create_input(self.config_frame, "Password", os.getenv("SMTP_PASSWORD", ""), 1, 1, show="*")

        # Email Content Frame
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.content_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.content_frame, text="To:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.to_entry = ctk.CTkEntry(self.content_frame, placeholder_text="recipient@example.com")
        self.to_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.content_frame, text="Subject:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.subject_entry = ctk.CTkEntry(self.content_frame, placeholder_text="Test Subject")
        self.subject_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.content_frame, text="Body:").grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        self.body_entry = ctk.CTkTextbox(self.content_frame, height=100)
        self.body_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.body_entry.insert("0.0", "This is a test email sent via ER-MailTool.")

        # Action Buttons
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.send_button = ctk.CTkButton(self.button_frame, text="Send Email", command=self.start_send_thread, fg_color="#0066cc", hover_color="#0052a3")
        self.send_button.pack(side="right")

        # Log Console
        self.log_label = ctk.CTkLabel(self, text="Execution Logs", anchor="w")
        self.log_label.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.log_console = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.log_console.grid(row=5, column=0, padx=20, pady=(5, 20), sticky="nsew")

    def create_input(self, parent, label_text, default_val, row, col, show=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text=label_text).pack(anchor="w")
        entry = ctk.CTkEntry(frame, show=show)
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
        port = int(self.port_entry.get())
        user = self.user_entry.get()
        password = self.pass_entry.get()
        
        to_addr = self.to_entry.get()
        subject = self.subject_entry.get()
        body = self.body_entry.get("0.0", "end")

        service = EmailService(server, port, user, password)
        
        try:
            self.log("-" * 40)
            service.send_email(to_addr, subject, body, callback=self.log)
            self.log("-" * 40)
        except Exception as e:
            pass # Error is already logged in callback
        finally:
            self.send_button.configure(state="normal", text="Send Email")
