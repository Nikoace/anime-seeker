# 动画 BT 下载聚合站 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个中文动画 BT 下载聚合站，后端用 FastAPI 聚合四个种子源（nyaa/acg.rip/dmhy/mikan），前端用 Next.js 15 提供搜索、动画详情（含 OP/ED 播放）和磁力链列表。

**Architecture:** Python FastAPI 后端统一代理 Bangumi API、AnimeThemes API，并聚合四个 RSS 种子源（统一去重排序后返回）。Next.js 15 前端纯 UI，所有数据请求打向后端 API（本地通过 docker-compose 联通，生产分别部署 Render.com + Vercel）。

**Tech Stack:** Python 3.12, FastAPI, httpx, feedparser, cachetools, pydantic v2 / Next.js 15 (App Router), TypeScript, TailwindCSS, shadcn/ui, @tanstack/react-query

---

## File Map

```
gstack-demo-project/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app 入口，CORS 配置
│   │   ├── models.py            # 全局 Pydantic 模型
│   │   ├── cache.py             # 统一缓存实例（TTLCache）
│   │   ├── routers/
│   │   │   ├── anime.py         # GET /api/anime/search, /api/anime/{id}, /api/anime/{id}/music
│   │   │   ├── themes.py        # GET /api/themes/{bangumi_id}
│   │   │   └── torrents.py      # GET /api/torrents/{bangumi_id}
│   │   └── scrapers/
│   │       ├── base.py          # BaseScraper 抽象类
│   │       ├── nyaa.py          # nyaa.si RSS
│   │       ├── acgrip.py        # acg.rip RSS
│   │       ├── dmhy.py          # 动漫花园 RSS
│   │       └── mikan.py         # 蜜柑计划 RSS（best-effort）
│   ├── tests/
│   │   ├── test_models.py       # Pydantic 模型验证
│   │   ├── test_scrapers.py     # scraper 单元测试（mock HTTP）
│   │   ├── test_router_anime.py # /api/anime/* 集成测试
│   │   ├── test_router_themes.py
│   │   └── test_router_torrents.py
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # 首页：搜索框 + 6 个热门动画卡片
│   │   └── anime/[id]/
│   │       └── page.tsx         # 动画详情页
│   ├── components/
│   │   ├── SearchBar.tsx
│   │   ├── AnimeCard.tsx
│   │   ├── ThemePlayer.tsx      # OP/ED WebM 嵌入播放器
│   │   └── TorrentList.tsx      # 种子列表（含来源 badge + 磁力链复制）
│   ├── lib/
│   │   └── api.ts               # 所有后端 API 调用函数
│   ├── types/
│   │   └── index.ts             # 全局 TypeScript 类型（与后端 models.py 对应）
│   ├── next.config.ts
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml
└── README.md
```

---

## Task 1: 项目骨架初始化

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/requirements.txt`
- Create: `docker-compose.yml`

- [ ] **Step 1: 创建 backend 目录结构**

```bash
cd /home/niko/hobby/gstack-demo-project
mkdir -p backend/app/routers backend/app/scrapers backend/tests
touch backend/app/__init__.py backend/app/routers/__init__.py backend/app/scrapers/__init__.py backend/tests/__init__.py
```

- [ ] **Step 2: 写 `backend/requirements.txt`**

```
fastapi==0.115.6
uvicorn[standard]==0.32.1
httpx==0.28.1
feedparser==6.0.11
cachetools==5.5.0
pydantic==2.10.4
pytest==8.3.4
pytest-asyncio==0.24.0
httpx==0.28.1
respx==0.21.1
```

- [ ] **Step 3: 写 `backend/pyproject.toml`**

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 4: 初始化 Next.js 项目**

```bash
cd /home/niko/hobby/gstack-demo-project
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"
```

Expected: 创建 `frontend/` 目录，包含 Next.js 15 骨架。

- [ ] **Step 5: 安装前端依赖**

```bash
cd frontend
npx shadcn@latest init -d
npm install @tanstack/react-query axios
```

- [ ] **Step 6: 写 `docker-compose.yml`**

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
```

- [ ] **Step 7: 写 `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 8: 验证 backend 可以安装依赖**

```bash
cd /home/niko/hobby/gstack-demo-project/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -c "import fastapi, httpx, feedparser, cachetools; print('OK')"
```

Expected: `OK`

- [ ] **Step 9: Commit**

```bash
cd /home/niko/hobby/gstack-demo-project
git init
git add .
git commit -m "chore: project skeleton — FastAPI backend + Next.js 15 frontend"
```

---

## Task 2: 后端 Pydantic 模型 + 缓存

**Files:**
- Create: `backend/app/models.py`
- Create: `backend/app/cache.py`
- Create: `backend/tests/test_models.py`

- [ ] **Step 1: 写失败的测试**

```python
# backend/tests/test_models.py
from app.models import Torrent, TorrentsResponse, AnimeSearchResult, AnimeDetail, AnimeTheme

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
    assert resp.torrents[0].source == "nyaa"  # keeps first occurrence

def test_anime_search_result_fields():
    r = AnimeSearchResult(id=1, name="進撃の巨人", name_cn="进击的巨人", image="https://example.com/img.jpg", air_date="2013-04-07", eps=25, rank=1)
    assert r.name_cn == "进击的巨人"
```

- [ ] **Step 2: 确认测试失败**

```bash
cd backend && source .venv/bin/activate
pytest tests/test_models.py -v
```

Expected: `ImportError` (models.py 不存在)

- [ ] **Step 3: 写 `backend/app/models.py`**

```python
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class AnimeSearchResult(BaseModel):
    id: int
    name: str           # 日文标题
    name_cn: str        # 中文标题（可能为空字符串）
    image: str          # 封面图 URL
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
    type: str           # "OP" or "ED"
    sequence: Optional[int] = None
    song_title: str
    artist: Optional[str] = None
    video_url: Optional[str] = None   # WebM URL from AnimeThemes


