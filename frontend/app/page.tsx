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
      {animes.map((a) => (
        <AnimeCard key={a.id} anime={a} />
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
    <main className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="flex flex-col items-center gap-6 mb-10">
        <h1 className="text-3xl font-bold tracking-tight">动画 BT 聚合</h1>
        <SearchBar defaultValue={q ?? ""} />
      </div>

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
    </main>
  );
}
