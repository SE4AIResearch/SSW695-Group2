from buma.gateway.health import status


def test_health_status():
    result = status()
    assert result["status"] == "ok"
    assert result["service"] == "buma"
