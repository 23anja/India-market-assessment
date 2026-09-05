# India Market & Geopolitics Digest

A self-updating site that pulls today's geopolitics / economics / markets
news, picks the most important 2–3 stories, and writes a short analysis of
how each one connects to the Indian economy and markets — automatically,
every day, for free.

**How it works:** GitHub Actions runs on a schedule → pulls candidate
headlines from Google News RSS → sends them to Gemini (free tier) to pick
the best stories and write the analysis → renders a static HTML page →
publishes it to GitHub Pages. Total ongoing cost: **₹0.**

---

## One-time setup (10–15 minutes)

### 1. Create the repo
Push this folder to a new GitHub repository (public or private — Pages
works with either, private just needs GitHub Pro/Team/Enterprise for a
custom Pages site; a public repo works on the free plan).

```bash
cd india-market-digest
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/india-market-digest.git
git push -u origin main
```

### 2. Get a free Gemini API key
1. Go to **https://aistudio.google.com/apikey**
2. Sign in with a Google account, click **Create API key**.
3. Copy the key. Free tier gives generous daily quota — one run/day uses
   almost nothing of it.

### 3. Add the key as a GitHub secret
In your repo: **Settings → Secrets and variables → Actions → New repository
secret**
- Name: `GEMINI_API_KEY`
- Value: *(paste the key)*

(You do **not** need to add a `GITHUB_TOKEN` secret — GitHub provides one
automatically to every workflow run.)

### 4. Turn on GitHub Pages
**Settings → Pages → Build and deployment → Source: "Deploy from a
branch"** → select branch **`gh-pages`** (this branch gets created
automatically the first time the workflow runs) → folder **`/ (root)`**.
Your site will then be live at:
`https://<your-username>.github.io/india-market-digest/`

*(If `gh-pages` doesn't appear yet, run the workflow once manually first —
step 5 below — then come back and select it.)*

### 5. Run it for the first time
**Actions tab → "Daily Digest" → Run workflow** (the manual trigger button).
Wait ~30 seconds, check the run succeeded, then visit your Pages URL.

After this, it runs automatically every day at **7:00 AM IST** — no
further action needed from you.

---

## Customizing it

Everything you'll want to tweak lives in **`config.yaml`**, no code
required:
- `search_queries` — what topics/keywords the news pool is built from
- `stories_per_day` — how many stories to show (default 3)
- `analysis_instructions` — the "lens" the AI writes through; edit this
  directly to change tone, depth, or focus (e.g. add "focus more on IT
  services and pharma exports" if that's your sector)
- `gemini_model` — which Gemini model to use
- `lookback_hours` — how far back to search for "today's" news

Change the schedule time by editing the `cron` line in
`.github/workflows/daily-digest.yml` (times are in UTC; IST = UTC + 5:30).

---

## Giving feedback (this is what tunes it over time)

Click **"Give feedback →"** on the site — it opens a pre-filled GitHub
Issue in your repo, labeled `feedback`. Write anything: "too much US Fed
news, more on China+India trade", "analysis is too shallow, go deeper on
mechanism", "skip pure sports/entertainment-adjacent stories", etc.

Every day's run reads all **open** issues labeled `feedback` and feeds
them into the prompt that picks and analyzes stories. Close an issue once
you feel it's been addressed, or leave it open if it's an ongoing
preference.

---

## Repo structure

```
config.yaml                  ← your settings, edit freely
requirements.txt             ← Python deps
scripts/
  fetch_news.py              ← pulls candidate headlines (Google News RSS)
  analyze.py                 ← sends candidates to Gemini, gets picks + analysis
  feedback.py                ← reads GitHub Issues labeled "feedback"
  build_site.py              ← renders the static HTML
  main.py                    ← orchestrates the above, run daily by Actions
site/                        ← the published site (index.html + archive/)
data/history.json            ← full history of past digests, machine-readable
.github/workflows/
  daily-digest.yml           ← the schedule + automation
```

## Notes & limits
- Google News RSS occasionally surfaces a slightly stale or duplicate
  story — the Gemini step is asked to de-duplicate, but it's not perfect.
  Tell it via feedback if a topic bucket is consistently noisy and adjust
  `search_queries` in `config.yaml`.
- This is a news curation and analysis tool, not investment advice.
- If a run ever fails (e.g. Gemini free-tier rate limit on a busy day),
  the site simply doesn't update that day — check the **Actions** tab for
  the error log.
