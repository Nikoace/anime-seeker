from cachetools import TTLCache

bangumi_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)
themes_cache: TTLCache = TTLCache(maxsize=200, ttl=21600)
torrents_cache: TTLCache = TTLCache(maxsize=200, ttl=300)
