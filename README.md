# 动画 BT 聚合站

面向中文用户的动画 BT 下载聚合工具。聚合 Nyaa、ACG.RIP、动漫花园、蜜柑计划四个种子源，提供中文动画信息和 OP/ED 视频播放。

## 功能

- 搜索动画（中文/日文关键词）
- 动画详情：封面、中文简介、评分、标签
- OP/ED 主题曲视频嵌入播放（AnimeThemes）
- 多源磁力链聚合（nyaa / acg.rip / 动漫花园 / 蜜柑计划）
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
# 访问 http://localhost:8000/docs

# 前端（新终端）
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

如果你是在 Windows + WSL 开发，前端需要监听 `0.0.0.0` 才能稳定从 Windows 浏览器访问。
当前项目的 `npm run dev` 已经默认按这个方式启动；如果端口转发异常，也可以直接访问 WSL IP，例如 `http://172.x.x.x:3000`。

## 运行测试

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.12, FastAPI, httpx, feedparser, cachetools |
| 前端 | Next.js 15 (App Router), TypeScript, TailwindCSS, shadcn/ui |
| 动画信息 | [Bangumi API](https://api.bgm.tv)（中文） |
| OP/ED | [AnimeThemes API](https://api.animethemes.moe) |
| 种子源 | nyaa.si · acg.rip · dmhy.org · mikanani.me |

## 部署说明

- **后端**：推荐 [Render.com](https://render.com) 免费层，首次请求有 30-60 秒冷启动延迟（15 分钟无流量后休眠）
- **前端**：推荐 [Vercel](https://vercel.com) 免费层，设置环境变量 `NEXT_PUBLIC_API_URL` 为后端地址

## 缓存策略

| 数据类型 | 后端 TTL | 前端 revalidate | 说明 |
|---|---|---|---|
| 番剧基础信息 / 音乐 | 1 小时 | 1 小时 | Bangumi 数据几乎不变 |
| OP/ED 主题曲 | 6 小时 | 6 小时 | AnimeThemes 数据极稳定 |
| 种子聚合 | 1 小时 | 1 小时 | 每小时重新爬取四个源 |
| 搜索结果 | 不缓存 | 30 秒 | 允许新番及时出现 |

后端使用内存 TTLCache（cachetools），重启后缓存清空。

## 注意

- 蜜柑计划（mikanani.me）有 Cloudflare 防护，非日本 IP 可能被拦截，失败时静默忽略
- 各爬虫 timeout 为 5 秒，超时视为该源不可用，不影响其他源结果
- 本工具仅作学习用途

## License

MIT
