# ER-MailTool

![Logo](images/logo.png)

A portable, secure, and extensible Email Testing Tool designed for DevOps and Security professionals.
Primarily built to test authenticated SMTP sending (Office 365, etc.) with strict security compliance.

## Features

- **Portable**: Build as a standalone executable (Windows/Linux/macOS).
- **Secure**: Strict secrets management, SBOM generation, and API hardening.
- **Office 365 Ready**: Pre-configured for StartTLS (Port 587).
- **DevSecOps**: Integrated SAST (CodeQL/Ruff), Dependency Scanning, and Auto-Fixing CI/CD.

## Usage

### CLI

```bash
# Send a test email
er-mailtool send --to user@example.com --subject "Test" --body "Hello"
```

### API

Start the secure API server:

```bash
er-mailtool serve
```

Access Swagger Docs at `http://localhost:8000/docs`.

### Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

## Development

```bash
# Install
poetry install

# Lint
poetry run ruff check .

# Test
poetry run pytest
```

## Build & Release

Builds are managed via GitHub Actions.
Trigger a "Full" build manually via the Actions tab to generate artifacts.

## License

MIT
