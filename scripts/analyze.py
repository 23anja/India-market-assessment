"""
Sends the candidate headline pool to Gemini (Google AI Studio free tier),
asking it to pick the N most important stories and write India-focused
analysis for each, incorporating any reader feedback collected via GitHub
Issues.
"""
import json
import os
import re

import requests

GEMINI_URL_TMPL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def _build_prompt(candidates, config, feedback_notes):
    stories_per_day = config.get("stories_per_day", 3)
    analysis_instructions = config["analysis_instructions"]

    candidate_lines = []
    for i, c in enumerate(candidates):
        candidate_lines.append(
            f"[{i}] ({c['topic_bucket']}) \"{c['title']}\" — {c['source']} — {c['link']}"
        )
    candidate_block = "\n".join(candidate_lines)

    feedback_block = "None yet." if not feedback_notes else "\n".join(f"- {n}" for n in feedback_notes)

    prompt = f"""You are curating a daily geopolitics/economics/markets digest for one
specific reader in India. From the candidate headlines below, select the
{stories_per_day} MOST IMPORTANT and MOST DISTINCT stories (avoid picking
near-duplicates of the same event). Prioritize genuine significance over
sensationalism.

READER FEEDBACK / PREFERENCES SO FAR (weight these when choosing and when
writing analysis; ignore if empty):
{feedback_block}

ANALYSIS INSTRUCTIONS:
{analysis_instructions}

CANDIDATE HEADLINES (format: [index] (bucket) "title" — source — link):
{candidate_block}

Respond with ONLY valid JSON, no markdown fences, matching exactly this shape:
{{
  "stories": [
    {{
      "candidate_index": <int, index from the list above>,
      "headline": "<clear, rewritten headline, not clickbait>",
      "summary": "<2-4 sentence neutral summary>",
      "india_impact": "<the mechanism connecting it to India per instructions>",
      "what_to_watch": "<short forward-looking pointer>"
    }}
  ]
}}
"""
    return prompt


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text)
    text = re.sub(r"```$", "", text)
    return json.loads(text.strip())


def select_and_analyze(candidates: list[dict], config: dict, feedback_notes: list[str]) -> list[dict]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    model = config.get("gemini_model", "gemini-3.1-flash-lite")
    prompt = _build_prompt(candidates, config, feedback_notes)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "response_mime_type": "application/json",
        },
    }

    url = GEMINI_URL_TMPL.format(model=model)
    resp = requests.post(url, params={"key": api_key}, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = _extract_json(text)

    results = []
    for story in parsed.get("stories", []):
        idx = story.get("candidate_index")
        if idx is None or idx < 0 or idx >= len(candidates):
            continue
        source_candidate = candidates[idx]
        results.append({
            **story,
            "source": source_candidate["source"],
            "link": source_candidate["link"],
            "topic_bucket": source_candidate["topic_bucket"],
        })
    return results


if __name__ == "__main__":
    # quick manual test scaffold (requires GEMINI_API_KEY + config.yaml + fetch_news)
    import yaml
    from fetch_news import fetch_candidates

    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)
    cands = fetch_candidates(cfg)
    out = select_and_analyze(cands, cfg, [])
    print(json.dumps(out, indent=2))
