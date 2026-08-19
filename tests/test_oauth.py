import base64
import json
import urllib.error
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from src.api import app as api_app
from src.cli import app as cli_app
from src.oauth import OAuthTester

client = TestClient(api_app)
runner = CliRunner()

def make_dummy_jwt(payload_dict):
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).decode().rstrip("=")
    signature = "dummy_signature"
    return f"{header}.{payload}.{signature}"

def test_resolve_token_url():
    tenant_id = "contoso.onmicrosoft.com"
    assert OAuthTester.resolve_token_url(tenant_id) == "https://login.microsoftonline.com/contoso.onmicrosoft.com/oauth2/v2.0/token"
    
    full_url = "https://auth.custom-domain.com/token"
    assert OAuthTester.resolve_token_url(full_url) == full_url

def test_decode_jwt_unverified():
    dummy_payload = {
        "aud": "https://graph.microsoft.com",
        "iss": "https://sts.windows.net/test-tenant/",
        "roles": ["Mail.Send", "User.Read.All"],
        "appid": "app-12345",
        "exp": 1999999999
    }
    jwt_str = make_dummy_jwt(dummy_payload)
    decoded = OAuthTester.decode_jwt_unverified(jwt_str)

    assert "header" in decoded
    assert decoded["header"].get("alg") == "RS256"
    assert "payload" in decoded
    assert decoded["payload"].get("appid") == "app-12345"
    assert decoded["payload"].get("roles") == ["Mail.Send", "User.Read.All"]
    assert decoded["_validity"]["is_expired"] is False

def test_client_credentials_success():
    fake_token = make_dummy_jwt({"appid": "test-app", "roles": ["Mail.Send"], "exp": 1999999999})
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps({
        "token_type": "Bearer",
        "expires_in": 3599,
        "access_token": fake_token
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = OAuthTester.test_oauth_auth(
            tenant_or_token_url="my-tenant-id",
            client_id="my-client-id",
            auth_type="client_secret",
            client_secret="my-secret",
            scope="https://graph.microsoft.com/.default"
        )
        assert res["success"] is True
        assert res["status_code"] == 200
        assert res["access_token"] == fake_token
        assert res["claims"]["payload"]["appid"] == "test-app"

def test_jwt_bearer_assertion_success():
    assertion_jwt = make_dummy_jwt({"sub": "user@example.com", "exp": 1999999999})
    fake_token = make_dummy_jwt({"appid": "test-app", "scp": "Mail.Send", "exp": 1999999999})
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps({
        "token_type": "Bearer",
        "expires_in": 3599,
        "access_token": fake_token
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = OAuthTester.test_oauth_auth(
            tenant_or_token_url="my-tenant-id",
            client_id="my-client-id",
            auth_type="jwt_bearer",
            assertion=assertion_jwt,
            scope="https://graph.microsoft.com/.default"
        )
        assert res["success"] is True
        assert res["access_token"] == fake_token

def test_client_credentials_http_error():
    err_body = json.dumps({
        "error": "invalid_client",
        "error_description": "AADSTS7000215: Invalid client secret is provided."
    }).encode("utf-8")
    http_error = urllib.error.HTTPError(
        url="https://login.microsoftonline.com/test/oauth2/v2.0/token",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=MagicMock(read=MagicMock(return_value=err_body))
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        res = OAuthTester.test_oauth_auth(
            tenant_or_token_url="test",
            client_id="test",
            auth_type="client_secret",
            client_secret="wrong"
        )
        assert res["success"] is False
        assert res["status_code"] == 401
        assert res["error"] == "invalid_client"
        assert "Invalid client secret" in res["error_description"]

def test_api_oauth_endpoint():
    dummy_jwt = make_dummy_jwt({"appid": "api-test-app"})
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps({
        "token_type": "Bearer",
        "expires_in": 3600,
        "access_token": dummy_jwt
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        response = client.post("/oauth/test", json={
            "tenant_or_token_url": "my-tenant",
            "client_id": "test-id",
            "auth_type": "client_secret",
            "client_secret": "test-secret",
            "scope": "https://graph.microsoft.com/.default"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["claims"]["payload"]["appid"] == "api-test-app"

def test_api_jwt_decode_endpoint():
    token = make_dummy_jwt({"custom_claim": "hello_world"})
    response = client.post("/oauth/decode", json={"token": token})
    assert response.status_code == 200
    data = response.json()
    assert data["payload"]["custom_claim"] == "hello_world"

def test_cli_test_oauth_command():
    fake_token = make_dummy_jwt({"appid": "cli-app", "roles": ["Mail.Send"]})
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps({
        "token_type": "Bearer",
        "expires_in": 3600,
        "access_token": fake_token
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = runner.invoke(cli_app, [
            "test-oauth",
            "--tenant", "test-tenant",
            "--client-id", "test-client",
            "--client-secret", "secret",
            "--auth-type", "client_secret"
        ])
        assert res.exit_code == 0
        assert "Token Acquired Successfully" in res.stdout
