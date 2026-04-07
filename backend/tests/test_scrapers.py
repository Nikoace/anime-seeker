from app.scrapers.base import extract_btih
from app.scrapers.nyaa import parse_nyaa_item


def test_extract_btih_hex():
    magnet = "magnet:?xt=urn:btih:AABB1122AABB1122AABB1122AABB1122AABB1122&dn=test"
    assert extract_btih(magnet) == "aabb1122aabb1122aabb1122aabb1122aabb1122"


def test_extract_btih_invalid():
    assert extract_btih("not-a-magnet") is None


def test_parse_nyaa_item_with_infohash():
    item = {
        "title": "[SubGroup] Shingeki no Kyojin - 01 [1080p]",
        "link": "https://nyaa.si/view/123456",
        "nyaa_infohash": "aabb1122aabb1122aabb1122aabb1122aabb1122",
        "nyaa_size": "350.2 MiB",
        "published": "Mon, 15 Jan 2024 12:00:00 +0000",
    }
    torrent = parse_nyaa_item(item)
    assert torrent is not None
    assert torrent.source == "nyaa"
    assert torrent.btih == "aabb1122aabb1122aabb1122aabb1122aabb1122"
    assert torrent.size == "350.2 MiB"
    assert "magnet:" in torrent.magnet


def test_parse_nyaa_item_no_hash_returns_none():
    item = {"title": "no hash", "link": "https://nyaa.si/view/1"}
    assert parse_nyaa_item(item) is None
