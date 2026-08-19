import os
from typing import Dict, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from .mailer import EmailService
from .network_tools import NetworkTools
from .oauth import OAuthTester

app = FastAPI(title="ER-MailTool API", version="1.0.0")

# --- Models ---
class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    server: str = os.getenv("SMTP_SERVER", "smtp.office365.com")
    port: int = int(os.getenv("SMTP_PORT", 587))
    username: str = os.getenv("SMTP_USERNAME")
    password: str = os.getenv("SMTP_PASSWORD")

class OAuthTestRequest(BaseModel):
    tenant_or_token_url: str
    client_id: str
    auth_type: str = "client_secret" # client_secret | jwt_bearer | client_assertion
    client_secret: Optional[str] = None
    assertion: Optional[str] = None
    scope: str = "https://graph.microsoft.com/.default"
    resource: Optional[str] = None
    custom_params: Optional[Dict[str, str]] = None
    test_graph_api: bool = False

class JWTDecodeRequest(BaseModel):
    token: str

class SendOAuthEmailRequest(BaseModel):
    access_token: str
    from_email: EmailStr
    to_email: EmailStr
    subject: str
    body: str
    method: str = "graph"  # graph | smtp_oauth2
    smtp_server: str = "smtp.office365.com"
    smtp_port: int = 587

# --- Rate Limiting ---
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Adjusted CSP to allow Swagger UI assets and source maps from CDN
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
            "connect-src 'self' https://cdn.jsdelivr.net; "
            "frame-src 'self';"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# --- Routes ---

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return RedirectResponse(url="https://fastapi.tiangolo.com/img/favicon.png")

@app.get("/health")
@limiter.limit("5/minute")
async def health_check(request: Request):
    return {"status": "ok", "security": "hardened"}

# --- Mail Endpoints ---

@app.post("/send")
@limiter.limit("2/minute")
async def send_email(request: Request, email_data: EmailRequest):
    if not email_data.username or not email_data.password:
        return {"status": "error", "message": "SMTP credentials missing"}
    
    service = EmailService(
        email_data.server, 
        email_data.port, 
        email_data.username, 
        email_data.password
    )
    
    try:
        service.send_email(email_data.to, email_data.subject, email_data.body)
        return {"status": "success", "message": "Email sent"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Network & DNS Endpoints ---

@app.get("/mx/{domain}")
@limiter.limit("10/minute")
async def get_mx(request: Request, domain: str):
    records = NetworkTools.get_mx_records(domain)
    return {"domain": domain, "mx_records": records}

@app.get("/spf/{domain}")
@limiter.limit("10/minute")
async def get_spf(request: Request, domain: str):
    record = NetworkTools.get_spf_record(domain)
    return {"domain": domain, "spf_record": record}

@app.get("/dmarc/{domain}")
@limiter.limit("10/minute")
async def get_dmarc(request: Request, domain: str):
    record = NetworkTools.get_dmarc_record(domain)
    return {"domain": domain, "dmarc_record": record}

@app.get("/dkim/{domain}/{selector}")
@limiter.limit("10/minute")
async def get_dkim(request: Request, domain: str, selector: str):
    record = NetworkTools.get_dkim_record(domain, selector)
    return {"domain": domain, "selector": selector, "dkim_record": record}

@app.get("/dns/{domain}/{record_type}")
@limiter.limit("10/minute")
async def get_dns(request: Request, domain: str, record_type: str):
    records = NetworkTools.get_dns_records(domain, record_type.upper())
    return {"domain": domain, "type": record_type.upper(), "records": records}

@app.get("/scan/{host}")
@limiter.limit("2/minute")
async def port_scan(request: Request, host: str):
    results = NetworkTools.scan_common_ports(host)
    return {"host": host, "open_ports": results}

@app.get("/rbl/{ip_address}")
@limiter.limit("2/minute")
async def blacklist_check(request: Request, ip_address: str):
    results = NetworkTools.check_rbl(ip_address)
    return {"ip": ip_address, "blacklist_results": results}

@app.get("/whois/{domain}")
@limiter.limit("5/minute")
async def get_whois_info(request: Request, domain: str):
    results = NetworkTools.get_whois(domain)
    # whois returns a dictionary-like object that might need conversion
    return {"domain": domain, "whois_data": str(results)}

# --- OAuth 2.0 & Enterprise App Endpoints ---

@app.post("/oauth/test")
@limiter.limit("10/minute")
async def test_oauth(request: Request, data: OAuthTestRequest):
    res = OAuthTester.test_oauth_auth(
        tenant_or_token_url=data.tenant_or_token_url,
        client_id=data.client_id,
        auth_type=data.auth_type,
        client_secret=data.client_secret,
        assertion=data.assertion,
        scope=data.scope,
        resource=data.resource,
        custom_params=data.custom_params
    )

    if res.get("success") and data.test_graph_api and res.get("access_token"):
        graph_res = OAuthTester.test_microsoft_graph_api(res["access_token"])
        res["graph_test"] = graph_res

    return res

@app.post("/oauth/decode")
@limiter.limit("30/minute")
async def decode_token_claims(request: Request, data: JWTDecodeRequest):
    return OAuthTester.decode_jwt_unverified(data.token)

@app.post("/oauth/send")
@limiter.limit("5/minute")
async def send_oauth_email(request: Request, data: SendOAuthEmailRequest):
    if data.method == "graph":
        return OAuthTester.send_email_graph(
            access_token=data.access_token,
            from_user=data.from_email,
            to_email=data.to_email,
            subject=data.subject,
            body=data.body
        )
    else:
        return OAuthTester.send_email_smtp_oauth2(
            access_token=data.access_token,
            from_email=data.from_email,
            to_email=data.to_email,
            subject=data.subject,
            body=data.body,
            server=data.smtp_server,
            port=data.smtp_port
        )
