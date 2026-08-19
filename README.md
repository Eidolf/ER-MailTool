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

# Test OAuth 2.0 Client Credentials flow (Microsoft Entra ID / Azure AD)
er-mailtool test-oauth --tenant "<tenant-id>" --client-id "<app-id>" --client-secret "<secret>" --test-graph

# Test OAuth 2.0 JWT Bearer / Client Assertion flow
er-mailtool test-oauth --tenant "<tenant-id>" --client-id "<app-id>" --assertion "<jwt>" --auth-type jwt_bearer

# Inspect JWT claims without signature verification
er-mailtool inspect-jwt "<jwt-token>"
```

### API

Start the secure API server:

```bash
er-mailtool serve
```

Access Swagger Docs at `http://localhost:8000/docs`.

Key API Endpoints:
- `POST /oauth/test`: Test OAuth 2.0 Client Credentials or JWT Bearer Assertion flow & validate permissions.
- `POST /oauth/decode`: Decode unverified JWT claims, roles, appid, expiration & audience.
- `POST /send`: Send email via authenticated SMTP.
- `GET /mx/{domain}`, `GET /spf/{domain}`, `GET /dmarc/{domain}`, `GET /dkim/{domain}/{selector}`: DNS & Auth records.

### Linux Server (Headless / Testing Environment)

If you are running on a test server without a graphical desktop (GUI), run in CLI or API daemon mode without requiring X11 / Tkinter:

```bash
# 1. Install dependencies via poetry
poetry install

# 2. Start the API server on all interfaces
poetry run er-mailtool serve --host 0.0.0.0 --port 8000

# 3. Or run CLI commands directly
poetry run er-mailtool test-oauth --tenant "<tenant-id>" --client-id "<app-id>" --client-secret "<secret>"
```

### Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

## Development

```bash
# Install dependencies
poetry install

# Lint & static analysis
poetry run ruff check .

# Run test suite
poetry run pytest
```

## Build & Release

### Local Portable Binary Build

To package a standalone executable locally (e.g. for testing before releasing):

```bash
# Build standalone binary (dist/er-mailtool or dist/er-mailtool.exe)
poetry run pyinstaller --noconfirm --onefile --windowed --name er-mailtool \
  --add-data "$(poetry run pip show customtkinter | grep Location | cut -d' ' -f2)/customtkinter:customtkinter/" \
  --hidden-import=customtkinter \
  src/main.py
```

### CI / CD via GitHub Actions

1. **Automated Test Builds & Artifacts**:
   - Every push to `main` or manual trigger (`Actions` > `CI Orchestrator` with `Full` mode) runs SAST, tests, builds the standalone Linux executable, and generates an SBOM.
   - Download the pre-built binary under the workflow's **Artifacts** (`er-mailtool-linux`).

2. **Official Version Releases**:
   - Navigate to `Actions` > `Release` > `Run workflow`.
   - Select version increment (`patch`, `minor`, or `major`).
   - GitHub Actions automatically bumps `pyproject.toml`, creates a Git release tag (e.g. `v1.0.1`), and publishes a GitHub Release with auto-generated release notes.

## License

MIT