class Torrent(BaseModel):
    title: str
    magnet: str
    size: Optional[str] = None
    date: Optional[str] = None
    source: str         # "nyaa" | "acgrip" | "dmhy" | "mikan"
    btih: str           # lowercase hex infohash, dedup key


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
```

- [ ] **Step 4: 写 `backend/app/cache.py`**

```python
from cachetools import TTLCache
import threading

_lock = threading.Lock()

# TTLs in seconds
bangumi_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)    # 60 min
themes_cache: TTLCache  = TTLCache(maxsize=200, ttl=21600)   # 360 min
torrents_cache: TTLCache = TTLCache(maxsize=200, ttl=300)    # 5 min
```

- [ ] **Step 5: 运行测试，确认通过**

```bash
pytest tests/test_models.py -v
```

Expected:
```
test_torrent_btih_extraction PASSED
test_torrents_response_deduplication PASSED
test_anime_search_result_fields PASSED
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/models.py backend/app/cache.py backend/tests/test_models.py
git commit -m "feat: add Pydantic models and TTL cache instances"
```

---

## Task 3: FastAPI 入口 + Bangumi 动画搜索 API

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/routers/anime.py`
- Create: `backend/tests/test_router_anime.py`

- [ ] **Step 1: 写失败的测试**

```python
# backend/tests/test_router_anime.py
import pytest
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
    "tags": [{"name": "动作"}, {"name": "热血"}],
    "rating": {"score": 8.9},
    "air_date": "2013-04-07",
    "eps": 25,
}


@respx.mock
def test_search_returns_results():
    respx.get("https://api.bgm.tv/search/subject/%E8%BF%9B%E5%87%BB%E7%9A%84%E5%B7%A8%E4%BA%BA").mock(
        return_value=httpx.Response(200, json=BANGUMI_SEARCH_RESPONSE)
    )
    resp = client.get("/api/anime/search?q=进击的巨人")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name_cn"] == "进击的巨人"
    assert data[0]["id"] == 8


@respx.mock
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
```

- [ ] **Step 2: 确认测试失败**

```bash
pytest tests/test_router_anime.py -v
```

Expected: `ImportError` (main.py 不存在)

- [ ] **Step 3: 写 `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import anime, themes, torrents

app = FastAPI(title="Anime BT Aggregator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(anime.router, prefix="/api/anime", tags=["anime"])
app.include_router(themes.router, prefix="/api/themes", tags=["themes"])
app.include_router(torrents.router, prefix="/api/torrents", tags=["torrents"])


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: 写 `backend/app/routers/anime.py`**

```python
from fastapi import APIRouter, Query, HTTPException
import httpx
from app.models import AnimeSearchResult, AnimeDetail, MusicEntry
from app.cache import bangumi_cache

router = APIRouter()
BANGUMI_BASE = "https://api.bgm.tv"
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1 (https://github.com/yourname/anime-bt-aggregator)"}


def _search_cache_key(q: str) -> str:
    return f"search:{q}"


@router.get("/search", response_model=list[AnimeSearchResult])
async def search_anime(q: str = Query(..., min_length=1)):
    key = _search_cache_key(q)
    if key in bangumi_cache:
        return bangumi_cache[key]

    url = f"{BANGUMI_BASE}/search/subject/{q}"
    params = {"type": 2, "responseGroup": "small", "max_results": 20}
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Bangumi API error")
        raw = resp.json()

    items = raw.get("list", [])
    results = [
        AnimeSearchResult(
            id=item["id"],
            name=item.get("name", ""),
            name_cn=item.get("name_cn") or item.get("name", ""),
            image=item.get("images", {}).get("common", ""),
            air_date=item.get("air_date"),
            eps=item.get("eps"),
            rank=item.get("rank"),
        )
        for item in items
    ]
    bangumi_cache[key] = results
    return results


@router.get("/{subject_id}", response_model=AnimeDetail)
async def get_anime_detail(subject_id: int):
    key = f"detail:{subject_id}"
    if key in bangumi_cache:
        return bangumi_cache[key]

    url = f"{BANGUMI_BASE}/v0/subjects/{subject_id}"
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Anime not found")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Bangumi API error")
        raw = resp.json()

    result = AnimeDetail(
        id=raw["id"],
        name=raw.get("name", ""),
        name_cn=raw.get("name_cn") or raw.get("name", ""),
        summary=raw.get("summary", ""),
        image=raw.get("images", {}).get("common", ""),
        tags=raw.get("tags", []),
        rating=raw.get("rating"),
        air_date=raw.get("date"),
        eps=raw.get("eps"),
    )
    bangumi_cache[key] = result
    return result


@router.get("/{subject_id}/music", response_model=list[MusicEntry])
async def get_anime_music(subject_id: int):
    key = f"music:{subject_id}"
    if key in bangumi_cache:
        return bangumi_cache[key]

    url = f"{BANGUMI_BASE}/v0/subjects/{subject_id}/subjects"
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return []  # best-effort: return empty on error
        raw = resp.json()

    # Bangumi subject type 3 = Music
    music = [
        MusicEntry(
            id=item["id"],
            name=item.get("name", ""),
            name_cn=item.get("name_cn") or item.get("name", ""),
            image=item.get("images", {}).get("common", ""),
        )
        for item in raw
        if item.get("type") == 3
    ]
    bangumi_cache[key] = music
    return music
```

- [ ] **Step 5: 创建 themes 和 torrents 路由占位（避免 import 错误）**

```python
# backend/app/routers/themes.py
from fastapi import APIRouter
router = APIRouter()
```

```python
# backend/app/routers/torrents.py
from fastapi import APIRouter
router = APIRouter()
```

- [ ] **Step 6: 运行测试**

```bash
pytest tests/test_router_anime.py -v
```

Expected:
```
test_search_returns_results PASSED
test_search_empty_query_returns_422 PASSED
test_get_detail_returns_anime PASSED
```

- [ ] **Step 7: 手动验证**

```bash
uvicorn app.main:app --reload &
curl "http://localhost:8000/api/anime/search?q=进击的巨人" | python -m json.tool | head -20
curl "http://localhost:8000/health"
```

Expected: JSON 结果，`{"status":"ok"}`

- [ ] **Step 8: Commit**

```bash
git add backend/app/main.py backend/app/routers/ backend/tests/test_router_anime.py
git commit -m "feat: Bangumi anime search and detail API"
```

---

## Task 4: AnimeThemes OP/ED 集成

**Files:**
- Modify: `backend/app/routers/themes.py`
- Create: `backend/tests/test_router_themes.py`

- [ ] **Step 1: 写失败的测试**

```python
# backend/tests/test_router_themes.py
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
                        {
                            "videos": [
                                {"link": "https://v.animethemes.moe/ShingekiNoKyojin-OP1.webm"}
                            ]
                        }
                    ],
                }
            ]
        }
    ]
}


