import errno
import imaplib
import smtplib
import socket
import socketserver
import ssl
import threading
from unittest.mock import Mock

import pytest

from src import connection_test as diagnostic


def settings(protocol="SMTP", security="STARTTLS", username="user", password="secret"):  # noqa: S107
    return diagnostic.ConnectionSettings(protocol, "mail.example", 587, security, username, password)


@pytest.fixture
def reachable(monkeypatch):
    monkeypatch.setattr(
        diagnostic, "_network_check", lambda *_: ([diagnostic.Check("DNS", "OK", "127.0.0.1")], True)
    )


def test_dns_failure_prevents_login(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", Mock(side_effect=socket.gaierror()))
    smtp = Mock()
    monkeypatch.setattr(smtplib, "SMTP", smtp)
    checks = diagnostic.test_connection(settings())
    assert checks[0].name == "DNS"
    assert checks[0].status == "ERROR"
    smtp.assert_not_called()


@pytest.mark.parametrize(
    ("error", "message"),
    [(TimeoutError(), "Zeitüberschreitung"), (ConnectionRefusedError(errno.ECONNREFUSED, "refused"), "abgelehnt")],
)
def test_tcp_errors_prevent_protocol(monkeypatch, error, message):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 587))
    ])
    sock = Mock()
    sock.__enter__ = Mock(return_value=sock)
    sock.__exit__ = Mock(return_value=False)
    sock.connect.side_effect = error
    monkeypatch.setattr(socket, "socket", lambda *a: sock)
    smtp = Mock()
    monkeypatch.setattr(smtplib, "SMTP", smtp)
    checks = diagnostic.test_connection(settings())
    assert checks[-1].name == "TCP"
    assert message in checks[-1].detail
    smtp.assert_not_called()


def test_network_lists_addresses_and_falls_back(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [
        (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 587, 0, 0)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 587)),
    ])
    sock = Mock()
    sock.__enter__ = Mock(return_value=sock)
    sock.__exit__ = Mock(return_value=False)
    sock.connect.side_effect = [ConnectionRefusedError(errno.ECONNREFUSED, "refused"), None]
    monkeypatch.setattr(socket, "socket", lambda *a: sock)
    checks, success = diagnostic._network_check(settings(), 10)
    assert success
    assert "::1" in checks[0].detail and "127.0.0.1" in checks[0].detail
    assert checks[1].status == "OK" and "ms" in checks[1].detail


def test_smtp_starttls_before_auth_and_features(monkeypatch, reachable):
    smtp = Mock()
    smtp.ehlo.return_value = (250, b"mail.example\nAUTH LOGIN XOAUTH2")
    smtp.has_extn.return_value = True
    smtp.esmtp_features = {"auth": " LOGIN XOAUTH2"}
    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **kw: smtp)
    checks = diagnostic.test_connection(settings())
    assert [c.name for c in checks] == ["DNS", "EHLO", "STARTTLS", "EHLO nach TLS", "SMTP AUTH", "Authentifizierung"]
    assert "XOAUTH2" in checks[-2].detail
    assert [c[0] for c in smtp.method_calls].index("starttls") < [c[0] for c in smtp.method_calls].index("login")
    smtp.close.assert_called_once()


def test_smtp_no_starttls_never_authenticates(monkeypatch, reachable):
    smtp = Mock()
    smtp.ehlo.return_value = (250, b"hello")
    smtp.has_extn.return_value = False
    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **kw: smtp)
    checks = diagnostic.test_connection(settings())
    assert checks[-1].name == "STARTTLS" and checks[-1].status == "ERROR"
    smtp.login.assert_not_called()


def test_smtp_tls_failure_never_authenticates(monkeypatch, reachable):
    smtp = Mock()
    smtp.ehlo.return_value = (250, b"hello")
    smtp.has_extn.return_value = True
    smtp.starttls.side_effect = ssl.SSLError("bad certificate")
    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **kw: smtp)
    checks = diagnostic.test_connection(settings())
    assert checks[-1].name == "STARTTLS" and checks[-1].status == "ERROR"
    smtp.login.assert_not_called()


def test_smtp_implicit_tls_validates_certificates(monkeypatch, reachable):
    smtp = Mock()
    smtp.ehlo.return_value = (250, b"hello")
    smtp.esmtp_features = {"auth": "LOGIN"}
    factory = Mock(return_value=smtp)
    monkeypatch.setattr(smtplib, "SMTP_SSL", factory)
    checks = diagnostic.test_connection(settings(security="SSL/TLS"))
    assert any(check.name == "TLS" and check.status == "OK" for check in checks)
    assert factory.call_args.kwargs["context"].check_hostname
    smtp.login.assert_called_once()


