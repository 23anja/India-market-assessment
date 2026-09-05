"""
Pulls open GitHub Issues labeled "feedback" from this repo and turns them
into short text notes that get fed into the Gemini prompt, so the digest
tunes itself to what the reader actually asks for over time.

Uses the GITHUB_TOKEN that GitHub Actions provides automatically — no
extra secret needed. Falls back to an empty list if anything is missing
(e.g. running locally without a token).
"""
import os

import requests


def get_feedback_notes() -> list[str]:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")  # e.g. "username/india-market-digest"
    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    params = {"state": "open", "labels": "feedback", "per_page": 30}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        issues = resp.json()
    except Exception:
        return []

    notes = []
    for issue in issues:
        if "pull_request" in issue:
            continue  # skip PRs, issues endpoint includes them
        title = (issue.get("title") or "").strip()
        body = (issue.get("body") or "").strip().replace("\n", " ")
        note = title if not body else f"{title} — {body[:300]}"
        if note:
            notes.append(note)
    return notes


if __name__ == "__main__":
    for n in get_feedback_notes():
        print("-", n)