@respx.mock
def test_get_themes_returns_op_ed():
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
def test_get_themes_returns_empty_on_not_found():
    respx.get("https://api.animethemes.moe/anime").mock(
        return_value=httpx.Response(200, json={"anime": []})
    )
    resp = client.get("/api/themes/99999")
    assert resp.status_code == 200
    assert resp.json() == []
```

- [ ] **Step 2: 确认失败**

```bash
pytest tests/test_router_themes.py -v
```

Expected: `FAILED` (themes router 是占位符)

- [ ] **Step 3: 实现 `backend/app/routers/themes.py`**

```python
from fastapi import APIRouter
import httpx
from app.models import AnimeTheme
from app.cache import themes_cache, bangumi_cache

router = APIRouter()
ANIMETHEMES_BASE = "https://api.animethemes.moe"
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1"}


async def _get_bangumi_name(subject_id: int) -> str:
    """Fetch the anime name to use for AnimeThemes title search."""
    key = f"detail:{subject_id}"
    if key in bangumi_cache:
        return bangumi_cache[key].name  # Japanese title works better for AnimeThemes
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        resp = await client.get(f"https://api.bgm.tv/v0/subjects/{subject_id}")
        if resp.status_code == 200:
            data = resp.json()
            return data.get("name", "")
    return ""


@router.get("/{bangumi_id}", response_model=list[AnimeTheme])
async def get_themes(bangumi_id: int):
    cache_key = f"themes:{bangumi_id}"
    if cache_key in themes_cache:
        return themes_cache[cache_key]

    anime_name = await _get_bangumi_name(bangumi_id)
    if not anime_name:
        return []

    params = {
        "filter[name]": anime_name,
        "include": "animethemes.animethemeentries.videos,animethemes.song.artists",
        "fields[anime]": "name",
        "fields[animetheme]": "id,slug,type,sequence",
        "fields[song]": "title",
        "fields[artist]": "name",
        "fields[video]": "link",
    }
    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
        resp = await client.get(f"{ANIMETHEMES_BASE}/anime", params=params)
        if resp.status_code != 200:
            return []
        raw = resp.json()

    themes: list[AnimeTheme] = []
    for anime in raw.get("anime", []):
        for theme in anime.get("animethemes", []):
            # get first video from first entry
            video_url = None
            entries = theme.get("animethemeentries", [])
            if entries and entries[0].get("videos"):
                video_url = entries[0]["videos"][0].get("link")

            song = theme.get("song", {})
            artists = song.get("artists", [])
            artist_name = artists[0]["name"] if artists else None

            themes.append(AnimeTheme(
                id=theme["id"],
                slug=theme["slug"],
                type=theme.get("type", "OP"),
                sequence=theme.get("sequence"),
                song_title=song.get("title", "Unknown"),
                artist=artist_name,
                video_url=video_url,
            ))

    themes_cache[cache_key] = themes
    return themes
```

- [ ] **Step 4: 运行测试**

```bash
pytest tests/test_router_themes.py -v
```

Expected:
```
test_get_themes_returns_op_ed PASSED
test_get_themes_returns_empty_on_not_found PASSED
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/themes.py backend/tests/test_router_themes.py
git commit -m "feat: AnimeThemes OP/ED integration"
```

---

## Task 5: RSS Scrapers + 种子聚合 API

**Files:**
- Create: `backend/app/scrapers/base.py`
- Create: `backend/app/scrapers/nyaa.py`
- Create: `backend/app/scrapers/acgrip.py`
- Create: `backend/app/scrapers/dmhy.py`
- Create: `backend/app/scrapers/mikan.py`
- Modify: `backend/app/routers/torrents.py`
- Create: `backend/tests/test_scrapers.py`
- Create: `backend/tests/test_router_torrents.py`

- [ ] **Step 1: 写 scraper 单元测试**

```python
# backend/tests/test_scrapers.py
import pytest
from app.scrapers.nyaa import extract_btih, parse_nyaa_item
from app.scrapers.base import BaseScraper

def test_extract_btih_hex():
    magnet = "magnet:?xt=urn:btih:AABB1122AABB1122AABB1122AABB1122AABB1122&dn=test"
    assert extract_btih(magnet) == "aabb1122aabb1122aabb1122aabb1122aabb1122"

def test_extract_btih_base32():
    # Base32 infohash (32 chars A-Z2-7)
    magnet = "magnet:?xt=urn:btih:MFRA2YLNMFRA2YLNMFRA2YLNMFQ======&dn=test"
    btih = extract_btih(magnet)
    assert btih is not None
    assert len(btih) == 40  # converted to hex

def test_extract_btih_invalid():
    assert extract_btih("not-a-magnet") is None

def test_parse_nyaa_item_basic():
    item = {
        "title": "[SubGroup] Shingeki no Kyojin - 01 [1080p]",
        "link": "https://nyaa.si/download/123456.torrent",
        "nyaa_infohash": "aabb1122aabb1122aabb1122aabb1122aabb1122",
        "nyaa_size": "350.2 MiB",
        "published": "Mon, 15 Jan 2024 12:00:00 +0000",
        "guid": "https://nyaa.si/view/123456",
    }
    torrent = parse_nyaa_item(item)
    assert torrent.source == "nyaa"
    assert torrent.btih == "aabb1122aabb1122aabb1122aabb1122aabb1122"
    assert torrent.size == "350.2 MiB"
    assert "magnet:" in torrent.magnet
