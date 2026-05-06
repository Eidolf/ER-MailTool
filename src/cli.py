import typer
import os
import uvicorn
from dotenv import load_dotenv
from .mailer import EmailService

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
        raise typer.Exit(code=1)

@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind")
):
    """
    Start the secure API server.
    """
    typer.echo(f"Starting API server on {host}:{port}...")
    uvicorn.run("src.api:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    app()
