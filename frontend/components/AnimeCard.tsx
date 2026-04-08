import Link from "next/link";
import Image from "next/image";
import type { AnimeSearchResult, AnimeDetail } from "@/types";

type Props = { anime: AnimeSearchResult | AnimeDetail; priority?: boolean };

export function AnimeCard({ anime, priority = false }: Props) {
  const title = anime.name_cn || anime.name;
  const image = anime.image?.replace("http://", "https://") ?? null;
  return (
    <Link
      href={`/anime/${anime.id}`}
      className="group block rounded-lg overflow-hidden border hover:border-primary transition-colors"
    >
      <div className="relative aspect-[3/4] bg-muted">
        {image ? (
          <Image
            src={image}
            alt={title}
            fill
            priority={priority}
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            sizes="(max-width: 768px) 50vw, 200px"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-muted-foreground text-sm">
            无封面
          </div>
        )}
      </div>
      <div className="p-2">
        <p className="font-medium text-sm line-clamp-2">{title}</p>
        {anime.air_date && (
          <p className="text-xs text-muted-foreground mt-1">
            {anime.air_date.slice(0, 4)}
          </p>
        )}
      </div>
    </Link>
  );
}