```

- [ ] **Step 2: 确认测试失败**

```bash
pytest tests/test_scrapers.py -v
```

Expected: `ImportError`

- [ ] **Step 3: 写 `backend/app/scrapers/base.py`**

```python
import re
import base64
from typing import Optional


def extract_btih(magnet: str) -> Optional[str]:
    """Extract infohash from magnet URI, always return lowercase hex (40 chars)."""
    match = re.search(r'urn:btih:([A-Fa-f0-9]{40}|[A-Za-z2-7]{32})', magnet)
    if not match:
        return None
    raw = match.group(1)
    if len(raw) == 40:
        return raw.lower()
    # Base32 → bytes → hex
    try:
        padded = raw.upper() + '=' * ((8 - len(raw) % 8) % 8)
        return base64.b32decode(padded).hex()
    except Exception:
        return None


def build_magnet(btih: str, title: str) -> str:
    return f"magnet:?xt=urn:btih:{btih.upper()}&dn={title}"
```

- [ ] **Step 4: 写 `backend/app/scrapers/nyaa.py`**

```python
import feedparser
import httpx
from typing import Optional
from app.models import Torrent, SourceError
from app.scrapers.base import extract_btih, build_magnet

NYAA_RSS = "https://nyaa.si/?page=rss&q={query}&c=1_0&f=0"
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1"}


def parse_nyaa_item(item: dict) -> Optional[Torrent]:
    # nyaa provides nyaa_infohash tag in their RSS
    btih = item.get("nyaa_infohash") or extract_btih(item.get("link", ""))
    if not btih:
        return None
    btih = btih.lower()
    title = item.get("title", "")
    magnet = item.get("link", "") if "magnet:" in item.get("link", "") else build_magnet(btih, title)
    return Torrent(
        title=title,
        magnet=magnet if magnet.startswith("magnet:") else build_magnet(btih, title),
        size=item.get("nyaa_size"),
        date=item.get("published"),
        source="nyaa",
        btih=btih,
    )


async def fetch_nyaa(query: str) -> tuple[list[Torrent], Optional[SourceError]]:
    url = NYAA_RSS.format(query=query)
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        torrents = [t for item in feed.entries if (t := parse_nyaa_item(item)) is not None]
        return torrents, None
    except Exception as e:
        return [], SourceError(source="nyaa", error=str(e))
```

- [ ] **Step 5: 写 `backend/app/scrapers/acgrip.py`**

```python
import feedparser
import httpx
from typing import Optional
from app.models import Torrent, SourceError
from app.scrapers.base import extract_btih, build_magnet

ACG_RSS = "https://acg.rip/bangumi/{bangumi_id}.xml"
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1"}


def parse_acgrip_item(item: dict) -> Optional[Torrent]:
    link = item.get("link", "")
    enclosure = item.get("enclosures", [{}])[0]
    torrent_url = enclosure.get("url", link)
    # acg.rip provides magnet in link for some entries
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
        async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        torrents = [t for item in feed.entries if (t := parse_acgrip_item(item)) is not None]
        return torrents, None
    except Exception as e:
        return [], SourceError(source="acgrip", error=str(e))
```

- [ ] **Step 6: 写 `backend/app/scrapers/dmhy.py`**

```python
import feedparser
import httpx
from typing import Optional
from app.models import Torrent, SourceError
from app.scrapers.base import extract_btih, build_magnet

DMHY_RSS = "https://dmhy.org/topics/rss/rss.xml?keyword={query}&sort_id=2&order=date-desc"
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1"}


def parse_dmhy_item(item: dict) -> Optional[Torrent]:
    link = item.get("link", "")
    # dmhy provides magnet as enclosure
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
```

- [ ] **Step 7: 写 `backend/app/scrapers/mikan.py`**

```python
import feedparser
import httpx
from typing import Optional
from app.models import Torrent, SourceError
from app.scrapers.base import extract_btih, build_magnet

MIKAN_RSS = "https://mikanani.me/RSS/Search?searchstr={query}&subgroupid=0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; anime-bt-aggregator/0.1)",
    "Accept-Language": "ja,zh;q=0.9",
}


def parse_mikan_item(item: dict) -> Optional[Torrent]:
    link = item.get("link", "")
    enclosures = item.get("enclosures", [])
    torrent_url = next((e["url"] for e in enclosures if e.get("url", "").endswith(".torrent")), None)
    # mikan torrents don't embed magnet directly, extract btih from torrent URL
    # URL format: https://mikanani.me/Download/xxxx/{btih}.torrent
    import re
    btih_match = re.search(r'/([A-Fa-f0-9]{40})\.torrent', torrent_url or link)
    if not btih_match:
        return None
    btih = btih_match.group(1).lower()
    magnet = build_magnet(btih, item.get("title", ""))
    return Torrent(
        title=item.get("title", ""),
        magnet=magnet,
        size=None,
        date=item.get("published"),
        source="mikan",
        btih=btih,
    )


async def fetch_mikan(query: str) -> tuple[list[Torrent], Optional[SourceError]]:
    """Best-effort: may fail on non-Japanese IPs due to Cloudflare."""
    url = MIKAN_RSS.format(query=query)
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code in (403, 503):
                return [], SourceError(source="mikan", error=f"Blocked (HTTP {resp.status_code})")
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        torrents = [t for item in feed.entries if (t := parse_mikan_item(item)) is not None]
        return torrents, None
    except Exception as e:
        return [], SourceError(source="mikan", error=str(e))
```

- [ ] **Step 8: 运行 scraper 测试**

```bash
pytest tests/test_scrapers.py -v
```

Expected: 全部 PASSED

- [ ] **Step 9: 实现 `backend/app/routers/torrents.py`**

```python
import asyncio
from fastapi import APIRouter, Query
import httpx
from app.models import TorrentsResponse, SourceError
from app.scrapers.nyaa import fetch_nyaa
from app.scrapers.acgrip import fetch_acgrip
from app.scrapers.dmhy import fetch_dmhy
from app.scrapers.mikan import fetch_mikan
from app.cache import torrents_cache, bangumi_cache

