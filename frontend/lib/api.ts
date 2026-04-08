import type {
  AnimeSearchResult,
  AnimeDetail,
  MusicEntry,
  AnimeTheme,
  TorrentsResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(path: string, revalidate: number): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { next: { revalidate } });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  // 搜索结果变化较快，缓存 30 秒
  searchAnime: (q: string) =>
    fetchJSON<AnimeSearchResult[]>(`/api/anime/search?q=${encodeURIComponent(q)}`, 30),

  // 番剧基础信息和音乐变化极少，缓存 1 小时（与后端 bangumi_cache TTL 一致）
  getAnimeDetail: (id: number) =>
    fetchJSON<AnimeDetail>(`/api/anime/${id}`, 3600),

  getAnimeMusic: (id: number) =>
    fetchJSON<MusicEntry[]>(`/api/anime/${id}/music`, 3600),

  // 主题曲几乎不变，缓存 6 小时（与后端 themes_cache TTL 一致）
  getAnimeThemes: (id: number) =>
    fetchJSON<AnimeTheme[]>(`/api/themes/${id}`, 21600),

  // 种子数据缓存 1 小时（与后端 torrents_cache TTL 一致）
  getTorrents: (id: number) =>
    fetchJSON<TorrentsResponse>(`/api/torrents/${id}`, 3600),
};
