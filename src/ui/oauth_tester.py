import json
import os
import threading

import customtkinter as ctk

from src.oauth import OAuthTester


class OAuthHelpWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("OAuth 2.0 & Enterprise App Guide & Reference")
        self.geometry("750x650")
        self.attributes("-topmost", True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkLabel(
            self,
            text="📖 OAuth 2.0 Concepts, Standards & Field Mappings",
            font=("Roboto", 18, "bold")
        )
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Scrollable Content
        scroll_box = ctk.CTkScrollableFrame(self)
        scroll_box.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        scroll_box.grid_columnconfigure(0, weight=1)

        help_sections = [
            (
                "1. Authentication Types (Flows & Standards)",
                "• client_secret (OAuth 2.0 Client Credentials Grant - RFC 6749 Section 4.4):\n"
                "  Standard Flow für Machine-to-Machine / Daemon-Dienste (z. B. Enterprise App Registrierungen).\n"
                "  Verwendet die App-ID (Client ID) und das geheime Passwort (Client Secret).\n\n"
                "• jwt_bearer (RFC 7523 JWT Bearer Assertion Grant):\n"
                "  Erlaubt die Vorlage eines vorhandenen JWT-Tokens (Assertion) beim Token-Endpunkt, um ein Access Token zu erhalten "
                "(z. B. On-Behalf-Of Flow / SAML-to-JWT Federation).\n\n"
                "• client_assertion (RFC 7523 Client Credentials mit Zertifikat):\n"
                "  Statt eines statischen Client Secrets signiert der Dienst ein JWT mit einem privaten RSA-Schlüssel/Zertifikat "
                "(höchste Enterprise-Sicherheitsstufe ohne statische Passwörter)."
            ),
            (
                "2. Wichtige Standard-Endpunkte & URLs",
                "• Token Endpoint URL:\n"
                "  - Microsoft Entra ID (Azure AD): https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token\n"
                "  - Wenn im Feld 'Tenant ID' nur eine ID / Domain eingegeben wird, baut das Tool die URL automatisch zusammen.\n"
                "  - Benutzerdefinierte OAuth2-Server (Keycloak, Okta, Ping): Vollständige Token-URL direkt in das Feld eintragen.\n\n"
                "• Scopes & Permissions:\n"
                "  - Microsoft Graph (.default): https://graph.microsoft.com/.default\n"
                "  - Exchange SMTP / IMAP OAuth2: https://outlook.office365.com/.default\n"
                "  - Azure Management: https://management.azure.com/.default\n\n"
                "• SMTP Server & Port für OAuth2:\n"
                "  - Server: smtp.office365.com\n"
                "  - Port: 587 (STARTTLS)\n"
                "  - Auth-Methode: XOAUTH2 (SASL-Format: user=mailbox@domain.com\\x01auth=Bearer <token>\\x01\\x01)"
            ),
            (
                "3. Enterprise App Rollen vs. Delegierte Berechtigungen",
                "• 'roles' (Application Permissions):\n"
                "  Wird vergeben, wenn eine App ohne interaktiven Benutzer E-Mails versenden darf (z. B. 'Mail.Send' oder 'SMTP.SendAsApp').\n"
                "  Wird im Token unter dem Claim 'roles': ['Mail.Send'] zurückgegeben.\n\n"
                "• 'scp' (Delegated Scopes):\n"
                "  Wird vergeben, wenn sich ein Benutzer persönlich anmeldet und die App in seinem Namen handelt."
            ),
            (
                "4. Test E-Mail Versandmethoden",
                "• Microsoft Graph API sendMail:\n"
                "  Nutzt den REST-Endpunkt /v1.0/users/{mailbox}/sendMail. Erfordert 'Mail.Send' Application Permission im Tenant.\n\n"
                "• Exchange SMTP XOAUTH2:\n"
                "  Nutzt den SMTP-Port 587 mit modernem OAuth2-Handshake. Erfordert die Microsoft 365 Exchange-Berechtigung 'SMTP.SendAsApp'."
            )
        ]

        for i, (title, content) in enumerate(help_sections):
            frame = ctk.CTkFrame(scroll_box, fg_color="gray20", corner_radius=6)
            frame.grid(row=i, column=0, padx=5, pady=8, sticky="ew")
            frame.grid_columnconfigure(0, weight=1)

            t_lbl = ctk.CTkLabel(frame, text=title, font=("Roboto", 13, "bold"), text_color="#3399ff", anchor="w")
            t_lbl.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

            c_lbl = ctk.CTkLabel(frame, text=content, font=("Consolas", 11), justify="left", anchor="w")
            c_lbl.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")

        # Close Button
        btn_close = ctk.CTkButton(self, text="Schließen", command=self.destroy, width=120)
        btn_close.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="e")


