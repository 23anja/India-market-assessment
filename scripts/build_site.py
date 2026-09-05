"""
Renders the daily digest into static HTML: one archive page per day, plus
an index.html that shows the latest digest and links to the archive.
Pure string templating — no build step, no JS framework, works on GitHub
Pages with zero configuration.
"""
import json
import os
from datetime import datetime, timezone

SITE_DIR = os.path.join(os.path.dirname(__file__), "..", "site")
ARCHIVE_DIR = os.path.join(SITE_DIR, "archive")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

STYLE = """
:root { --fg:#1a1a1a; --muted:#6b6b6b; --accent:#b5121b; --bg:#fdfcf9; --card:#ffffff; --border:#e8e5df; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font-family: Georgia, 'Times New Roman', serif; line-height:1.55; }
.wrap { max-width: 760px; margin: 0 auto; padding: 32px 20px 80px; }
header.site { border-bottom: 3px solid var(--fg); padding-bottom: 14px; margin-bottom: 28px; }
header.site h1 { font-size: 1.6rem; margin: 0 0 4px; letter-spacing: -0.01em; }
header.site .tagline { color: var(--muted); font-size: 0.95rem; font-family: Arial, sans-serif; }
.date-badge { font-family: Arial, sans-serif; font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 22px; }
.story { background: var(--card); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: 4px; padding: 20px 22px; margin-bottom: 22px; }
.story h2 { font-size: 1.25rem; margin: 0 0 6px; }
.story .meta { font-family: Arial, sans-serif; font-size: 0.78rem; color: var(--muted); margin-bottom: 12px; }
.story .meta a { color: var(--muted); }
.story h3.section-label { font-family: Arial, sans-serif; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); margin: 14px 0 4px; }
.story p { margin: 0 0 4px; }
nav.archive-links { font-family: Arial, sans-serif; font-size: 0.85rem; margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border); }
nav.archive-links a { color: var(--fg); text-decoration: none; margin-right: 14px; }
nav.archive-links a:hover { text-decoration: underline; }
footer.site { font-family: Arial, sans-serif; font-size: 0.8rem; color: var(--muted); margin-top: 40px; text-align: center; }
footer.site a { color: var(--accent); }
.feedback-btn { display:inline-block; font-family: Arial, sans-serif; font-size:0.85rem; padding:8px 16px; background:var(--fg); color:#fff; border-radius: 4px; text-decoration:none; }
"""


def _story_html(story: dict) -> str:
    return f"""
    <article class="story">
      <h2>{story['headline']}</h2>
      <div class="meta">{story.get('topic_bucket','')} &middot; {story.get('source','')} &middot;
        <a href="{story['link']}" target="_blank" rel="noopener">read original ↗</a></div>
      <h3 class="section-label">What happened</h3>
      <p>{story['summary']}</p>
      <h3 class="section-label">India / market angle</h3>
      <p>{story['india_impact']}</p>
      <h3 class="section-label">What to watch</h3>
      <p>{story['what_to_watch']}</p>
    </article>
    """


def _page_html(title: str, date_label: str, stories: list[dict], repo_url: str, is_index: bool) -> str:
    stories_html = "\n".join(_story_html(s) for s in stories)
    archive_link = "" if is_index else '<a href="../index.html">&larr; Back to latest</a>'
    feedback_url = f"{repo_url}/issues/new?labels=feedback&title=Feedback%3A%20" if repo_url else "#"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">
  <header class="site">
    <h1>India Market &amp; Geopolitics Digest</h1>
    <div class="tagline">3 stories a day, curated and connected to India — no doomscrolling required.</div>
  </header>
  <div class="date-badge">{date_label}</div>
  {stories_html}
  <p style="margin-top:30px;"><a class="feedback-btn" href="{feedback_url}" target="_blank" rel="noopener">Give feedback →</a></p>
  <nav class="archive-links">
    {archive_link}
    <a href="archive/index.html">Full archive</a>
  </nav>
  <footer class="site">Auto-generated daily via GitHub Actions + Gemini. Not investment advice.</footer>
</div>
</body>
</html>"""


def _archive_index_html(entries: list[dict]) -> str:
    items = "\n".join(
        f'<li><a href="{e["file"]}">{e["date_label"]}</a> — {e["headline_preview"]}</li>'
        for e in sorted(entries, key=lambda e: e["date"], reverse=True)
    )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Archive — India Market &amp; Geopolitics Digest</title>
<style>{STYLE}</style></head>
<body><div class="wrap">
<header class="site"><h1>Archive</h1></header>
<ul style="font-family:Arial,sans-serif; line-height:2;">{items}</ul>
<nav class="archive-links"><a href="../index.html">&larr; Back to latest</a></nav>
</div></body></html>"""


def build(stories: list[dict], repo_url: str = ""):
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    now = datetime.now(timezone.utc)
    date_key = now.strftime("%Y-%m-%d")
    date_label = now.strftime("%A, %d %B %Y")

    # Write today's archive page
    archive_filename = f"{date_key}.html"
    archive_path = os.path.join(ARCHIVE_DIR, archive_filename)
    with open(archive_path, "w") as f:
        f.write(_page_html(f"{date_label} — Digest", date_label, stories, repo_url, is_index=False))

    # Write index.html (latest)
    index_path = os.path.join(SITE_DIR, "index.html")
    with open(index_path, "w") as f:
        f.write(_page_html("India Market & Geopolitics Digest", date_label, stories, repo_url, is_index=True))

    # Update history.json (used to build archive index + feed selection memory)
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    history = [h for h in history if h["date"] != date_key]  # replace if re-run same day
    history.append({
        "date": date_key,
        "date_label": date_label,
        "file": archive_filename,
        "headline_preview": stories[0]["headline"] if stories else "",
        "stories": stories,
    })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    # Rebuild archive index
    with open(os.path.join(ARCHIVE_DIR, "index.html"), "w") as f:
        f.write(_archive_index_html(history))

    return index_path, archive_path
