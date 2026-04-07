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
          autoPlay
          className="w-full rounded-lg max-h-64 bg-black"
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
            <Badge
              variant={theme.type === "OP" ? "default" : "secondary"}
              className="mr-1.5 text-xs"
            >
              {theme.type}
              {theme.sequence ?? ""}
            </Badge>
            {theme.song_title}
            {theme.artist && (
              <span className="text-xs ml-1 opacity-70">/ {theme.artist}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