router = APIRouter()
BANGUMI_HEADERS = {"User-Agent": "anime-bt-aggregator/0.1"}


async def _get_anime_name(bangumi_id: int) -> str:
    key = f"detail:{bangumi_id}"
    if key in bangumi_cache:
        return bangumi_cache[key].name_cn or bangumi_cache[key].name
    async with httpx.AsyncClient(headers=BANGUMI_HEADERS, timeout=10) as client:
        resp = await client.get(f"https://api.bgm.tv/v0/subjects/{bangumi_id}")
        if resp.status_code == 200:
            data = resp.json()
            return data.get("name_cn") or data.get("name", "")
    return ""


@router.get("/{bangumi_id}", response_model=TorrentsResponse)
async def get_torrents(bangumi_id: int):
    cache_key = f"torrents:{bangumi_id}"
    if cache_key in torrents_cache:
        return torrents_cache[cache_key]

    query = await _get_anime_name(bangumi_id)
    if not query:
        return TorrentsResponse(torrents=[], errors=[SourceError(source="all", error="Anime not found")])

    # Fetch all sources concurrently; failures are non-fatal
    results = await asyncio.gather(
        fetch_nyaa(query),
        fetch_acgrip(bangumi_id),
        fetch_dmhy(query),
        fetch_mikan(query),
        return_exceptions=False,
    )

    all_torrents = []
    errors = []
    for torrents, error in results:
        all_torrents.extend(torrents)
        if error:
            errors.append(error)

    # Sort by date descending (None dates go to end)
    all_torrents.sort(key=lambda t: t.date or "", reverse=True)

    response = TorrentsResponse.deduplicated(all_torrents, errors)
    torrents_cache[cache_key] = response
    return response
```

- [ ] **Step 10: 写 torrents 路由测试**

```python
# backend/tests/test_router_torrents.py
import respx
import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BANGUMI_DETAIL = {
    "id": 8, "name": "進撃の巨人", "name_cn": "进击的巨人",
    "summary": "", "images": {"common": ""}, "date": None, "eps": None, "tags": [],
}

NYAA_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:nyaa="https://nyaa.si/xmlns/nyaa">
<channel>
  <item>
    <title>[SubGroup] Shingeki 01 [1080p]</title>
    <link>https://nyaa.si/view/1</link>
    <nyaa:infohash>aabb1122aabb1122aabb1122aabb1122aabb1122</nyaa:infohash>
    <nyaa:size>350.2 MiB</nyaa:size>
    <pubDate>Mon, 15 Jan 2024 12:00:00 +0000</pubDate>
  </item>
