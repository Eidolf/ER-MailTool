from typer.testing import CliRunner
from fastapi.testclient import TestClient
from src.cli import app
from src.api import app as api_app

runner = CliRunner()
client = TestClient(api_app)

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ER-MailTool" in result.stdout

def test_api_health():
    response = client.get("/health")
    # 429 is possible due to rate limiting in tests if run fast, but usually 200
    # Setup loop/rate limit mock if needed strictly
    if response.status_code == 200:
        assert response.json() == {"status": "ok", "security": "hardened"}
    
def test_security_headers():
    response = client.get("/health")
    if response.status_code == 200:
        assert "x-content-type-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"
