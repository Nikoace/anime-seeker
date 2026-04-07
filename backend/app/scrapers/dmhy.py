import feedparser
import httpx
from typing import Optional
from app.models import Torrent, SourceError
from app.scrapers.base import extract_btih, build_magnet

DMHY_RSS = "https://dmhy.org/topics/rss/rss.xml?keyword={query}&sort_id=2&order=date-desc"
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1"}


def parse_dmhy_item(item: dict) -> Optional[Torrent]:
    link = item.get("link", "")
    enclosures = item.get("enclosures", [])
    magnet = next((e["url"] for e in enclosures if "magnet:" in e.get("url", "")), None)
    if not magnet:
        magnet = link if "magnet:" in link else None
    if not magnet:
        return None
    btih = extract_btih(magnet)
    if not btih:
        return None
    return Torrent(
        title=item.get("title", ""),
        magnet=magnet,
        size=None,
        date=item.get("published"),
        source="dmhy",
        btih=btih.lower(),
    )


async def fetch_dmhy(query: str) -> tuple[list[Torrent], Optional[SourceError]]:
    url = DMHY_RSS.format(query=query)
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        torrents = [t for item in feed.entries if (t := parse_dmhy_item(item)) is not None]
        return torrents, None
    except Exception as e:
        return [], SourceError(source="dmhy", error=str(e))
