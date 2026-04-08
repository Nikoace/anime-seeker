import { Suspense } from "react";
import { SearchBar } from "@/components/SearchBar";
import { AnimeCard } from "@/components/AnimeCard";
import { api } from "@/lib/api";

// 热门动画（Bangumi ID），v1 静态展示
const POPULAR_IDS = [8, 328, 21, 245, 975, 34];

async function PopularAnime() {
  const results = await Promise.allSettled(
    POPULAR_IDS.map((id) => api.getAnimeDetail(id))
  );
  const animes = results
    .filter(
      (r): r is PromiseFulfilledResult<Awaited<ReturnType<typeof api.getAnimeDetail>>> =>
        r.status === "fulfilled"
    )
    .map((r) => r.value);

  return (
    <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
      {animes.map((a, i) => (
        <AnimeCard key={a.id} anime={a} priority={i === 0} />
      ))}
    </div>
  );
}

async function SearchResults({ q }: { q: string }) {
  try {
    const results = await api.searchAnime(q);
    if (results.length === 0) {
      return (
        <p className="text-muted-foreground text-center py-12">
          没有找到「{q}」相关的动画
        </p>
      );
    }
    return (
      <div className="grid grid-cols-3 md:grid-cols-5 gap-4">
        {results.map((a) => (
          <AnimeCard key={a.id} anime={a} />
        ))}
      </div>
    );
  } catch {
    return (
      <p className="text-destructive text-center py-12">
        搜索失败，请确认后端服务正在运行
      </p>
    );
  }
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;

  return (
    <main className="max-w-5xl mx-auto">
      <div className={`flex flex-col items-center gap-4 px-4 bg-gradient-to-b from-zinc-950 to-zinc-900 rounded-b-2xl ${q ? "py-5 mb-6" : "py-14 mb-8"}`}>
        {!q && (
          <div className="flex flex-col items-center gap-1">
            <h1 className="text-4xl font-bold tracking-tight text-white">动画 BT 聚合</h1>
            <p className="text-zinc-400 text-sm">聚合 Nyaa · ACG.RIP · 动漫花园 · 蜜柑计划</p>
          </div>
        )}
        {q && (
          <h1 className="text-xl font-bold text-white tracking-tight">动画 BT 聚合</h1>
        )}
        <SearchBar defaultValue={q ?? ""} />
      </div>
      <div className="px-4">

      {q ? (
        <>
          <h2 className="text-lg font-semibold mb-4">搜索：{q}</h2>
          <Suspense
            fallback={<p className="text-center text-muted-foreground">搜索中...</p>}
          >
            <SearchResults q={q} />
          </Suspense>
        </>
      ) : (
        <>
          <h2 className="text-lg font-semibold mb-4">热门动画</h2>
          <Suspense
            fallback={<p className="text-center text-muted-foreground">加载中...</p>}
          >
            <PopularAnime />
          </Suspense>
        </>
      )}
      </div>
    </main>
  );
}
