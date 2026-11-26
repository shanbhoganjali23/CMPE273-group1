import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agentmesh_analysis.config import Settings
from agentmesh_analysis.main import create_app


def test_health_without_model_credentials(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    with TestClient(create_app()) as client:
        for path in ['/health/live', '/health/ready']:
            response = client.get(path)
            assert response.status_code == 200
            assert response.json() == {'status': 'UP'}


def test_no_business_or_documentation_endpoints():
    with TestClient(create_app()) as client:
        assert client.post('/analysis', json={}).status_code == 404
        assert client.get('/traces/4bf92f3577b34da6a3ce929d0e0e4736/graph').status_code == 404
        assert client.get('/docs').status_code == 404


def test_settings_from_environment(monkeypatch):
    monkeypatch.setenv('ANALYSIS_PORT', '8101')
    assert Settings().port == 8101


@pytest.mark.parametrize('port', ['0', '65536', 'invalid'])
def test_invalid_port_rejected(monkeypatch, port):
    monkeypatch.setenv('ANALYSIS_PORT', port)
    with pytest.raises(ValidationError):
        Settings()
