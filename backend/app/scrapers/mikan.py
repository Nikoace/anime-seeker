import re
import feedparser
import httpx
from typing import Optional
from app.models import Torrent, SourceError
from app.scrapers.base import build_magnet

MIKAN_RSS = "https://mikanani.me/RSS/Search?searchstr={query}&subgroupid=0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; anime-bt-aggregator/0.1)",
    "Accept-Language": "ja,zh;q=0.9",
}


def parse_mikan_item(item: dict) -> Optional[Torrent]:
    enclosures = item.get("enclosures", [])
    torrent_url = next((e["url"] for e in enclosures if e.get("url", "").endswith(".torrent")), None)
    link = item.get("link", "")
    btih_match = re.search(r'/([A-Fa-f0-9]{40})\.torrent', torrent_url or link)
    if not btih_match:
        return None
    btih = btih_match.group(1).lower()
    return Torrent(
        title=item.get("title", ""),
        magnet=build_magnet(btih, item.get("title", "")),
        size=None,
        date=item.get("published"),
        source="mikan",
        btih=btih,
    )


async def fetch_mikan(query: str) -> tuple[list[Torrent], Optional[SourceError]]:
    """Best-effort: may fail on non-Japanese IPs due to Cloudflare."""
    url = MIKAN_RSS.format(query=query)
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=5) as client:
            resp = await client.get(url)
            if resp.status_code in (403, 503):
                return [], SourceError(source="mikan", error=f"Blocked (HTTP {resp.status_code})")
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        torrents = [t for item in feed.entries if (t := parse_mikan_item(item)) is not None]
        return torrents, None
    except Exception as e:
        return [], SourceError(source="mikan", error=str(e))
