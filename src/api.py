from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, EmailStr
from fastapi.responses import RedirectResponse
from .mailer import EmailService
import os

app = FastAPI(title="ER-MailTool API", version="1.0.0")

# Models
class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    server: str = os.getenv("SMTP_SERVER", "smtp.office365.com")
    port: int = int(os.getenv("SMTP_PORT", 587))
    username: str = os.getenv("SMTP_USERNAME")
    password: str = os.getenv("SMTP_PASSWORD")

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Headers Middleware (Helmet-like)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Adjusted CSP to allow Swagger UI assets from CDN
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
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
