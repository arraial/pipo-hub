#!usr/bin/env python3
import pytest
from fastapi.testclient import TestClient
from faststream.rabbit import TestRabbitBroker

from pipo_hub.config import settings
from pipo_hub.app import create_app, get_broker


@pytest.mark.integration
class TestHealthProbes:
    @pytest.fixture
    async def client(self):
        async with TestRabbitBroker(get_broker()) as br:
            yield TestClient(create_app(br))

    def test_livez(self, client):
        response = client.get("/livez", timeout=settings.probes.liveness.timeout)
        assert response.status_code == settings.probes.liveness.status_code

    def test_readyz(self, client):
        response = client.get("/readyz", timeout=settings.probes.readiness.timeout)
        assert response.status_code == 204
