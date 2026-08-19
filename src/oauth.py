import base64
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


class OAuthTester:
    @staticmethod
    def resolve_token_url(tenant_or_url: str) -> str:
        """
        If tenant_or_url is a full URL, return it.
        Otherwise assume it is an Azure AD / Entra ID tenant ID / domain and format the v2.0 endpoint.
        """
        tenant_or_url = tenant_or_url.strip()
        if tenant_or_url.startswith("http://") or tenant_or_url.startswith("https://"):
            return tenant_or_url
        return f"https://login.microsoftonline.com/{tenant_or_url}/oauth2/v2.0/token"

    @staticmethod
    def decode_jwt_unverified(token: str) -> Dict[str, Any]:
        """
        Safely decodes header and payload of a JWT without verifying signature.
        Useful for inspecting claims, roles, scopes, appid, issuer, and expiration.
        """
        parts = token.strip().split(".")
        if len(parts) < 2:
            return {"error": "Invalid JWT format (expected at least 2 dot-separated parts)"}

        def _b64_decode(data: str) -> Dict[str, Any]:
            # Add padding
            rem = len(data) % 4
            if rem > 0:
                data += "=" * (4 - rem)
            decoded_bytes = base64.urlsafe_b64decode(data.encode("utf-8"))
            return json.loads(decoded_bytes.decode("utf-8", errors="replace"))

        result = {}
        try:
            result["header"] = _b64_decode(parts[0])
        except Exception as e:
            result["header_error"] = str(e)

        try:
            result["payload"] = _b64_decode(parts[1])
            # Add human readable expiration info if present
            if "exp" in result["payload"]:
                exp_ts = result["payload"]["exp"]
                now_ts = int(time.time())
                diff = exp_ts - now_ts
                result["_validity"] = {
                    "is_expired": diff <= 0,
                    "expires_in_seconds": diff,
                    "expires_at_epoch": exp_ts
                }
        except Exception as e:
            result["payload_error"] = str(e)

        return result

    @classmethod
    def test_oauth_auth(
        cls,
        tenant_or_token_url: str,
        client_id: str,
        auth_type: str = "client_secret",
        client_secret: Optional[str] = None,
        assertion: Optional[str] = None,
        scope: str = "https://graph.microsoft.com/.default",
        resource: Optional[str] = None,
        custom_params: Optional[Dict[str, str]] = None,
        timeout: int = 15
    ) -> Dict[str, Any]:
        """
        Execute OAuth 2.0 Token Request.
        auth_type:
          - 'client_secret': Standard Client Credentials Flow
          - 'jwt_bearer': RFC 7523 JWT Bearer Assertion Grant (grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer)
          - 'client_assertion': Client Credentials using JWT Client Assertion (client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer)
        """
        token_url = cls.resolve_token_url(tenant_or_token_url)
        payload = {}

        if auth_type == "client_secret":
            payload["grant_type"] = "client_credentials"
            payload["client_id"] = client_id
            if not client_secret:
                return {"success": False, "error": "client_secret is required for Client Credentials flow"}
            payload["client_secret"] = client_secret
            if scope:
                payload["scope"] = scope
            if resource:
                payload["resource"] = resource

        elif auth_type == "jwt_bearer":
            # RFC 7523 / RFC 7521 Bearer Assertion grant
            payload["grant_type"] = "urn:ietf:params:oauth:grant-type:jwt-bearer"
            payload["client_id"] = client_id
            if client_secret:
                payload["client_secret"] = client_secret
            if not assertion:
                return {"success": False, "error": "assertion JWT is required for JWT Bearer grant"}
            payload["assertion"] = assertion
            if scope:
                payload["scope"] = scope
            if resource:
                payload["resource"] = resource

        elif auth_type == "client_assertion":
            # Client Credentials with Private Key / Certificate JWT client assertion
            payload["grant_type"] = "client_credentials"
            payload["client_id"] = client_id
            payload["client_assertion_type"] = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
            if not assertion:
                return {"success": False, "error": "client_assertion JWT is required for Client Assertion flow"}
            payload["client_assertion"] = assertion
            if scope:
                payload["scope"] = scope
            if resource:
                payload["resource"] = resource
        else:
            return {"success": False, "error": f"Unsupported auth_type: {auth_type}"}

        if custom_params:
            payload.update(custom_params)

        # Execute HTTP POST
        data_encoded = urllib.parse.urlencode(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "ER-MailTool/1.0.0 (OAuth2-Tester)"
        }

        if not (token_url.startswith("https://") or token_url.startswith("http://")):
            return {"success": False, "error": "Invalid URL scheme: only http/https allowed"}

        req = urllib.request.Request(token_url, data=data_encoded, headers=headers, method="POST")  # noqa: S310
        ssl_ctx = ssl.create_default_context()

        start_time = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as response:  # noqa: S310
                latency_ms = int((time.time() - start_time) * 1000)
                status_code = response.getcode()
                raw_body = response.read().decode("utf-8", errors="replace")
                try:
                    json_resp = json.loads(raw_body)
                except Exception:
                    json_resp = {"raw": raw_body}

                access_token = json_resp.get("access_token")
                decoded_claims = None
                if access_token:
                    decoded_claims = cls.decode_jwt_unverified(access_token)

                return {
                    "success": True,
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                    "token_url": token_url,
                    "token_type": json_resp.get("token_type"),
                    "expires_in": json_resp.get("expires_in"),
                    "ext_expires_in": json_resp.get("ext_expires_in"),
                    "access_token": access_token,
                    "scope_granted": json_resp.get("scope"),
                    "claims": decoded_claims,
                    "raw_response": json_resp
                }

        except urllib.error.HTTPError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
            except Exception:
                err_json = {"raw": err_body}

            return {
                "success": False,
                "status_code": e.code,
                "latency_ms": latency_ms,
                "token_url": token_url,
                "error": err_json.get("error", "HTTPError"),
                "error_description": err_json.get("error_description", str(e)),
                "error_codes": err_json.get("error_codes", []),
                "raw_response": err_json
            }
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "status_code": 0,
                "latency_ms": latency_ms,
                "token_url": token_url,
                "error": type(e).__name__,
                "error_description": str(e)
            }

    @staticmethod
    def test_microsoft_graph_api(access_token: str, endpoint: str = "https://graph.microsoft.com/v1.0/organization", timeout: int = 10) -> Dict[str, Any]:
        """
        Verify acquired access token against Microsoft Graph API.
        """
        if not access_token:
            return {"success": False, "error": "Access token is required"}

        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "ER-MailTool/1.0.0 (Graph-Validator)"
        }

        if not (endpoint.startswith("https://") or endpoint.startswith("http://")):
            return {"success": False, "error": "Invalid URL scheme: only http/https allowed"}

        req = urllib.request.Request(endpoint, headers=headers, method="GET")  # noqa: S310
        ssl_ctx = ssl.create_default_context()
        start_time = time.time()

        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as response:  # noqa: S310
                latency_ms = int((time.time() - start_time) * 1000)
                status_code = response.getcode()
                raw_body = response.read().decode("utf-8", errors="replace")
                try:
                    data = json.loads(raw_body)
                except Exception:
                    data = {"raw": raw_body}

                return {
                    "success": True,
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                    "endpoint": endpoint,
                    "data": data
                }
        except urllib.error.HTTPError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
            except Exception:
                err_json = {"raw": err_body}

            return {
                "success": False,
                "status_code": e.code,
                "latency_ms": latency_ms,
                "endpoint": endpoint,
                "error": err_json.get("error", str(e)),
                "raw_response": err_json
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "latency_ms": int((time.time() - start_time) * 1000),
                "endpoint": endpoint,
                "error": str(e)
            }

    @staticmethod
    def send_email_graph(
        access_token: str,
        from_user: str,
        to_email: str,
        subject: str,
        body: str,
        timeout: int = 15
    ) -> Dict[str, Any]:
        """
        Send an email via Microsoft Graph API /v1.0/users/{from_user}/sendMail using the Bearer token.
        Requires Mail.Send (Application permission) on the Enterprise App.
        """
        if not access_token:
            return {"success": False, "error": "Access token is required"}
        if not from_user:
            return {"success": False, "error": "Sender email (from_user) is required"}
        if not to_email:
            return {"success": False, "error": "Recipient email (to_email) is required"}

        endpoint = f"https://graph.microsoft.com/v1.0/users/{urllib.parse.quote(from_user)}/sendMail"
        message_payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ]
            },
            "saveToSentItems": "true"
        }

        data_encoded = json.dumps(message_payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "ER-MailTool/1.0.0 (Graph-Mailer)"
        }

        req = urllib.request.Request(endpoint, data=data_encoded, headers=headers, method="POST")  # noqa: S310
        ssl_ctx = ssl.create_default_context()
        start_time = time.time()

        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as response:  # noqa: S310
                latency_ms = int((time.time() - start_time) * 1000)
                status_code = response.getcode()
                return {
                    "success": True,
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                    "message": f"Email successfully sent via MS Graph to {to_email} (from {from_user})."
                }
        except urllib.error.HTTPError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
            except Exception:
                err_json = {"raw": err_body}

            return {
                "success": False,
                "status_code": e.code,
                "latency_ms": latency_ms,
                "error": err_json.get("error", {}).get("message", str(e)) if isinstance(err_json.get("error"), dict) else str(err_json),
                "raw_response": err_json
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "latency_ms": int((time.time() - start_time) * 1000),
                "error": str(e)
            }

    @staticmethod
    def send_email_smtp_oauth2(
        access_token: str,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        server: str = "smtp.office365.com",
        port: int = 587,
        use_ssl: bool = False,
        use_starttls: bool = True,
        timeout: int = 15
    ) -> Dict[str, Any]:
        """
        Send an email via SMTP using OAuth2 XOAUTH2 authentication.
        Format: user=<user>\x01auth=Bearer <token>\x01\x01
        """
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        if not access_token:
            return {"success": False, "error": "Access token is required"}
        if not from_email or not to_email:
            return {"success": False, "error": "Sender and recipient emails are required"}

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        start_time = time.time()
        try:
            if use_ssl or port == 465:
                smtp_client = smtplib.SMTP_SSL(server, port, timeout=timeout)
            else:
                smtp_client = smtplib.SMTP(server, port, timeout=timeout)

            with smtp_client as smtp:
                smtp.ehlo()
                if not (use_ssl or port == 465) and use_starttls and smtp.has_extn('STARTTLS'):
                    smtp.starttls()
                    smtp.ehlo()

                # Generate XOAUTH2 SASL string
                auth_str = f"user={from_email}\x01auth=Bearer {access_token}\x01\x01"
                auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

                # AUTH XOAUTH2 command
                code, resp = smtp.docmd("AUTH", f"XOAUTH2 {auth_b64}")
                if code not in (235, 250):
                    return {
                        "success": False,
                        "status_code": code,
                        "latency_ms": int((time.time() - start_time) * 1000),
                        "error": f"SMTP OAuth2 Auth Failed ({code}): {resp.decode('utf-8', errors='replace')}"
                    }

                smtp.sendmail(from_email, [to_email], msg.as_string())
                return {
                    "success": True,
                    "status_code": 250,
                    "latency_ms": int((time.time() - start_time) * 1000),
                    "message": f"Email successfully sent via SMTP XOAUTH2 to {to_email} (from {from_email})."
                }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "latency_ms": int((time.time() - start_time) * 1000),
                "error": str(e)
            }
