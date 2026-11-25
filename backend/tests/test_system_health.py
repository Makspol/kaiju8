from app.main import favicon, health

def test_system_health():
    assert health() == {"status": "ok"}


def test_favicon_route_returns_svg():
    response = favicon()

    assert response.media_type == "image/svg+xml"
    assert b"<svg" in response.body
