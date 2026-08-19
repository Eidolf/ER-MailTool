import json
import os
import threading

import customtkinter as ctk

from src.oauth import OAuthTester


class OAuthTesterView(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.last_access_token = None

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # Header
        self.header = ctk.CTkLabel(self, text="OAuth 2.0 & Enterprise App Tester", font=("Roboto", 20, "bold"))
        self.header.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        self.sub_header = ctk.CTkLabel(
            self,
            text="Verify Microsoft Entra ID / Azure AD Enterprise App registrations, Client Credentials & JWT Bearer flows.",
            font=("Roboto", 12),
            text_color="gray70"
        )
        self.sub_header.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")

        # Configuration Frame
        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        self.config_frame.grid_columnconfigure((0, 1), weight=1)

        # Auth Type & Preset Selection
        type_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        type_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        type_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(type_frame, text="Authentication Type:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.auth_type_var = ctk.StringVar(value="client_secret")
        self.auth_type_menu = ctk.CTkOptionMenu(
            type_frame,
            values=["client_secret (Client Credentials)", "jwt_bearer (RFC 7523 Assertion)", "client_assertion (Private Key / Cert JWT)"],
            command=self.on_auth_type_change
        )
        self.auth_type_menu.grid(row=1, column=0, padx=5, pady=2, sticky="ew")

        ctk.CTkLabel(type_frame, text="Preset / Target Scope:").grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.preset_menu = ctk.CTkOptionMenu(
            type_frame,
            values=[
                "Entra ID - Microsoft Graph (.default)",
                "Office 365 Exchange SMTP / IMAP OAuth2",
                "Azure Management API",
                "Custom Scope / Token URL"
            ],
            command=self.on_preset_change
        )
        self.preset_menu.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        # Inputs
        self.tenant_entry = self.create_input(
            self.config_frame,
            "Tenant ID / Domain / Custom Token URL",
            os.getenv("AZURE_TENANT_ID", "common"),
            1, 0
        )
        self.client_id_entry = self.create_input(
            self.config_frame,
            "Client ID (App / Registration ID)",
            os.getenv("AZURE_CLIENT_ID", ""),
            1, 1
        )
        self.secret_entry = self.create_input(
            self.config_frame,
            "Client Secret / Password",
            os.getenv("AZURE_CLIENT_SECRET", ""),
            2, 0,
            show="*"
        )
        self.scope_entry = self.create_input(
            self.config_frame,
            "Scope (e.g. https://graph.microsoft.com/.default)",
            "https://graph.microsoft.com/.default",
            2, 1
        )

        # JWT Assertion Frame (for JWT Bearer / Client Assertion)
        self.assertion_frame = ctk.CTkFrame(self)
        self.assertion_frame.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.assertion_frame.grid_columnconfigure(0, weight=1)

        self.assertion_label = ctk.CTkLabel(self.assertion_frame, text="JWT Assertion / Signed Client JWT Token:")
        self.assertion_label.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="w")

        self.assertion_box = ctk.CTkTextbox(self.assertion_frame, height=70, font=("Consolas", 11))
        self.assertion_box.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")
        self.assertion_box.insert("0.0", "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...")

        # Action Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        self.btn_test = ctk.CTkButton(
            self.btn_frame,
            text="🚀 Test OAuth & Fetch Token",
            command=self.start_test_thread,
            fg_color="#007acc",
            hover_color="#005999",
            width=220,
            height=36,
            font=("Roboto", 13, "bold")
        )
        self.btn_test.pack(side="left", padx=(0, 10))

        self.btn_graph = ctk.CTkButton(
            self.btn_frame,
            text="🔍 Test MS Graph API",
            command=self.start_graph_thread,
            fg_color="#2b8a3e",
            hover_color="#237032",
            height=36,
            state="disabled"
        )
        self.btn_graph.pack(side="left", padx=(0, 10))

        self.btn_inspect = ctk.CTkButton(
            self.btn_frame,
            text="📋 Inspect Token Claims",
            command=self.inspect_current_token,
            fg_color="#495057",
            hover_color="#343a40",
            height=36,
            state="disabled"
        )
        self.btn_inspect.pack(side="left", padx=(0, 10))

        self.btn_clear = ctk.CTkButton(
            self.btn_frame,
            text="Clear Logs",
            command=self.clear_logs,
            fg_color="transparent",
            border_width=1,
            height=36,
            width=90
        )
        self.btn_clear.pack(side="right")

        # Send Test Email via OAuth (Graph / SMTP XOAUTH2) Frame
        self.mail_frame = ctk.CTkFrame(self)
        self.mail_frame.grid(row=5, column=0, padx=20, pady=5, sticky="ew")
        self.mail_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Mail header & method selection
        mail_header_frame = ctk.CTkFrame(self.mail_frame, fg_color="transparent")
        mail_header_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=(5, 2), sticky="ew")
        
        ctk.CTkLabel(
            mail_header_frame,
            text="✉️ Send Test Email with Acquired OAuth2 Token:",
            font=("Roboto", 12, "bold")
        ).pack(side="left")

        self.mail_method_var = ctk.StringVar(value="graph")
        self.mail_method_menu = ctk.CTkOptionMenu(
            mail_header_frame,
            values=["Microsoft Graph sendMail (Mail.Send)", "Exchange SMTP XOAUTH2 (Port 587)"],
            command=self.on_mail_method_change,
            width=260
        )
        self.mail_method_menu.pack(side="right")

        # Mail Inputs
        self.mail_from_entry = self.create_input(
            self.mail_frame,
            "From (Sender Mailbox / User)",
            os.getenv("DEFAULT_SENDER", os.getenv("SMTP_USERNAME", "")),
            1, 0
        )
        self.mail_to_entry = self.create_input(
            self.mail_frame,
            "To (Recipient)",
            "",
            1, 1
        )
        self.mail_subject_entry = self.create_input(
            self.mail_frame,
            "Subject",
            "OAuth2 Enterprise App Test Email",
            1, 2
        )

        # Send Button
        self.btn_send_mail = ctk.CTkButton(
            self.mail_frame,
            text="📤 Send Test Email",
            command=self.start_send_mail_thread,
            fg_color="#107c41",
            hover_color="#0b5a2f",
            height=32,
            font=("Roboto", 12, "bold"),
            state="disabled"
        )
        self.btn_send_mail.grid(row=2, column=2, padx=10, pady=(0, 8), sticky="e")

        # Log Console
        self.log_console = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.log_console.grid(row=6, column=0, padx=20, pady=(5, 20), sticky="nsew")

    def create_input(self, parent, label_text, default_val, row, col, show=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text=label_text).pack(anchor="w")
        entry = ctk.CTkEntry(frame, show=show)
        entry.pack(fill="x")
        if default_val:
            entry.insert(0, default_val)
        return entry

    def on_auth_type_change(self, choice):
        if "client_secret" in choice:
            self.auth_type_var.set("client_secret")
        elif "jwt_bearer" in choice:
            self.auth_type_var.set("jwt_bearer")
        elif "client_assertion" in choice:
            self.auth_type_var.set("client_assertion")

    def on_preset_change(self, choice):
        if "Microsoft Graph" in choice:
            self.scope_entry.delete(0, "end")
            self.scope_entry.insert(0, "https://graph.microsoft.com/.default")
        elif "Exchange SMTP" in choice:
            self.scope_entry.delete(0, "end")
            self.scope_entry.insert(0, "https://outlook.office365.com/.default")
        elif "Azure Management" in choice:
            self.scope_entry.delete(0, "end")
            self.scope_entry.insert(0, "https://management.azure.com/.default")

    def on_mail_method_change(self, choice):
        if "Microsoft Graph" in choice:
            self.mail_method_var.set("graph")
        else:
            self.mail_method_var.set("smtp_oauth2")

    def log(self, message):
        self.log_console.configure(state="normal")
        self.log_console.insert("end", message + "\n")
        self.log_console.see("end")
        self.log_console.configure(state="disabled")

    def clear_logs(self):
        self.log_console.configure(state="normal")
        self.log_console.delete("0.0", "end")
        self.log_console.configure(state="disabled")

    def start_test_thread(self):
        self.btn_test.configure(state="disabled", text="Testing...")
        threading.Thread(target=self.run_test, daemon=True).start()

    def run_test(self):
        tenant = self.tenant_entry.get().strip()
        client_id = self.client_id_entry.get().strip()
        client_secret = self.secret_entry.get().strip()
        scope = self.scope_entry.get().strip()
        auth_type = self.auth_type_var.get()
        assertion = self.assertion_box.get("0.0", "end").strip()

        self.log("=" * 60)
        self.log(f"Starting OAuth 2.0 Auth Test ({auth_type})")
        self.log(f"Target / Tenant: {tenant}")
        self.log(f"Client ID: {client_id}")
        self.log(f"Scope: {scope}")
        self.log("-" * 60)

        res = OAuthTester.test_oauth_auth(
            tenant_or_token_url=tenant,
            client_id=client_id,
            auth_type=auth_type,
            client_secret=client_secret if client_secret else None,
            assertion=assertion if assertion else None,
            scope=scope
        )

        if res.get("success"):
            self.last_access_token = res.get("access_token")
            self.log(f"✅ [SUCCESS] Token Acquired! (HTTP {res.get('status_code')}, {res.get('latency_ms')} ms)")
            self.log(f"Token Type: {res.get('token_type')}")
            self.log(f"Expires In: {res.get('expires_in')}s")
            
            claims = res.get("claims")
            if claims and "payload" in claims:
                payload = claims["payload"]
                self.log(f"App ID (appid): {payload.get('appid', payload.get('azp', 'N/A'))}")
                self.log(f"Tenant (tid): {payload.get('tid', 'N/A')}")
                self.log(f"Audience (aud): {payload.get('aud', 'N/A')}")
                self.log(f"Roles / App Permissions: {payload.get('roles', 'None')}")
                self.log(f"Scopes: {payload.get('scp', res.get('scope_granted', 'N/A'))}")

            self.btn_graph.configure(state="normal")
            self.btn_inspect.configure(state="normal")
            self.btn_send_mail.configure(state="normal")
        else:
            self.last_access_token = None
            self.btn_send_mail.configure(state="disabled")
            self.log(f"❌ [FAILED] HTTP {res.get('status_code')} ({res.get('latency_ms', 0)} ms)")
            self.log(f"Error: {res.get('error')}")
            self.log(f"Description: {res.get('error_description')}")
            if "raw_response" in res:
                self.log(f"Raw Response: {json.dumps(res['raw_response'], indent=2)}")

        self.log("=" * 60)
        self.btn_test.configure(state="normal", text="🚀 Test OAuth & Fetch Token")

    def start_graph_thread(self):
        if not self.last_access_token:
            self.log("No active access token to test MS Graph.")
            return
        self.btn_graph.configure(state="disabled", text="Testing Graph...")
        threading.Thread(target=self.run_graph_test, daemon=True).start()

    def run_graph_test(self):
        self.log("-" * 60)
        self.log("Testing token against Microsoft Graph API (/v1.0/organization)...")
        res = OAuthTester.test_microsoft_graph_api(self.last_access_token)
        if res.get("success"):
            self.log(f"✅ Microsoft Graph API Call Succeeded (HTTP {res.get('status_code')})")
            self.log(f"Organization Data: {json.dumps(res.get('data'), indent=2)}")
        else:
            self.log(f"❌ Microsoft Graph Call Failed (HTTP {res.get('status_code')})")
            self.log(f"Error: {res.get('error')}")
            if "raw_response" in res:
                self.log(f"Details: {json.dumps(res.get('raw_response'), indent=2)}")
        self.log("-" * 60)
        self.btn_graph.configure(state="normal", text="🔍 Test MS Graph API")

    def start_send_mail_thread(self):
        if not self.last_access_token:
            self.log("❌ No active access token. Please run 'Test OAuth & Fetch Token' first.")
            return
        self.btn_send_mail.configure(state="disabled", text="Sending...")
        threading.Thread(target=self.run_send_mail, daemon=True).start()

    def run_send_mail(self):
        from_user = self.mail_from_entry.get().strip()
        to_email = self.mail_to_entry.get().strip()
        subject = self.mail_subject_entry.get().strip()
        method = self.mail_method_var.get()
        body = (
            "Hello,\n\n"
            "This is a test email sent via ER-MailTool using authenticated OAuth 2.0 credentials "
            "(Microsoft Entra ID Enterprise App Registration).\n\n"
            "Status: Successful verification."
        )

        self.log("-" * 60)
        self.log(f"Sending test email via {method.upper()}...")
        self.log(f"From: {from_user}")
        self.log(f"To: {to_email}")
        self.log(f"Subject: {subject}")

        if method == "graph":
            res = OAuthTester.send_email_graph(
                access_token=self.last_access_token,
                from_user=from_user,
                to_email=to_email,
                subject=subject,
                body=body
            )
        else:
            res = OAuthTester.send_email_smtp_oauth2(
                access_token=self.last_access_token,
                from_email=from_user,
                to_email=to_email,
                subject=subject,
                body=body
            )

        if res.get("success"):
            self.log(f"✅ {res.get('message')} ({res.get('latency_ms', 0)} ms)")
        else:
            self.log(f"❌ Email sending failed (Status {res.get('status_code', 0)}): {res.get('error')}")
            if "raw_response" in res:
                self.log(f"Details: {json.dumps(res.get('raw_response'), indent=2)}")

        self.log("-" * 60)
        self.btn_send_mail.configure(state="normal", text="📤 Send Test Email")

    def inspect_current_token(self):
        if not self.last_access_token:
            self.log("No token available.")
            return
        claims = OAuthTester.decode_jwt_unverified(self.last_access_token)
        self.log("-" * 60)
        self.log("JWT Claims Inspector:")
        self.log(json.dumps(claims, indent=2))
        self.log("-" * 60)
