"""Test the /personalities endpoint logic."""

import json


def _build_test_app():
    """Build the WSGI app in isolation (same logic as agent._build_wsgi_app)."""
    from src.personalities import REGISTRY

    def app(environ, start_response):
        path = environ.get("PATH_INFO", "")

        if path == "/personalities":
            profiles = [
                {"id": p.id, "display_name": p.display_name, "description": p.description}
                for p in REGISTRY.values()
            ]
            body = json.dumps(profiles).encode()
            start_response(
                "200 OK",
                [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]

        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"not found"]

    return app


def _call_wsgi(app, path):
    """Minimal WSGI test helper."""
    environ = {"PATH_INFO": path, "REQUEST_METHOD": "GET"}
    status_holder = {}
    headers_holder = {}

    def start_response(status, headers):
        status_holder["status"] = status
        headers_holder["headers"] = dict(headers)

    body_parts = app(environ, start_response)
    body = b"".join(body_parts)
    return status_holder["status"], headers_holder["headers"], body


def test_personalities_returns_json():
    app = _build_test_app()
    status, headers, body = _call_wsgi(app, "/personalities")

    assert status == "200 OK"
    assert headers["Content-Type"] == "application/json"

    data = json.loads(body)
    assert isinstance(data, list)
    assert len(data) >= 4


def test_personalities_has_required_fields():
    app = _build_test_app()
    _, _, body = _call_wsgi(app, "/personalities")

    data = json.loads(body)
    for profile in data:
        assert "id" in profile
        assert "display_name" in profile
        assert "description" in profile
        assert isinstance(profile["id"], str)
        assert len(profile["id"]) > 0


def test_personalities_contains_known_profiles():
    app = _build_test_app()
    _, _, body = _call_wsgi(app, "/personalities")

    ids = {p["id"] for p in json.loads(body)}
    assert "peruvian" in ids
    assert "mexican" in ids
    assert "kpop" in ids
    assert "roblox" in ids


def test_personalities_display_names():
    app = _build_test_app()
    _, _, body = _call_wsgi(app, "/personalities")

    by_id = {p["id"]: p for p in json.loads(body)}
    assert by_id["peruvian"]["display_name"] == "{name} Etnocacerista"
    assert by_id["roblox"]["display_name"] == "{name} Gamer"
