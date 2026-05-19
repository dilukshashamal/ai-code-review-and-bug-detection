from fastapi.testclient import TestClient

from app.main import create_app


def test_graphql_allows_vite_frontend_origin() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/graphql",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
