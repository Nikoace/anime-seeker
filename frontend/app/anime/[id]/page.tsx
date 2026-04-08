import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { api } from "@/lib/api";
import { ThemePlayer } from "@/components/ThemePlayer";
import { TorrentList } from "@/components/TorrentList";
import { Badge } from "@/components/ui/badge";

async function ThemesSection({ id }: { id: number }) {
  const themes = await api.getAnimeThemes(id).catch(() => []);
  return <ThemePlayer themes={themes} />;
}

async function MusicSection({ id }: { id: number }) {
  const music = await api.getAnimeMusic(id).catch(() => []);
  if (music.length === 0) return null;
  const shown = music.slice(0, 8);
  const rest = music.length - shown.length;
  return (
    <section className="mb-8">
      <h2 className="text-xl font-semibold mb-3">原声带 (OST)</h2>
      <div className="flex flex-wrap gap-2">
        {shown.map((m) => (
          <Badge key={m.id} variant="outline" className="text-xs">
            {m.name_cn || m.name}
          </Badge>
        ))}
        {rest > 0 && (
          <Badge variant="secondary" className="text-xs text-muted-foreground">
            +{rest} 更多
          </Badge>
        )}
      </div>
    </section>
  );
}

async function TorrentsSection({ id }: { id: number }) {
  const data = await api
    .getTorrents(id)
    .catch(() => ({ torrents: [], errors: [{ source: "all", error: "请求失败" }] }));
  return <TorrentList data={data} />;
}

export default async function AnimePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: idStr } = await params;
  const id = parseInt(idStr, 10);
  if (isNaN(id)) notFound();

  const anime = await api.getAnimeDetail(id).catch(() => null);
  if (!anime) notFound();

  const title = anime.name_cn || anime.name;
  const image = anime.image?.replace("http://", "https://") ?? null;

  return (
    <main className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="mb-6 flex items-center gap-3">
        <Link
          href="/"
          className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
        >
          ← 返回搜索
        </Link>
      </div>

      {/* 顶部信息 */}
      <div className="flex gap-6 mb-8">
        <div className="relative w-40 h-56 shrink-0 rounded-lg overflow-hidden border bg-muted">
          {image && (
            <Image
              src={image}
              alt={title}
              fill
              className="object-cover"
              sizes="160px"
            />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold">{title}</h1>
          {anime.name !== title && (
            <p className="text-muted-foreground mt-1 text-sm">{anime.name}</p>
          )}
          <div className="flex flex-wrap gap-2 mt-3">
            {anime.air_date && (
              <Badge variant="outline">{anime.air_date.slice(0, 4)}</Badge>
            )}
            {anime.eps && <Badge variant="outline">{anime.eps} 话</Badge>}
            {anime.rating?.score && <Badge>{anime.rating.score} 分</Badge>}
            {anime.tags.slice(0, 6).map((t) => (
              <Badge key={t.name} variant="secondary">
                {t.name}
              </Badge>
            ))}
          </div>
          <p className="text-sm text-muted-foreground mt-4 line-clamp-4 leading-relaxed">
            {anime.summary || "暂无简介"}
          </p>
        </div>
      </div>

      {/* OP/ED */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-3">主题曲 (OP/ED)</h2>
        <Suspense
          fallback={<p className="text-sm text-muted-foreground">加载中...</p>}
        >
          <ThemesSection id={id} />
        </Suspense>
      </section>

      {/* OST (best-effort) */}
      <Suspense fallback={null}>
        <MusicSection id={id} />
      </Suspense>

      {/* 种子列表 */}
      <section>
        <h2 className="text-xl font-semibold mb-3">磁力下载</h2>
        <Suspense
          fallback={
            <p className="text-sm text-muted-foreground">聚合中，请稍候...</p>
          }
        >
          <TorrentsSection id={id} />
        </Suspense>
      </section>
    </main>
  );
}
