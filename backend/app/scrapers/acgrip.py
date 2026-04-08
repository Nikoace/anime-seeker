import feedparser
import httpx
from typing import Optional
from app.models import Torrent, SourceError
from app.scrapers.base import extract_btih, build_magnet

ACG_RSS = "https://acg.rip/bangumi/{bangumi_id}.xml"
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1"}


def parse_acgrip_item(item: dict) -> Optional[Torrent]:
    link = item.get("link", "")
    enclosures = item.get("enclosures", [{}])
    torrent_url = enclosures[0].get("url", link) if enclosures else link
    if "magnet:" in link:
        btih = extract_btih(link)
        magnet = link
    else:
        btih = extract_btih(torrent_url)
        magnet = build_magnet(btih, item.get("title", "")) if btih else None
    if not btih or not magnet:
        return None
    return Torrent(
        title=item.get("title", ""),
        magnet=magnet,
        size=None,
        date=item.get("published"),
        source="acgrip",
        btih=btih.lower(),
    )


async def fetch_acgrip(bangumi_id: int) -> tuple[list[Torrent], Optional[SourceError]]:
    url = ACG_RSS.format(bangumi_id=bangumi_id)
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=5) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        torrents = [t for item in feed.entries if (t := parse_acgrip_item(item)) is not None]
        return torrents, None
    except Exception as e:
        return [], SourceError(source="acgrip", error=str(e))
