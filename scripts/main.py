import os
import sys

import yaml

from fetch_news import fetch_candidates
from analyze import select_and_analyze
from feedback import get_feedback_notes
from build_site import build

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main():
    with open(os.path.join(ROOT, "config.yaml")) as f:
        config = yaml.safe_load(f)

    print("Fetching candidate headlines...")
    candidates = fetch_candidates(config)
    print(f"  {len(candidates)} candidates found")
    if not candidates:
        print("No candidates found — aborting without changing the site.")
        sys.exit(1)

    print("Pulling reader feedback from GitHub Issues...")
    notes = get_feedback_notes()
    print(f"  {len(notes)} feedback notes found")

    print("Selecting + analyzing stories with Gemini...")
    stories = select_and_analyze(candidates, config, notes)
    if not stories:
        print("Gemini returned no stories — aborting without changing the site.")
        sys.exit(1)
    print(f"  {len(stories)} stories selected")

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    repo_url = f"https://github.com/{repo}" if repo else ""

    index_path, archive_path = build(stories, repo_url=repo_url)
    print(f"Wrote {index_path} and {archive_path}")


if __name__ == "__main__":
    main()
