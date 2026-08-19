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

### 1. Graphical Interface (GUI)

To start the desktop application (Windows/macOS or Linux with Desktop Environment / X11):

```bash
# Start GUI directly
poetry run er-mailtool
```
*(Or double-click the compiled binary `er-mailtool` / `er-mailtool.exe` without CLI arguments.)*

> [!NOTE]
> **Linux GUI Prerequisite**: Linux distributions require the OS-level Tkinter package (`sudo apt install python3-tk` on Debian/Ubuntu, `sudo dnf install python3-tkinter` on Fedora).

---

### 2. API Server (Headless / Testing Environment)

On headless Linux test servers without a display, start the REST API server:

```bash
# Start API daemon on port 8000
poetry run er-mailtool serve --host 0.0.0.0 --port 8000
```

Access Swagger Documentation & Test Interface at `http://<server-ip>:8000/docs`.

Key API Endpoints:
- `POST /oauth/test`: Test OAuth 2.0 Client Credentials or JWT Bearer Assertion flow & validate permissions.
- `POST /oauth/decode`: Decode unverified JWT claims, roles, appid, expiration & audience.
- `POST /send`: Send email via authenticated SMTP.
- `GET /mx/{domain}`, `GET /spf/{domain}`, `GET /dmarc/{domain}`, `GET /dkim/{domain}/{selector}`: DNS & Auth records.

---

### 3. CLI Commands

You can run direct diagnostic commands via CLI:

```bash
# Send a test email
poetry run er-mailtool send --to user@example.com --subject "Test" --body "Hello"

# Test OAuth 2.0 Client Credentials flow (Microsoft Entra ID / Azure AD)
poetry run er-mailtool test-oauth --tenant "<tenant-id>" --client-id "<app-id>" --client-secret "<secret>" --test-graph

# Test OAuth 2.0 JWT Bearer / Client Assertion flow
poetry run er-mailtool test-oauth --tenant "<tenant-id>" --client-id "<app-id>" --assertion "<jwt>" --auth-type jwt_bearer

# Inspect JWT claims without signature verification
poetry run er-mailtool inspect-jwt "<jwt-token>"
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
   - Every push to `main` or manual trigger (`Actions` > `CI Orchestrator` with `Full` mode) runs SAST, tests, builds standalone executables for **both Linux and Windows**, and generates an SBOM.
   - Download the pre-built binaries under the workflow's **Artifacts** (`er-mailtool-linux` and `er-mailtool-windows`).

2. **Official Version Releases**:
   - Navigate to `Actions` > `Release` > `Run workflow`.
   - Select version increment (`patch`, `minor`, or `major`).
   - GitHub Actions automatically bumps `pyproject.toml`, creates a Git release tag (e.g. `v1.0.1`), and publishes a GitHub Release with auto-generated release notes.

## License

MIT