def test_smtp_tls_or_auth_error_does_not_expose_secret(monkeypatch, reachable):
    smtp = Mock()
    smtp.ehlo.return_value = (250, b"hello")
    smtp.has_extn.return_value = True
    smtp.esmtp_features = {"auth": "LOGIN"}
    smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"secret")
    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **kw: smtp)
    checks = diagnostic.test_connection(settings())
    assert checks[-1].name == "Authentifizierung" and checks[-1].status == "ERROR"
    assert "secret" not in repr(checks)


def test_imap_tls_banner_auth_and_capability(monkeypatch, reachable):
    imap = Mock()
    imap.welcome = b"* OK ready"
    imap.login.return_value = ("OK", [b"welcome"])
    imap.capability.return_value = ("OK", [b"IMAP4rev1 AUTH=XOAUTH2"])
    factory = Mock(return_value=imap)
    monkeypatch.setattr(imaplib, "IMAP4_SSL", factory)
    checks = diagnostic.test_connection(settings("IMAP", "SSL/TLS"))
    assert [c.name for c in checks] == ["DNS", "TLS", "Banner", "Authentifizierung", "CAPABILITY"]
    assert "AUTH=XOAUTH2" in checks[-1].detail
    assert factory.call_args.kwargs["ssl_context"].check_hostname
    imap.shutdown.assert_called_once()


def test_imap_starttls_failure_blocks_login(monkeypatch, reachable):
    imap = Mock()
    imap.welcome = b"* OK ready"
    imap.starttls.side_effect = imaplib.IMAP4.error("unsupported")
    factory = Mock(return_value=imap)
    factory.error = imaplib.IMAP4.error
    monkeypatch.setattr(imaplib, "IMAP4", factory)
    checks = diagnostic.test_connection(settings("IMAP"))
    assert checks[-1].name == "STARTTLS" and checks[-1].status == "ERROR"
    imap.login.assert_not_called()


def test_imap_starttls_before_login(monkeypatch, reachable):
    imap = Mock()
    imap.welcome = b"* OK ready"
    imap.login.return_value = ("OK", [b"welcome"])
    imap.capability.return_value = ("OK", [b"IMAP4rev1"])
    factory = Mock(return_value=imap)
    factory.error = imaplib.IMAP4.error
    monkeypatch.setattr(imaplib, "IMAP4", factory)
    checks = diagnostic.test_connection(settings("IMAP"))
    assert any(check.name == "STARTTLS" and check.status == "OK" for check in checks)
    assert imap.starttls.call_args.kwargs["ssl_context"].check_hostname
    methods = [call[0] for call in imap.method_calls]
    assert methods.index("starttls") < methods.index("login")


def test_no_credentials_and_incomplete_credentials(monkeypatch, reachable):
    smtp = Mock()
    smtp.ehlo.return_value = (250, b"hello")
    smtp.has_extn.return_value = True
    smtp.esmtp_features = {}
    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **kw: smtp)
    checks = diagnostic.test_connection(settings(username="", password=""))
    assert checks[-1].status == "SKIP"
    smtp.login.assert_not_called()
    assert diagnostic.test_connection(settings(password=""))[0].name == "Eingabe"


@pytest.mark.parametrize("protocol", ["IMAP", "SMTP"])
def test_real_local_protocol_session(protocol):
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            try:
                self.wfile.write(b"* OK test server\r\n" if protocol == "IMAP" else b"220 test server\r\n")
                while line := self.rfile.readline():
                    if protocol == "IMAP":
                        tag, command, *_ = line.split()
                        if command.upper() == b"CAPABILITY":
                            self.wfile.write(b"* CAPABILITY IMAP4rev1 AUTH=XOAUTH2\r\n" + tag + b" OK done\r\n")
                        else:
                            self.wfile.write(tag + b" OK logged in\r\n")
                    elif line.upper().startswith(b"EHLO"):
                        self.wfile.write(b"250-test server\r\n250 AUTH PLAIN LOGIN XOAUTH2\r\n")
                    elif line.upper().startswith(b"AUTH"):
                        self.wfile.write(b"235 authenticated\r\n")
                    else:
                        self.wfile.write(b"500 unsupported\r\n")
            except (BrokenPipeError, ConnectionResetError):
                return

    with socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler) as server:
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            config = diagnostic.ConnectionSettings(protocol, "127.0.0.1", server.server_address[1],
                                                   "None", "user", "secret")
            checks = diagnostic.test_connection(config)
        finally:
            server.shutdown()
            thread.join()
    assert not [check for check in checks if check.status == "ERROR"]
    assert any(check.name == "TCP" and check.status == "OK" for check in checks)
    assert any(check.name == "Authentifizierung" and check.status == "OK" for check in checks)
    assert any("XOAUTH2" in check.detail for check in checks)
