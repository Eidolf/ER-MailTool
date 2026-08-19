import json
import os
from typing import Optional

import typer
import uvicorn
from dotenv import load_dotenv

from .mailer import EmailService
from .oauth import OAuthTester

load_dotenv()

app = typer.Typer(help="ER-MailTool: Portable Secure Email Utility", rich_markup_mode=None)

@app.command()
def send(
    to: str = typer.Option(..., help="Recipient email"),
    subject: str = typer.Option(..., help="Email subject"),
    body: str = typer.Option(..., help="Email body"),
    server: str = typer.Option(os.getenv("SMTP_SERVER", "smtp.office365.com"), help="SMTP Server"),
    port: int = typer.Option(int(os.getenv("SMTP_PORT", 587)), help="SMTP Port"),
    username: str = typer.Option(os.getenv("SMTP_USERNAME"), help="SMTP Username"),
    password: str = typer.Option(os.getenv("SMTP_PASSWORD"), help="SMTP Password"),
):
    """
    Send an email via authenticated SMTP.
    """
    if not username or not password:
        typer.echo("Error: Username and Password required (set in .env or via flags).", err=True)
        raise typer.Exit(code=1)

    service = EmailService(server, port, username, password)
    try:
        service.send_email(to, subject, body)
        typer.echo("Email sent successfully!")
    except Exception as e:
        typer.echo(f"Failed to send email: {e}", err=True)
        raise typer.Exit(code=1) from e

@app.command("test-oauth")
def test_oauth_cmd(
    tenant: str = typer.Option(os.getenv("AZURE_TENANT_ID", "common"), help="Tenant ID / Domain or Token URL"),
    client_id: str = typer.Option(os.getenv("AZURE_CLIENT_ID", ""), help="Client ID / App Registration ID"),
    client_secret: Optional[str] = typer.Option(None, help="Client Secret (for client_secret flow)"),
    assertion: Optional[str] = typer.Option(None, help="JWT assertion string (for jwt_bearer or client_assertion flow)"),
    auth_type: str = typer.Option("client_secret", help="Auth type: client_secret | jwt_bearer | client_assertion"),
    scope: str = typer.Option("https://graph.microsoft.com/.default", help="OAuth Scope"),
    test_graph: bool = typer.Option(False, help="Perform test request against Microsoft Graph API after token acquisition"),
    send_to: Optional[str] = typer.Option(None, help="Send a test email to this recipient after token acquisition"),
    send_from: Optional[str] = typer.Option(os.getenv("DEFAULT_SENDER", None), help="Sender email mailbox address"),
    send_method: str = typer.Option("graph", help="Email sending method: graph | smtp_oauth2")
):
    """
    Test OAuth 2.0 Client Credentials or JWT Bearer Authentication for Enterprise App Registrations.
    """
    if not client_id:
        typer.echo("Error: Client ID is required.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Testing OAuth2 Auth [{auth_type}] for Client ID: {client_id} against {tenant}...")
    res = OAuthTester.test_oauth_auth(
        tenant_or_token_url=tenant,
        client_id=client_id,
        auth_type=auth_type,
        client_secret=client_secret,
        assertion=assertion,
        scope=scope
    )

    if res.get("success"):
        typer.secho("✅ Token Acquired Successfully!", fg=typer.colors.GREEN, bold=True)
        typer.echo(f"Status: HTTP {res['status_code']} ({res['latency_ms']} ms)")
        typer.echo(f"Token Type: {res.get('token_type')}")
        typer.echo(f"Expires In: {res.get('expires_in')}s")

        claims = res.get("claims")
        if claims and "payload" in claims:
            p = claims["payload"]
            typer.echo(f"Roles/Permissions: {p.get('roles', 'None')}")
            typer.echo(f"Scopes: {p.get('scp', res.get('scope_granted', 'N/A'))}")
            typer.echo(f"Audience: {p.get('aud')}")

        if test_graph and res.get("access_token"):
            typer.echo("\nValidating token against Microsoft Graph API...")
            graph_res = OAuthTester.test_microsoft_graph_api(res["access_token"])
            if graph_res.get("success"):
                typer.secho("✅ Microsoft Graph API Call Passed!", fg=typer.colors.GREEN)
                typer.echo(json.dumps(graph_res.get("data"), indent=2))
            else:
                typer.secho(f"❌ Microsoft Graph Call Failed (HTTP {graph_res.get('status_code')}): {graph_res.get('error')}", fg=typer.colors.RED)

        if send_to and res.get("access_token"):
            sender = send_from or os.getenv("DEFAULT_SENDER", os.getenv("SMTP_USERNAME"))
            if not sender:
                typer.secho("❌ Sender email (--send-from or DEFAULT_SENDER) is required to send test email.", fg=typer.colors.RED)
            else:
                typer.echo(f"\nSending test email via {send_method.upper()} to {send_to} (From: {sender})...")
                if send_method == "graph":
                    mail_res = OAuthTester.send_email_graph(
                        access_token=res["access_token"],
                        from_user=sender,
                        to_email=send_to,
                        subject="ER-MailTool OAuth 2.0 Test Email",
                        body="Test email sent via Microsoft Graph API using OAuth 2.0 Enterprise App Authentication."
                    )
                else:
                    mail_res = OAuthTester.send_email_smtp_oauth2(
                        access_token=res["access_token"],
                        from_email=sender,
                        to_email=send_to,
                        subject="ER-MailTool OAuth 2.0 Test Email",
                        body="Test email sent via SMTP XOAUTH2 using OAuth 2.0 Enterprise App Authentication."
                    )

                if mail_res.get("success"):
                    typer.secho(f"✅ {mail_res.get('message')}", fg=typer.colors.GREEN, bold=True)
                else:
                    typer.secho(f"❌ Email sending failed: {mail_res.get('error')}", fg=typer.colors.RED)
    else:
        typer.secho("❌ OAuth Authentication Failed!", fg=typer.colors.RED, bold=True)
        typer.echo(f"Status: HTTP {res.get('status_code')} ({res.get('latency_ms', 0)} ms)")
        typer.echo(f"Error: {res.get('error')}")
        typer.echo(f"Description: {res.get('error_description')}")
        raise typer.Exit(code=1)

@app.command("inspect-jwt")
def inspect_jwt_cmd(
    token: str = typer.Argument(..., help="JWT token string to decode and inspect claims")
):
    """
    Decode and display header and payload claims of a JWT without signature verification.
    """
    claims = OAuthTester.decode_jwt_unverified(token)
    typer.echo(json.dumps(claims, indent=2))

@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind"),  # noqa: S104
    port: int = typer.Option(8000, help="Port to bind")
):
    """
    Start the secure API server.
    """
    typer.echo(f"Starting API server on {host}:{port}...")
    uvicorn.run("src.api:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    app()
