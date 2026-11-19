"""Network and mail protocol diagnostics without sending a message."""

import errno
import imaplib
import smtplib
import socket
import ssl
import time
from dataclasses import dataclass, field
from typing import Literal

Security = Literal["SSL/TLS", "STARTTLS", "None"]
Protocol = Literal["IMAP", "SMTP"]


@dataclass(frozen=True)
class ConnectionSettings:
    protocol: Protocol
    host: str
    port: int
    security: Security
    username: str = ""
    password: str = field(default="", repr=False)


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def _network_check(settings: ConnectionSettings, timeout: float) -> tuple[list[Check], bool]:
    try:
        addresses = socket.getaddrinfo(settings.host, settings.port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return [Check("DNS", "ERROR", "Name konnte nicht aufgelöst werden. Hostname und DNS prüfen.")], False
    if not addresses:
        return [Check("DNS", "ERROR", "Keine IPv4- oder IPv6-Adresse gefunden. DNS prüfen.")], False

    ips = list(dict.fromkeys(item[4][0] for item in addresses))
    checks = [Check("DNS", "OK", ", ".join(ips))]
    errors = []
    started = time.monotonic()
    deadline = started + timeout
    for family, socktype, proto, _, address in addresses:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            errors.append("timeout")
            break
        try:
            with socket.socket(family, socktype, proto) as connection:
                connection.settimeout(remaining)
                connection.connect(address)
            elapsed = (time.monotonic() - started) * 1000
            checks.append(Check("TCP", "OK", f"{settings.host}:{settings.port} ({elapsed:.0f} ms; {address[0]})"))
            return checks, True
        except (TimeoutError, socket.timeout):
            errors.append("timeout")
        except OSError as exc:
            errors.append("refused" if exc.errno == errno.ECONNREFUSED else "unreachable")

    if "timeout" in errors:
        detail = "Zeitüberschreitung. Firewall, Providerfilter und Erreichbarkeit des Zielports prüfen."
    elif "refused" in errors:
        detail = "Verbindung aktiv abgelehnt. Port, Dienst und Firewall-Regeln prüfen."
    else:
        detail = "Ziel nicht erreichbar. Netzwerkroute, Server und Firewall prüfen."
    checks.append(Check("TCP", "ERROR", detail))
    return checks, False


def _text(value: bytes | str) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _smtp(settings: ConnectionSettings, checks: list[Check], timeout: float) -> None:
    context = ssl.create_default_context()
    client = None
    stage = "Protokoll"
    try:
        cls = smtplib.SMTP_SSL if settings.security == "SSL/TLS" else smtplib.SMTP
        kwargs = {"timeout": timeout}
        if settings.security == "SSL/TLS":
            kwargs["context"] = context
        stage = "TLS" if settings.security == "SSL/TLS" else "Protokoll"
        client = cls(settings.host, settings.port, **kwargs)
        if settings.security == "SSL/TLS":
            checks.append(Check("TLS", "OK", "Zertifikat und TLS-Handshake erfolgreich geprüft."))
        stage = "EHLO"
        code, response = client.ehlo()
        if code != 250:
            checks.append(Check("EHLO", "ERROR", f"Server hat EHLO abgelehnt (Code {code})."))
            return
        checks.append(Check("EHLO", "OK", _text(response)))
        if settings.security == "STARTTLS":
            stage = "STARTTLS"
            if not client.has_extn("starttls"):
                checks.append(Check(stage, "ERROR", "Server bietet STARTTLS nicht an. Port und TLS-Modus prüfen."))
                return
            client.starttls(context=context)
            checks.append(Check(stage, "OK", "Zertifikat und TLS-Handshake erfolgreich geprüft."))
            stage = "EHLO"
            code, response = client.ehlo()
            if code != 250:
                checks.append(Check(stage, "ERROR", f"EHLO nach STARTTLS abgelehnt (Code {code})."))
                return
            checks.append(Check("EHLO nach TLS", "OK", _text(response)))
        elif settings.security == "None":
            checks.append(Check("TLS", "WARN", "Unverschlüsselte Verbindung; Zugangsdaten sind lesbar."))
        methods = client.esmtp_features.get("auth", "").strip()
        checks.append(Check("SMTP AUTH", "INFO", methods or "Keine Verfahren angekündigt."))
        if settings.username:
            stage = "Authentifizierung"
            client.login(settings.username, settings.password)
            checks.append(Check(stage, "OK", "Anmeldung erfolgreich."))
        else:
            checks.append(Check("Authentifizierung", "SKIP", "Keine Zugangsdaten angegeben; nur Netzwerk getestet."))
    except (OSError, ssl.SSLError, smtplib.SMTPException, UnicodeError, ValueError):
        _protocol_error(checks, stage)
    finally:
        if client is not None:
            client.close()


def _imap(settings: ConnectionSettings, checks: list[Check], timeout: float) -> None:
    context = ssl.create_default_context()
    client = None
    stage = "TLS" if settings.security == "SSL/TLS" else "Protokoll"
    try:
        if settings.security == "SSL/TLS":
            client = imaplib.IMAP4_SSL(settings.host, settings.port, ssl_context=context, timeout=timeout)
            checks.append(Check("TLS", "OK", "Zertifikat und TLS-Handshake erfolgreich geprüft."))
        else:
            client = imaplib.IMAP4(settings.host, settings.port, timeout=timeout)
        checks.append(Check("Banner", "INFO", _text(client.welcome)))
        if settings.security == "STARTTLS":
            stage = "STARTTLS"
            client.starttls(ssl_context=context)
            checks.append(Check(stage, "OK", "Zertifikat und TLS-Handshake erfolgreich geprüft."))
        elif settings.security == "None":
            checks.append(Check("TLS", "WARN", "Unverschlüsselte Verbindung; Zugangsdaten sind lesbar."))
        if settings.username:
            stage = "Authentifizierung"
            status, _ = client.login(settings.username, settings.password)
            if status != "OK":
                _protocol_error(checks, stage)
                return
            checks.append(Check(stage, "OK", "Anmeldung erfolgreich."))
        else:
            checks.append(Check("Authentifizierung", "SKIP", "Keine Zugangsdaten angegeben; nur Netzwerk getestet."))
        stage = "CAPABILITY"
        status, data = client.capability()
        if status != "OK":
            checks.append(Check(stage, "ERROR", "CAPABILITY konnte nicht gelesen werden."))
            return
        checks.append(Check(stage, "OK", " ".join(_text(item) for item in data if item is not None)))
    except (OSError, ssl.SSLError, imaplib.IMAP4.error, UnicodeError, ValueError):
        _protocol_error(checks, stage)
    finally:
        if client is not None:
            client.shutdown()


def _protocol_error(checks: list[Check], stage: str) -> None:
    if stage == "Authentifizierung":
        detail = ("Anmeldung fehlgeschlagen. Zugangsdaten, Mailbox-Freigabe und Authentifizierungsrichtlinien prüfen; "
                  "Microsoft 365 kann OAuth2 statt Basic Authentication verlangen.")
    elif stage in ("TLS", "STARTTLS"):
        detail = "TLS fehlgeschlagen. TLS-Modus, Port, Zertifikatskette und Servernamen prüfen."
    else:
        detail = "Mailserver antwortet nicht wie erwartet. Protokoll, Port, Dienst und Firewall prüfen."
    checks.append(Check(stage, "ERROR", detail))


def test_connection(settings: ConnectionSettings, timeout: float = 10) -> list[Check]:
    if (settings.protocol not in ("IMAP", "SMTP") or settings.security not in ("SSL/TLS", "STARTTLS", "None")
            or not settings.host.strip() or not 1 <= settings.port <= 65535
            or bool(settings.username) != bool(settings.password) or timeout <= 0):
        return [Check("Eingabe", "ERROR", "Host, Port, Protokoll, TLS-Modus und vollständige Zugangsdaten prüfen.")]
    checks, reachable = _network_check(settings, timeout)
    if reachable:
        if settings.protocol == "IMAP":
            _imap(settings, checks, timeout)
        else:
            _smtp(settings, checks, timeout)
    return checks
