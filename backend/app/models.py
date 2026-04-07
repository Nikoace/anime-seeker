from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class AnimeSearchResult(BaseModel):
    id: int
    name: str
    name_cn: str
    image: str
    air_date: Optional[str] = None
    eps: Optional[int] = None
    rank: Optional[int] = None


class AnimeDetail(BaseModel):
    id: int
    name: str
    name_cn: str
    summary: str
    image: str
    tags: list[dict] = []
    rating: Optional[dict] = None
    air_date: Optional[str] = None
    eps: Optional[int] = None


class MusicEntry(BaseModel):
    id: int
    name: str
    name_cn: str
    image: str


class AnimeTheme(BaseModel):
    id: int
    slug: str
    type: str
    sequence: Optional[int] = None
    song_title: str
    artist: Optional[str] = None
    video_url: Optional[str] = None


class Torrent(BaseModel):
    title: str
    magnet: str
    size: Optional[str] = None
    date: Optional[str] = None
    source: str
    btih: str


class SourceError(BaseModel):
    source: str
    error: str


class TorrentsResponse(BaseModel):
    torrents: list[Torrent]
    errors: list[SourceError]

    @classmethod
    def deduplicated(cls, torrents: list[Torrent], errors: list[SourceError]) -> "TorrentsResponse":
        seen: set[str] = set()
        unique: list[Torrent] = []
        for t in torrents:
            key = t.btih.lower()
            if key not in seen:
                seen.add(key)
                unique.append(t)
        return cls(torrents=unique, errors=errors)
