"use client";
import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function SearchBar({ defaultValue = "" }: { defaultValue?: string }) {
  const [q, setQ] = useState(defaultValue);
  const router = useRouter();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (q.trim()) router.push(`/?q=${encodeURIComponent(q.trim())}`);
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 w-full max-w-2xl">
      <Input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="搜索动画名称（中文或日文）..."
        className="flex-1 h-11 text-base"
      />
      <Button type="submit" className="h-11 px-6 text-base">搜索</Button>
    </form>
  );
}
