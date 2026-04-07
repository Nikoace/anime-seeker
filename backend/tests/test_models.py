from app.models import Torrent, TorrentsResponse, AnimeSearchResult, SourceError


def test_torrent_btih_extraction():
    t = Torrent(
        title="[SubGroup] Anime S01E01 [1080p]",
        magnet="magnet:?xt=urn:btih:AABBCCDD11223344AABBCCDD11223344AABBCCDD&dn=test",
        size="350 MiB",
        date="2024-01-15",
        source="nyaa",
        btih="aabbccdd11223344aabbccdd11223344aabbccdd",
    )
    assert t.btih == "aabbccdd11223344aabbccdd11223344aabbccdd"


def test_torrents_response_deduplication():
    t1 = Torrent(title="A", magnet="magnet:?xt=urn:btih:AAAA1111AAAA1111AAAA1111AAAA1111AAAA1111", size=None, date=None, source="nyaa", btih="aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111")
    t2 = Torrent(title="A (duplicate)", magnet="magnet:?xt=urn:btih:AAAA1111AAAA1111AAAA1111AAAA1111AAAA1111", size=None, date=None, source="acgrip", btih="aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111")
    resp = TorrentsResponse.deduplicated([t1, t2], errors=[])
    assert len(resp.torrents) == 1
    assert resp.torrents[0].source == "nyaa"


def test_anime_search_result_fields():
    r = AnimeSearchResult(id=1, name="進撃の巨人", name_cn="进击的巨人", image="https://example.com/img.jpg", air_date="2013-04-07", eps=25, rank=1)
    assert r.name_cn == "进击的巨人"
