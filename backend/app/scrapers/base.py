import re
import base64
from typing import Optional


def extract_btih(magnet: str) -> Optional[str]:
    """Extract infohash from magnet URI, return lowercase hex (40 chars)."""
    match = re.search(r'urn:btih:([A-Fa-f0-9]{40}|[A-Za-z2-7]{32})', magnet)
    if not match:
        return None
    raw = match.group(1)
    if len(raw) == 40:
        return raw.lower()
    try:
        padded = raw.upper() + '=' * ((8 - len(raw) % 8) % 8)
        return base64.b32decode(padded).hex()
    except Exception:
        return None


def build_magnet(btih: str, title: str) -> str:
    return f"magnet:?xt=urn:btih:{btih.upper()}&dn={title}"