class OAuthTesterView(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.last_access_token = None
        self.help_window = None

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        # Header Frame with Help Button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkLabel(header_frame, text="OAuth 2.0 & Enterprise App Tester", font=("Roboto", 20, "bold"))
        self.header.grid(row=0, column=0, sticky="w")

        self.btn_help = ctk.CTkButton(
            header_frame,
            text="❓ Hilfe & Erklärung",
            command=self.open_help_window,
            fg_color="#495057",
            hover_color="#343a40",
            width=150,
            height=30
        )
        self.btn_help.grid(row=0, column=1, sticky="e")

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

        ctk.CTkLabel(type_frame, text="Authentication Type (Grant Flow):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.auth_type_var = ctk.StringVar(value="client_secret")
        self.auth_type_menu = ctk.CTkOptionMenu(
            type_frame,
            values=[
                "client_secret (OAuth 2.0 Client Credentials)",
                "jwt_bearer (RFC 7523 Assertion Flow)",
                "client_assertion (Private Key / Cert JWT)"
            ],
            command=self.on_auth_type_change
        )
        self.auth_type_menu.grid(row=1, column=0, padx=5, pady=2, sticky="ew")

        ctk.CTkLabel(type_frame, text="Target Scope / Resource Preset:").grid(row=0, column=1, padx=5, pady=2, sticky="w")
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
            "Tenant ID / Domain (or Full Token URL)",
            os.getenv("AZURE_TENANT_ID", "common"),
            1, 0
        )
        self.client_id_entry = self.create_input(
            self.config_frame,
            "Client ID (Application Registration ID)",
            os.getenv("AZURE_CLIENT_ID", ""),
            1, 1
        )
        self.secret_entry = self.create_input(
            self.config_frame,
            "Client Secret (Password / Value)",
            os.getenv("AZURE_CLIENT_SECRET", ""),
            2, 0,
            show="*"
        )
        self.scope_entry = self.create_input(
            self.config_frame,
            "Scope (default: https://graph.microsoft.com/.default)",
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
            width=230,
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

        # Send Test Email via OAuth Frame
        self.mail_frame = ctk.CTkFrame(self)
        self.mail_frame.grid(row=5, column=0, padx=20, pady=5, sticky="ew")
        self.mail_frame.grid_columnconfigure((0, 1, 2), weight=1)

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
            values=["Microsoft Graph sendMail (Mail.Send)", "Custom / Exchange SMTP XOAUTH2"],
            command=self.on_mail_method_change,
            width=260
        )
        self.mail_method_menu.pack(side="right")

        # Custom SMTP Server Configuration (shown when SMTP XOAUTH2 is selected or custom preset)
        self.custom_smtp_frame = ctk.CTkFrame(self.mail_frame, fg_color="gray18", corner_radius=6)
        self.custom_smtp_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.custom_smtp_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.custom_smtp_host_entry = self.create_input(
            self.custom_smtp_frame,
            "SMTP Server Host",
            os.getenv("SMTP_SERVER", "smtp.office365.com"),
            0, 0
        )
        self.custom_smtp_port_entry = self.create_input(
            self.custom_smtp_frame,
            "Port (e.g. 587 or 465)",
            str(os.getenv("SMTP_PORT", "587")),
            0, 1
        )
        self.custom_smtp_tls_var = ctk.StringVar(value="STARTTLS")
        tls_frame = ctk.CTkFrame(self.custom_smtp_frame, fg_color="transparent")
        tls_frame.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tls_frame, text="Encryption / Security").pack(anchor="w")
        self.custom_smtp_tls_menu = ctk.CTkOptionMenu(
            tls_frame,
            values=["STARTTLS (Port 587)", "SSL/TLS (Port 465)", "Plain (None)"],
            variable=self.custom_smtp_tls_var
        )
        self.custom_smtp_tls_menu.pack(fill="x")

        # Hide custom SMTP frame by default (since Graph is default)
        self.custom_smtp_frame.grid_remove()

        # Mail Inputs
        self.mail_from_entry = self.create_input(
            self.mail_frame,
            "From (Sender Mailbox / User)",
            os.getenv("DEFAULT_SENDER", os.getenv("SMTP_USERNAME", "")),
            2, 0
        )
        self.mail_to_entry = self.create_input(
            self.mail_frame,
            "To (Recipient)",
            "",
            2, 1
        )
        self.mail_subject_entry = self.create_input(
            self.mail_frame,
            "Subject",
            "OAuth2 Enterprise App Test Email",
            2, 2
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
        self.btn_send_mail.grid(row=3, column=2, padx=10, pady=(0, 8), sticky="e")

        # Log Console
        self.log_console = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.log_console.grid(row=6, column=0, padx=20, pady=(5, 20), sticky="nsew")

    def open_help_window(self):
        if self.help_window is None or not self.help_window.winfo_exists():
            self.help_window = OAuthHelpWindow(self)
        else:
            self.help_window.focus()

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
            self.mail_method_menu.set("Microsoft Graph sendMail (Mail.Send)")
            self.on_mail_method_change("Microsoft Graph sendMail (Mail.Send)")
        elif "Exchange SMTP" in choice:
            self.scope_entry.delete(0, "end")
            self.scope_entry.insert(0, "https://outlook.office365.com/.default")
            self.mail_method_menu.set("Custom / Exchange SMTP XOAUTH2")
            self.on_mail_method_change("Custom / Exchange SMTP XOAUTH2")
            self.custom_smtp_host_entry.delete(0, "end")
            self.custom_smtp_host_entry.insert(0, "smtp.office365.com")
            self.custom_smtp_port_entry.delete(0, "end")
            self.custom_smtp_port_entry.insert(0, "587")
        elif "Azure Management" in choice:
            self.scope_entry.delete(0, "end")
            self.scope_entry.insert(0, "https://management.azure.com/.default")
        elif "Custom Scope" in choice:
            self.mail_method_menu.set("Custom / Exchange SMTP XOAUTH2")
            self.on_mail_method_change("Custom / Exchange SMTP XOAUTH2")

    def on_mail_method_change(self, choice):
        if "Microsoft Graph" in choice:
            self.mail_method_var.set("graph")
            self.custom_smtp_frame.grid_remove()
        else:
            self.mail_method_var.set("smtp_oauth2")
            self.custom_smtp_frame.grid()

    def log(self, message):
        """Thread-safe UI log update using Tkinter after callback."""
        def _append():
            try:
                self.log_console.configure(state="normal")
                self.log_console.insert("end", message + "\n")
                self.log_console.see("end")
                self.log_console.configure(state="disabled")
            except Exception:  # noqa: S110
                pass
        self.after(0, _append)

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

        def _update_ui():
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

        self.after(0, _update_ui)

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

        def _update_ui():
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

        self.after(0, _update_ui)

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
            smtp_host = self.custom_smtp_host_entry.get().strip() or "smtp.office365.com"
            try:
                smtp_port = int(self.custom_smtp_port_entry.get().strip())
            except ValueError:
                smtp_port = 587
            
            tls_choice = self.custom_smtp_tls_var.get()
            use_ssl = "SSL" in tls_choice or smtp_port == 465
            use_starttls = "STARTTLS" in tls_choice

            res = OAuthTester.send_email_smtp_oauth2(
                access_token=self.last_access_token,
                from_email=from_user,
                to_email=to_email,
                subject=subject,
                body=body,
                server=smtp_host,
                port=smtp_port,
                use_ssl=use_ssl,
                use_starttls=use_starttls
            )

        def _update_ui():
            if res.get("success"):
                self.log(f"✅ {res.get('message')} ({res.get('latency_ms', 0)} ms)")
            else:
                self.log(f"❌ Email sending failed (Status {res.get('status_code', 0)}): {res.get('error')}")
                if "raw_response" in res:
                    self.log(f"Details: {json.dumps(res.get('raw_response'), indent=2)}")

            self.log("-" * 60)
            self.btn_send_mail.configure(state="normal", text="📤 Send Test Email")

        self.after(0, _update_ui)

    def inspect_current_token(self):
        if not self.last_access_token:
            self.log("No token available.")
            return
        claims = OAuthTester.decode_jwt_unverified(self.last_access_token)
        self.log("-" * 60)
        self.log("JWT Claims Inspector:")
        self.log(json.dumps(claims, indent=2))
        self.log("-" * 60)

