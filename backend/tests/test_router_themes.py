import respx
import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

ANIMETHEMES_RESPONSE = {
    "anime": [
        {
            "animethemes": [
                {
                    "id": 101,
                    "slug": "OP1",
                    "type": "OP",
                    "sequence": 1,
                    "song": {"title": "紅蓮の弓矢", "artists": [{"name": "Linked Horizon"}]},
                    "animethemeentries": [
                        {"videos": [{"link": "https://v.animethemes.moe/ShingekiNoKyojin-OP1.webm"}]}
                    ],
                }
            ]
        }
    ]
}


@respx.mock
def test_get_themes_returns_op():
    respx.get("https://api.bgm.tv/v0/subjects/8").mock(
        return_value=httpx.Response(200, json={"id": 8, "name": "進撃の巨人", "name_cn": "进击的巨人"})
    )
    respx.get("https://api.animethemes.moe/anime").mock(
        return_value=httpx.Response(200, json=ANIMETHEMES_RESPONSE)
    )
    resp = client.get("/api/themes/8")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["type"] == "OP"
    assert data[0]["song_title"] == "紅蓮の弓矢"
    assert data[0]["video_url"] == "https://v.animethemes.moe/ShingekiNoKyojin-OP1.webm"


@respx.mock
def test_get_themes_empty_when_not_found():
    respx.get("https://api.bgm.tv/v0/subjects/99999").mock(
        return_value=httpx.Response(200, json={"id": 99999, "name": "Unknown Anime", "name_cn": ""})
    )
    respx.get("https://api.animethemes.moe/anime").mock(
        return_value=httpx.Response(200, json={"anime": []})
    )
    resp = client.get("/api/themes/99999")
    assert resp.status_code == 200
    assert resp.json() == []
