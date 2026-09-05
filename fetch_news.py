"""
Pulls candidate headlines from Google News RSS for each configured search
query. Google News RSS needs no API key and covers essentially every major
outlet, which keeps this resilient (individual publishers change/kill their
RSS feeds fairly often; Google News aggregates around that).
"""
import time
import urllib.parse
from datetime import datetime, timezone

import feedparser
from dateutil import parser as dateparser


def _to_utc(struct_time_or_str):
    try:
        if struct_time_or_str is None:
            return None
        dt = dateparser.parse(struct_time_or_str) if isinstance(struct_time_or_str, str) else None
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def fetch_candidates(config: dict) -> list[dict]:
    """Returns a deduplicated list of candidate articles across all queries."""
    lookback_hours = config.get("lookback_hours", 30)
    per_query = config.get("candidates_per_query", 8)
    cutoff = datetime.now(timezone.utc).timestamp() - lookback_hours * 3600

    seen_links = set()
    seen_titles = set()
    candidates = []

    for q in config["search_queries"]:
        encoded = urllib.parse.quote(q["query"])
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(url)

        count = 0
        for entry in feed.entries:
            if count >= per_query:
                break

            published = _to_utc(entry.get("published"))
            if published is not None and published.timestamp() < cutoff:
                continue

            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue

            # crude de-dupe: same link, or near-identical title
            title_key = title.lower()[:80]
            if link in seen_links or title_key in seen_titles:
                continue
            seen_links.add(link)
            seen_titles.add(title_key)

            source = ""
            if "source" in entry and hasattr(entry.source, "title"):
                source = entry.source.title
            elif " - " in title:
                source = title.rsplit(" - ", 1)[-1]

            candidates.append({
                "topic_bucket": q["name"],
                "title": title,
                "link": link,
                "source": source,
                "published": published.isoformat() if published else None,
            })
            count += 1

        time.sleep(0.5)  # be polite to Google News

    return candidates


if __name__ == "__main__":
    import yaml
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)
    items = fetch_candidates(cfg)
    print(f"Fetched {len(items)} candidates")
    for it in items[:10]:
        print("-", it["title"], "|", it["source"])
