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
  nyaa: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  acgrip: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  dmhy: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  mikan: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
};

export function TorrentList({ data }: { data: TorrentsResponse }) {
  const [copied, setCopied] = useState<string | null>(null);

  function copyMagnet(magnet: string, btih: string) {
    navigator.clipboard.writeText(magnet);
    setCopied(btih);
    setTimeout(() => setCopied(null), 2000);
  }

  const realErrors = data.errors.filter((e) => e.error);

  if (data.torrents.length === 0) {
    return (
      <div className="text-sm text-muted-foreground space-y-1">
        <p>暂无种子数据</p>
        {realErrors.map((e) => (
          <p key={e.source} className="text-xs text-destructive">
            {SOURCE_LABELS[e.source] ?? e.source}: {e.error}
          </p>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {data.errors.length > 0 && (
        <p className="text-xs text-muted-foreground">
          部分来源不可用：
          {data.errors.map((e) => SOURCE_LABELS[e.source] ?? e.source).join("、")}
        </p>
      )}
      <div className="divide-y rounded-lg border overflow-hidden">
        {data.torrents.map((t) => (
          <div
            key={t.btih}
            className="flex items-start gap-3 p-3 hover:bg-muted/50 transition-colors"
          >
            <span
              className={`text-xs px-2 py-0.5 rounded-full shrink-0 mt-0.5 font-medium ${
                SOURCE_COLORS[t.source] ?? ""
              }`}
            >
              {SOURCE_LABELS[t.source] ?? t.source}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate" title={t.title}>
                {t.title}
              </p>
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
              {copied === t.btih ? "已复制 ✓" : "复制磁力"}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
