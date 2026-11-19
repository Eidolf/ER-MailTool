import logging
import queue
import threading

import customtkinter as ctk

from src.connection_test import ConnectionSettings, test_connection

logger = logging.getLogger("er-mailtool")


class ConnectionTester(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.results = queue.Queue()

        ctk.CTkLabel(self, text="IMAP / SMTP Connection Test", font=("Roboto", 20, "bold")).grid(
            row=0, column=0, padx=20, pady=(20, 5), sticky="w"
        )
        ctk.CTkLabel(
            self,
            text=("Microsoft 365: IMAP im Postfach und SMTP AUTH für Benutzer/Tenant aktivieren. "
                  "OAuth2 wird bevorzugt; Basic Auth kann deaktiviert sein.\n"
                  "Netzwerkerfolg bedeutet keine erfolgreiche Anmeldung. Ohne Zugangsdaten nur Netzwerk testen.\n"
                  "Sicherheit 'None' überträgt Zugangsdaten unverschlüsselt."),
            justify="left", anchor="w", wraplength=800,
        ).grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        config = ctk.CTkFrame(self)
        config.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        for column in range(3):
            config.grid_columnconfigure(column, weight=1)
        self.imap_host = self._entry(config, "IMAP Host", "outlook.office365.com", 0, 0)
        self.imap_port = self._entry(config, "IMAP Port", "993", 0, 1)
        self.imap_security = self._security(config, "IMAP Sicherheit", "SSL/TLS", 0, 2)
        self.smtp_host = self._entry(config, "SMTP Host", "smtp.office365.com", 1, 0)
        self.smtp_port = self._entry(config, "SMTP Port", "587", 1, 1)
        self.smtp_security = self._security(config, "SMTP Sicherheit", "STARTTLS", 1, 2)
        self.username = self._entry(config, "Benutzername", "", 2, 0)
        self.password = self._entry(config, "Passwort", "", 2, 1, show="*")
        ctk.CTkButton(config, text="Microsoft 365 Vorgaben", command=self.set_m365).grid(
            row=2, column=2, padx=10, pady=10, sticky="s"
        )

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.imap_button = ctk.CTkButton(actions, text="IMAP testen", command=lambda: self.start("IMAP"))
        self.imap_button.pack(side="left", padx=(0, 10))
        self.smtp_button = ctk.CTkButton(actions, text="SMTP testen", command=lambda: self.start("SMTP"))
        self.smtp_button.pack(side="left")
        self.output = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.output.grid(row=4, column=0, padx=20, pady=(5, 20), sticky="nsew")

    def _entry(self, parent, label, value, row, column, show=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=column, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text=label).pack(anchor="w")
        entry = ctk.CTkEntry(frame, show=show)
        entry.pack(fill="x")
        entry.insert(0, value)
        return entry

    def _security(self, parent, label, value, row, column):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=column, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text=label).pack(anchor="w")
        menu = ctk.CTkOptionMenu(frame, values=["SSL/TLS", "STARTTLS", "None"])
        menu.set(value)
        menu.pack(fill="x")
        return menu

    def set_m365(self):
        for entry, value in ((self.imap_host, "outlook.office365.com"), (self.imap_port, "993"),
                             (self.smtp_host, "smtp.office365.com"), (self.smtp_port, "587")):
            entry.delete(0, "end")
            entry.insert(0, value)
        self.imap_security.set("SSL/TLS")
        self.smtp_security.set("STARTTLS")

    def _show(self, text):
        self.output.configure(state="normal")
        self.output.delete("0.0", "end")
        self.output.insert("end", text)
        self.output.configure(state="disabled")

    def start(self, protocol):
        host = self.imap_host.get() if protocol == "IMAP" else self.smtp_host.get()
        port = self.imap_port.get() if protocol == "IMAP" else self.smtp_port.get()
        security = self.imap_security.get() if protocol == "IMAP" else self.smtp_security.get()
        try:
            port = int(port)
        except ValueError:
            self._show("Eingabe [ERROR]: Der Port muss eine Zahl zwischen 1 und 65535 sein.")
            return
        settings = ConnectionSettings(protocol, host.strip(), port, security, self.username.get(), self.password.get())
        self.imap_button.configure(state="disabled")
        self.smtp_button.configure(state="disabled")
        self._show(f"{protocol}-Test läuft ...")
        threading.Thread(target=self._run, args=(settings,), daemon=True).start()
        self.after(100, self._poll)

    def _run(self, settings):
        try:
            checks = test_connection(settings)
            self.results.put("\n\n".join(f"{check.name} [{check.status}]\n{check.detail}" for check in checks))
        except Exception:
            logger.error("Unexpected connection test failure; no connection details logged")
            self.results.put("Test [ERROR]: Unerwarteter Fehler. Anwendungsprotokoll prüfen.")

    def _poll(self):
        try:
            result = self.results.get_nowait()
        except queue.Empty:
            self.after(100, self._poll)
            return
        self._show(result)
        self.imap_button.configure(state="normal")
        self.smtp_button.configure(state="normal")
