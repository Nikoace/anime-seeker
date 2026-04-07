export interface AnimeSearchResult {
  id: number;
  name: string;
  name_cn: string;
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
