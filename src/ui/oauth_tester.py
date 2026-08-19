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
            hover_color="#005999"
        )
        self.btn_test.pack(side="left", padx=(0, 10))

        self.btn_graph = ctk.CTkButton(
            self.btn_frame,
            text="🔍 Test MS Graph API",
            command=self.start_graph_thread,
            fg_color="#2b8a3e",
            hover_color="#237032",
            state="disabled"
        )
        self.btn_graph.pack(side="left", padx=(0, 10))

        self.btn_inspect = ctk.CTkButton(
            self.btn_frame,
            text="📋 Inspect Token Claims",
            command=self.inspect_current_token,
            fg_color="#495057",
            hover_color="#343a40",
            state="disabled"
        )
        self.btn_inspect.pack(side="left", padx=(0, 10))

        self.btn_clear = ctk.CTkButton(
            self.btn_frame,
            text="Clear Logs",
            command=self.clear_logs,
            fg_color="transparent",
            border_width=1,
            width=80
        )
        self.btn_clear.pack(side="right")

        # Log Console
        self.log_console = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.log_console.grid(row=5, column=0, padx=20, pady=(5, 20), sticky="nsew")

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
        else:
            self.last_access_token = None
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

    def inspect_current_token(self):
        if not self.last_access_token:
            self.log("No token available.")
            return
        claims = OAuthTester.decode_jwt_unverified(self.last_access_token)
        self.log("-" * 60)
        self.log("JWT Claims Inspector:")
        self.log(json.dumps(claims, indent=2))
        self.log("-" * 60)