</channel>
</rss>"""


@respx.mock
def test_get_torrents_aggregates_sources():
    respx.get("https://api.bgm.tv/v0/subjects/8").mock(
        return_value=httpx.Response(200, json=BANGUMI_DETAIL)
    )
    # Mock nyaa (returns 1 result)
    respx.get("https://nyaa.si/").mock(return_value=httpx.Response(200, text=NYAA_RSS_XML))
    # Mock other sources to return empty RSS
    empty_rss = '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'
    respx.get("https://acg.rip/bangumi/8.xml").mock(return_value=httpx.Response(200, text=empty_rss))
    respx.get("https://dmhy.org/topics/rss/rss.xml").mock(return_value=httpx.Response(200, text=empty_rss))
    respx.get("https://mikanani.me/RSS/Search").mock(return_value=httpx.Response(200, text=empty_rss))

    resp = client.get("/api/torrents/8")
    assert resp.status_code == 200
    data = resp.json()
    assert "torrents" in data
    assert "errors" in data


@respx.mock
def test_get_torrents_partial_failure_returns_available():
    respx.get("https://api.bgm.tv/v0/subjects/8").mock(
        return_value=httpx.Response(200, json=BANGUMI_DETAIL)
    )
    respx.get("https://nyaa.si/").mock(return_value=httpx.Response(200, text=NYAA_RSS_XML))
    # Simulate acg.rip timeout
    respx.get("https://acg.rip/bangumi/8.xml").mock(side_effect=httpx.TimeoutException("timeout"))
    empty_rss = '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'
    respx.get("https://dmhy.org/topics/rss/rss.xml").mock(return_value=httpx.Response(200, text=empty_rss))
    respx.get("https://mikanani.me/RSS/Search").mock(return_value=httpx.Response(200, text=empty_rss))

    resp = client.get("/api/torrents/8")
    assert resp.status_code == 200
    data = resp.json()
    # Should still return available torrents + list the error
    errors = data["errors"]
    assert any(e["source"] == "acgrip" for e in errors)
```

- [ ] **Step 11: 运行所有测试**

```bash
pytest tests/ -v
```

Expected: 全部 PASSED

- [ ] **Step 12: Commit**

```bash
git add backend/app/scrapers/ backend/app/routers/torrents.py backend/tests/test_scrapers.py backend/tests/test_router_torrents.py
git commit -m "feat: RSS scrapers for nyaa/acgrip/dmhy/mikan + torrent aggregation API"
```

---

## Task 6: 前端 — API 类型 + 数据层

**Files:**
- Create: `frontend/types/index.ts`
- Create: `frontend/lib/api.ts`
- Modify: `frontend/app/layout.tsx`

- [ ] **Step 1: 写 `frontend/types/index.ts`**

```typescript
export interface AnimeSearchResult {
  id: number;
  name: string;       // 日文标题
  name_cn: string;    // 中文标题
  image: string;
  air_date: string | null;
  eps: number | null;
  rank: number | null;
}

export interface AnimeDetail {
  id: number;
  name: string;
  name_cn: string;
  summary: string;
  image: string;
  tags: { name: string }[];
  rating: { score: number } | null;
  air_date: string | null;
  eps: number | null;
}

export interface MusicEntry {
  id: number;
  name: string;
  name_cn: string;
  image: string;
}

export interface AnimeTheme {
  id: number;
  slug: string;
  type: "OP" | "ED";
  sequence: number | null;
  song_title: string;
  artist: string | null;
  video_url: string | null;
}

export interface Torrent {
  title: string;
  magnet: string;
  size: string | null;
  date: string | null;
  source: "nyaa" | "acgrip" | "dmhy" | "mikan";
  btih: string;
}

export interface TorrentsResponse {
  torrents: Torrent[];
  errors: { source: string; error: string }[];
}
```

- [ ] **Step 2: 写 `frontend/lib/api.ts`**

```typescript
import type { AnimeSearchResult, AnimeDetail, MusicEntry, AnimeTheme, TorrentsResponse } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  searchAnime: (q: string) =>
    fetchJSON<AnimeSearchResult[]>(`/api/anime/search?q=${encodeURIComponent(q)}`),

  getAnimeDetail: (id: number) =>
    fetchJSON<AnimeDetail>(`/api/anime/${id}`),

  getAnimeMusic: (id: number) =>
    fetchJSON<MusicEntry[]>(`/api/anime/${id}/music`),

  getAnimeThemes: (id: number) =>
    fetchJSON<AnimeTheme[]>(`/api/themes/${id}`),

  getTorrents: (id: number) =>
    fetchJSON<TorrentsResponse>(`/api/torrents/${id}`),
};
```

- [ ] **Step 3: 修改 `frontend/app/layout.tsx` 加全局 QueryClientProvider**

```typescript
// frontend/app/layout.tsx
"use client";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </body>
    </html>
  );
}
```

注意：layout.tsx 加了 `"use client"` 后需要把 metadata 移到单独的文件，或删除 metadata export（开发阶段直接删除即可）。

- [ ] **Step 4: 验证 TypeScript 编译**

```bash
cd frontend
npx tsc --noEmit
```

Expected: 无错误

- [ ] **Step 5: Commit**

```bash
git add frontend/types/ frontend/lib/ frontend/app/layout.tsx
git commit -m "feat: frontend types and API client"
```

---

## Task 7: 前端 — 搜索首页

**Files:**
- Modify: `frontend/app/page.tsx`
- Create: `frontend/components/SearchBar.tsx`
- Create: `frontend/components/AnimeCard.tsx`

- [ ] **Step 1: 写 `frontend/components/SearchBar.tsx`**

```typescript
"use client";
import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function SearchBar({ defaultValue = "" }: { defaultValue?: string }) {
  const [q, setQ] = useState(defaultValue);
  const router = useRouter();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (q.trim()) router.push(`/?q=${encodeURIComponent(q.trim())}`);
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 w-full max-w-xl">
      <Input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="搜索动画名称（中文或日文）..."
        className="flex-1"
      />
      <Button type="submit">搜索</Button>
    </form>
  );
}
```

- [ ] **Step 2: 写 `frontend/components/AnimeCard.tsx`**

```typescript
import Link from "next/link";
import Image from "next/image";
import type { AnimeSearchResult } from "@/types";

export function AnimeCard({ anime }: { anime: AnimeSearchResult }) {
  const title = anime.name_cn || anime.name;
  return (
    <Link href={`/anime/${anime.id}`} className="group block rounded-lg overflow-hidden border hover:border-primary transition-colors">
      <div className="relative aspect-[3/4] bg-muted">
        {anime.image ? (
          <Image
            src={anime.image}
            alt={title}
            fill
            className="object-cover group-hover:scale-105 transition-transform"
            sizes="(max-width: 768px) 50vw, 200px"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-muted-foreground text-sm">无封面</div>
        )}
      </div>
      <div className="p-2">
        <p className="font-medium text-sm line-clamp-2">{title}</p>
        {anime.air_date && <p className="text-xs text-muted-foreground mt-1">{anime.air_date.slice(0, 4)}</p>}
      </div>
    </Link>
  );
}
```

- [ ] **Step 3: 写 `frontend/app/page.tsx`**

```typescript
import { Suspense } from "react";
import { SearchBar } from "@/components/SearchBar";
import { AnimeCard } from "@/components/AnimeCard";
import { api } from "@/lib/api";
import type { AnimeSearchResult } from "@/types";

// 热门动画硬编码（v1 静态展示，后续可接 Bangumi 热门 API）
const POPULAR_IDS = [8, 328, 21, 245, 975, 34];

async function PopularAnime() {
  const results = await Promise.allSettled(POPULAR_IDS.map((id) => api.getAnimeDetail(id)));
  const animes = results
    .filter((r): r is PromiseFulfilledResult<AnimeSearchResult> => r.status === "fulfilled")
    .map((r) => r.value as AnimeSearchResult);
  return (
    <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
      {animes.map((a) => <AnimeCard key={a.id} anime={a} />)}
    </div>
  );
}

async function SearchResults({ q }: { q: string }) {
  try {
    const results = await api.searchAnime(q);
    if (results.length === 0) {
      return <p className="text-muted-foreground text-center py-8">没有找到相关动画</p>;
    }
    return (
      <div className="grid grid-cols-3 md:grid-cols-5 gap-4">
        {results.map((a) => <AnimeCard key={a.id} anime={a} />)}
      </div>
    );
  } catch {
    return <p className="text-destructive text-center py-8">搜索失败，请稍后重试</p>;
  }
}

export default async function HomePage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q } = await searchParams;
  return (
    <main className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="flex flex-col items-center gap-6 mb-8">
        <h1 className="text-3xl font-bold">动画 BT 聚合</h1>
        <SearchBar defaultValue={q ?? ""} />
      </div>
      {q ? (
        <Suspense fallback={<p className="text-center">搜索中...</p>}>
          <SearchResults q={q} />
        </Suspense>
      ) : (
        <>
          <h2 className="text-lg font-semibold mb-4">热门动画</h2>
          <Suspense fallback={<p>加载中...</p>}>
            <PopularAnime />
          </Suspense>
        </>
      )}
    </main>
  );
}
```

- [ ] **Step 4: 配置 `frontend/next.config.ts` 允许 Bangumi 图片域名**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "lain.bgm.tv" },
      { protocol: "https", hostname: "*.bgm.tv" },
    ],
  },
};

export default nextConfig;
```

- [ ] **Step 5: 启动开发服务器验证**

```bash
cd frontend
# 先确保后端也在跑: cd backend && uvicorn app.main:app --reload &
npm run dev
```

打开 http://localhost:3000，应显示：
- 标题 "动画 BT 聚合"
- 搜索框
- 6 个热门动画卡片（需要后端运行）

- [ ] **Step 6: Commit**

```bash
git add frontend/components/SearchBar.tsx frontend/components/AnimeCard.tsx frontend/app/page.tsx frontend/next.config.ts
git commit -m "feat: search homepage with anime cards"
```

---

## Task 8: 前端 — 动画详情页

**Files:**
- Create: `frontend/app/anime/[id]/page.tsx`
- Create: `frontend/components/ThemePlayer.tsx`
- Create: `frontend/components/TorrentList.tsx`

- [ ] **Step 1: 写 `frontend/components/ThemePlayer.tsx`**

```typescript
"use client";
import { useState } from "react";
import type { AnimeTheme } from "@/types";
import { Badge } from "@/components/ui/badge";

export function ThemePlayer({ themes }: { themes: AnimeTheme[] }) {
  const [active, setActive] = useState<AnimeTheme | null>(themes[0] ?? null);

  if (themes.length === 0) {
    return <p className="text-muted-foreground text-sm">暂无 OP/ED 数据</p>;
  }

  return (
    <div className="space-y-4">
      {active?.video_url && (
        <video
          key={active.video_url}
          src={active.video_url}
          controls
          className="w-full rounded-lg max-h-64 bg-black"
          autoPlay
        />
      )}
      <div className="flex flex-wrap gap-2">
        {themes.map((theme) => (
          <button
            key={theme.id}
            onClick={() => setActive(theme)}
            className={`text-sm px-3 py-1.5 rounded-full border transition-colors ${
              active?.id === theme.id
                ? "bg-primary text-primary-foreground border-primary"
                : "hover:border-primary"
            }`}
          >
            <Badge variant={theme.type === "OP" ? "default" : "secondary"} className="mr-1.5 text-xs">
              {theme.type}{theme.sequence ?? ""}
            </Badge>
            {theme.song_title}
            {theme.artist && <span className="text-xs ml-1 opacity-70">/ {theme.artist}</span>}
          </button>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 写 `frontend/components/TorrentList.tsx`**

```typescript
"use client";
import { useState } from "react";
import type { TorrentsResponse } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const SOURCE_LABELS: Record<string, string> = {
  nyaa: "Nyaa",
  acgrip: "ACG.RIP",
  dmhy: "动漫花园",
  mikan: "蜜柑计划",
};

const SOURCE_COLORS: Record<string, string> = {
  nyaa: "bg-blue-100 text-blue-800",
  acgrip: "bg-green-100 text-green-800",
  dmhy: "bg-orange-100 text-orange-800",
  mikan: "bg-purple-100 text-purple-800",
};

export function TorrentList({ data }: { data: TorrentsResponse }) {
  const [copied, setCopied] = useState<string | null>(null);

  function copyMagnet(magnet: string, btih: string) {
    navigator.clipboard.writeText(magnet);
    setCopied(btih);
    setTimeout(() => setCopied(null), 2000);
  }

  if (data.torrents.length === 0 && data.errors.length > 0) {
    return (
      <div className="text-sm text-muted-foreground space-y-1">
        <p>暂无种子数据</p>
        {data.errors.map((e) => (
          <p key={e.source} className="text-xs text-destructive">{SOURCE_LABELS[e.source] ?? e.source}: {e.error}</p>
        ))}
      </div>
    );
  }

  if (data.torrents.length === 0) {
    return <p className="text-muted-foreground text-sm">暂无种子</p>;
  }

  return (
    <div className="space-y-2">
      {data.errors.length > 0 && (
        <p className="text-xs text-muted-foreground">
          部分来源不可用：{data.errors.map((e) => SOURCE_LABELS[e.source] ?? e.source).join("、")}
        </p>
      )}
      <div className="divide-y rounded-lg border overflow-hidden">
        {data.torrents.map((t) => (
          <div key={t.btih} className="flex items-start gap-3 p-3 hover:bg-muted/50 transition-colors">
            <Badge className={`text-xs shrink-0 mt-0.5 ${SOURCE_COLORS[t.source] ?? ""}`}>
              {SOURCE_LABELS[t.source] ?? t.source}
            </Badge>
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate" title={t.title}>{t.title}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {t.size && <span className="mr-3">{t.size}</span>}
                {t.date && <span>{t.date.slice(0, 10)}</span>}
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="shrink-0 text-xs"
              onClick={() => copyMagnet(t.magnet, t.btih)}
            >
              {copied === t.btih ? "已复制" : "复制磁力"}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 写 `frontend/app/anime/[id]/page.tsx`**

```typescript
import Image from "next/image";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { api } from "@/lib/api";
import { ThemePlayer } from "@/components/ThemePlayer";
import { TorrentList } from "@/components/TorrentList";
import { Badge } from "@/components/ui/badge";
import { SearchBar } from "@/components/SearchBar";

async function ThemesSection({ id }: { id: number }) {
  const themes = await api.getAnimeThemes(id).catch(() => []);
  return <ThemePlayer themes={themes} />;
}

async function MusicSection({ id }: { id: number }) {
  const music = await api.getAnimeMusic(id).catch(() => []);
  if (music.length === 0) return null;
  return (
    <section>
      <h2 className="text-xl font-semibold mb-3">原声带 (OST)</h2>
      <div className="flex flex-wrap gap-2">
        {music.map((m) => (
          <Badge key={m.id} variant="outline">{m.name_cn || m.name}</Badge>
        ))}
      </div>
    </section>
  );
}

async function TorrentsSection({ id }: { id: number }) {
  const data = await api.getTorrents(id).catch(() => ({ torrents: [], errors: [{ source: "all", error: "请求失败" }] }));
  return <TorrentList data={data} />;
}

export default async function AnimePage({ params }: { params: Promise<{ id: string }> }) {
  const { id: idStr } = await params;
  const id = parseInt(idStr, 10);
  if (isNaN(id)) notFound();

  const anime = await api.getAnimeDetail(id).catch(() => null);
  if (!anime) notFound();

  const title = anime.name_cn || anime.name;

  return (
    <main className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="mb-6">
        <SearchBar />
      </div>

      {/* 顶部信息区 */}
      <div className="flex gap-6 mb-8">
        <div className="relative w-40 h-56 shrink-0 rounded-lg overflow-hidden border bg-muted">
          {anime.image && (
            <Image src={anime.image} alt={title} fill className="object-cover" sizes="160px" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold">{title}</h1>
          {anime.name !== title && <p className="text-muted-foreground mt-1">{anime.name}</p>}
          <div className="flex flex-wrap gap-2 mt-3">
            {anime.air_date && <Badge variant="outline">{anime.air_date.slice(0, 4)}</Badge>}
            {anime.eps && <Badge variant="outline">{anime.eps} 话</Badge>}
            {anime.rating?.score && <Badge>{anime.rating.score} 分</Badge>}
            {anime.tags.slice(0, 6).map((t) => (
              <Badge key={t.name} variant="secondary">{t.name}</Badge>
            ))}
          </div>
          <p className="text-sm text-muted-foreground mt-4 line-clamp-4">{anime.summary || "暂无简介"}</p>
        </div>
      </div>

      {/* OP/ED 播放器 */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">主题曲 (OP/ED)</h2>
        <Suspense fallback={<p className="text-sm text-muted-foreground">加载中...</p>}>
          <ThemesSection id={id} />
        </Suspense>
      </section>

      {/* OST */}
      <div className="mb-8">
        <Suspense fallback={null}>
          <MusicSection id={id} />
        </Suspense>
      </div>

      {/* 种子列表 */}
      <section>
        <h2 className="text-xl font-semibold mb-3">磁力下载</h2>
        <Suspense fallback={<p className="text-sm text-muted-foreground">聚合中，请稍候...</p>}>
          <TorrentsSection id={id} />
        </Suspense>
      </section>
    </main>
  );
}
```

- [ ] **Step 4: 安装 shadcn 所需组件**

```bash
cd frontend
npx shadcn@latest add badge button input
```

- [ ] **Step 5: 验证 TypeScript 编译**

```bash
npx tsc --noEmit
```

Expected: 无错误

- [ ] **Step 6: 端到端测试**

```bash
# 确保后端运行中
cd backend && uvicorn app.main:app --reload &
# 启动前端
cd frontend && npm run dev
```

访问 http://localhost:3000 → 搜索"进击的巨人" → 点击结果 → 详情页应显示封面、简介、OP/ED 播放器、种子列表。

- [ ] **Step 7: Commit**

```bash
git add frontend/components/ThemePlayer.tsx frontend/components/TorrentList.tsx frontend/app/anime/
git commit -m "feat: anime detail page with OP/ED player and torrent list"
```

---

## Task 9: README + 部署说明

**Files:**
- Create: `README.md`

- [ ] **Step 1: 写 `README.md`**

```markdown
# 动画 BT 聚合站

面向中文用户的动画 BT 下载聚合工具。聚合 Nyaa、ACG.RIP、动漫花园、蜜柑计划，提供中文动画信息（Bangumi）和 OP/ED 视频（AnimeThemes）。

## 功能

- 搜索动画（中文/日文）
- 动画详情：封面、中文简介、评分、标签
- OP/ED 主题曲视频嵌入播放
- 多源磁力链聚合（nyaa/acg.rip/dmhy/mikan）
- 种子去重（btih infohash）

## 本地运行

**前置条件：** Docker + Docker Compose

```bash
git clone https://github.com/yourname/anime-bt-aggregator
cd anime-bt-aggregator
docker-compose up
```

访问 http://localhost:3000

## 开发模式

```bash
# 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端（新终端）
cd frontend
npm install
npm run dev
```

## 技术栈

- **后端**: Python 3.12, FastAPI, httpx, feedparser
- **前端**: Next.js 15, TypeScript, TailwindCSS, shadcn/ui
- **数据来源**: Bangumi API, AnimeThemes API, nyaa.si/acg.rip/dmhy/mikan RSS

## 注意事项

- 蜜柑计划（mikanani.me）有 Cloudflare 防护，非日本 IP 可能无法访问，失败时忽略
- 生产环境后端部署到 Render.com 免费层（首次请求有 30-60 秒冷启动延迟）
- 本工具仅作学习用途

## License

MIT
```

- [ ] **Step 2: 最终全量测试**

```bash
cd backend && pytest tests/ -v
```

Expected: 全部 PASSED，显示通过数量。

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup instructions"
```

---

## Self-Review

**Spec Coverage:**
- [x] 搜索动画（中文/日文）→ Task 3 + Task 7
- [x] 动画详情页（封面/简介/OP/ED/种子）→ Task 8
- [x] 中文信息（Bangumi）→ Task 3
- [x] AnimeThemes OP/ED 视频 → Task 4 + Task 8
- [x] 四个种子源聚合 → Task 5
- [x] 种子去重（btih）→ Task 2 + Task 5
- [x] 降级状态处理 → Task 5 (SourceError), Task 8 (catch+fallback)
- [x] 缓存 TTL → Task 2
- [x] docker-compose 部署 → Task 1
- [x] OST（best-effort）→ Task 3 + Task 8
- [x] mikanani best-effort → Task 5

**Placeholder Scan:** 无 TBD/TODO/placeholder

**Type Consistency:**
- `AnimeSearchResult` 在 models.py 和 types/index.ts 字段一致
- `Torrent.btih` 在 scrapers 和 models 里均为 lowercase hex
- `TorrentsResponse.deduplicated` 方法签名在 Task 2 定义，Task 5 调用一致
- `AnimeTheme.song_title`（非 `song.title`）在 models.py、router、types 三处一致
