import respx
import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BANGUMI_SEARCH_RESPONSE = {
    "total": 1,
    "list": [
        {
            "id": 8,
            "name": "進撃の巨人",
            "name_cn": "进击的巨人",
            "images": {"common": "https://lain.bgm.tv/pic/cover/c/abc.jpg"},
            "air_date": "2013-04-07",
            "eps": 25,
            "rank": 1,
        }
    ],
}

BANGUMI_DETAIL_RESPONSE = {
    "id": 8,
    "name": "進撃の巨人",
    "name_cn": "进击的巨人",
    "summary": "故事发生在...",
    "images": {"common": "https://lain.bgm.tv/pic/cover/c/abc.jpg"},
    "tags": [{"name": "动作"}],
    "rating": {"score": 8.9},
    "date": "2013-04-07",
    "eps": 25,
}


@respx.mock
def test_search_returns_results():
    respx.get("https://api.bgm.tv/search/subject/进击的巨人").mock(
        return_value=httpx.Response(200, json=BANGUMI_SEARCH_RESPONSE)
    )
    resp = client.get("/api/anime/search?q=进击的巨人")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name_cn"] == "进击的巨人"
    assert data[0]["id"] == 8


def test_search_empty_query_returns_422():
    resp = client.get("/api/anime/search")
    assert resp.status_code == 422


@respx.mock
def test_get_detail_returns_anime():
    respx.get("https://api.bgm.tv/v0/subjects/8").mock(
        return_value=httpx.Response(200, json=BANGUMI_DETAIL_RESPONSE)
    )
    resp = client.get("/api/anime/8")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name_cn"] == "进击的巨人"
    assert data["summary"] == "故事发生在..."
