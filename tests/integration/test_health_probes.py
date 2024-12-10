#!usr/bin/env python3
import pytest
from pipo_hub.app import create_app, get_broker
from pipo_hub.broker import load_broker
from fastapi.testclient import TestClient
from faststream.rabbit import TestRabbitBroker


@pytest.mark.integration
class TestHealthProbes:
    @pytest.fixture
    async def client(self):
        async with TestRabbitBroker(get_broker()) as br:
            yield TestClient(create_app(br))

    def test_livez(self, client):
        response = client.get("/livez")
        assert response.status_code == 200

    def test_readyz(self, client):
        response = client.get("/readyz")
        assert response.status_code == 204
