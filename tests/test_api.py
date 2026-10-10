from fastapi.testclient import TestClient

from matchlens.api.main import app

c = TestClient(app)


def test_flow():
    assert c.get("/health").json()["status"] == "ok"
    r = c.post("/matches", json={"seed": 42}).json()
    mid = r["match_id"]
    assert r["event_count"] > 500
    assert "momentum" in c.get(f"/matches/{mid}/stats").json()
    assert c.get(f"/matches/{mid}/moments").status_code == 200
    ov = c.get(f"/matches/{mid}/overlays", params={"mode": "analyst", "lang": "fr"}).json()["overlays"]
    assert ov and ov[0]["lang"] == "fr"
    assert "recap" in c.get(f"/matches/{mid}/recap").json()


def test_404_and_422():
    assert c.get("/matches/nope/stats").status_code == 404
    c.post("/matches", json={"seed": 1})
    assert c.get("/matches/m_1/overlays", params={"lang": "zz"}).status_code == 422
