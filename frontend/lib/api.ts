import type {
  AnimeSearchResult,
  AnimeDetail,
  MusicEntry,
  AnimeTheme,
  TorrentsResponse,
} from "@/types";

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
