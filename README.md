# ER-MailTool

![Logo](images/logo.png)

A portable, secure, and extensible Email Testing Tool designed for DevOps and Security professionals.
Primarily built to test authenticated SMTP sending (Office 365, etc.) with strict security compliance.

## Features

- **Portable**: Build as a standalone executable (Windows/Linux/macOS).
- **Secure**: Strict secrets management, SBOM generation, and API hardening.
- **Office 365 Ready**: Pre-configured for StartTLS (Port 587).
- **IMAP / SMTP diagnostics**: Check DNS, TCP, TLS and password authentication without sending mail.
- **DevSecOps**: Integrated SAST (CodeQL/Ruff), Dependency Scanning, and Auto-Fixing CI/CD.

<img width="1096" height="828" alt="image" src="https://github.com/user-attachments/assets/fccb9ef2-a1e3-4fd3-9136-b5d899712e8c" />


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

#### IMAP / SMTP connection test

Select **Connectivity → IMAP / SMTP Test**. The Microsoft 365 preset uses
`outlook.office365.com:993` (SSL/TLS) and `smtp.office365.com:587` (STARTTLS).
Hosts, ports and security modes can be changed independently for other mail servers.
Test IMAP or SMTP separately; the test does not send an email. Leave both username
and password empty for a network/protocol-only test. Enter both to test password
authentication. **None** explicitly uses an unencrypted connection and exposes
credentials to the network; use it only in a trusted test environment.

The test lists resolved IPv4/IPv6 addresses, TCP outcome and elapsed time before
opening a mail session. TLS certificates and hostnames are validated using the
system trust store. STARTTLS must succeed when selected; there is no fallback to
plaintext. Results include the IMAP greeting and CAPABILITY, or SMTP EHLO and
advertised AUTH mechanisms. An open port or successful TLS handshake does not
prove that authentication works. The protocol connection is separate from the
initial TCP probe, so changing network conditions may affect the second connection.
Credentials are not saved by this test. Only run it against servers you are
authorized to test.

For Microsoft 365, enable IMAP on the mailbox and SMTP AUTH for the user or
tenant as applicable. Microsoft prefers modern authentication and Basic
Authentication may be disabled. This connection test supports password login,
not OAuth2/XOAUTH2 login; advertised XOAUTH2 support alone does not establish
token permissions. The existing OAuth tester and SMTP OAuth2 sending flow are
separate; a future connection test can add token-based authentication without
changing the network checks.

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

The version in `pyproject.toml` and Git tags describe releases. Changes to the
build workflow do not themselves create a release.

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
   - The `er-mailtool-complete` artifact contains `er-mailtool-complete.zip`, with both executables and `sbom.spdx.json`. The Linux executable has its executable permission restored in the ZIP.

2. **Official Version Releases**:
   - Navigate to `Actions` > `Release` > `Run workflow`.
   - Select version increment (`patch`, `minor`, or `major`).
   - GitHub Actions automatically bumps `pyproject.toml`, creates a Git release tag (e.g. `v1.0.1`), and publishes a GitHub Release with auto-generated release notes.
   - Release assets include the complete ZIP as well as the existing individual executables and SBOM. The ZIP provides an alternative where direct `.exe` downloads are blocked; organizational policies may also block archives.

## Project documentation and change record

- [AGENTS.md](AGENTS.md) contains repository-specific working guidance.
- [ER KnowledgeBase](https://github.com/Eidolf/ER-KnowledgeBase) is a separate,
  access-controlled project. No MailTool-specific profile was identified in the
  checked local snapshot; no private content is copied here.
- Unreleased: added the desktop IMAP/SMTP connection test, Microsoft 365 preset,
  reachability and protocol diagnostics, focused tests and this documentation;
  added a complete ZIP to build artifacts and release assets. Existing SMTP
  sending, OAuth and DNS tools remain unchanged.
- Existing tools already provide test-mail sending and MX, SPF, DKIM and DMARC
  lookups. Certificate details/expiry and OAuth2 login in the new diagnostic
  remain possible future extensions.

## License

MIT
