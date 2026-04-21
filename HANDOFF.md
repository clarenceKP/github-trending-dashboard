# GitHub Trending Dashboard Handoff

## Current State

Production URL:

```text
https://clarenceKP.github.io/github-trending-dashboard/
```

Repository:

```text
https://github.com/clarenceKP/github-trending-dashboard
```

This project is a static GitHub Trending dashboard built on top of the original `bonfy/github-trending` markdown archive. It does not require a backend. The dashboard is generated into `docs/index.html`, and GitHub Pages publishes the `docs` folder from the `main` branch.

## Key Files

```text
scraper.py
```

Fetches GitHub Trending pages and writes daily markdown files. The current version captures:

- repository title
- repository URL
- description
- language section
- total stars
- forks
- stars gained today

The star metadata is stored inside markdown comments, for example:

```markdown
* [owner / repo](https://github.com/owner/repo):Description <!-- stars:1234 forks:56 stars_today:78 -->
```

```text
build_dashboard.py
```

The main dashboard generator. It reads markdown files, parses records, applies scoring and tags, embeds data into a single static HTML page, and writes:

```text
dashboard.html
docs/index.html
```

Developers should edit `build_dashboard.py`, not the generated HTML files directly.

```text
docs/index.html
```

Generated GitHub Pages entrypoint. Do not hand-edit unless debugging a generated output issue.

```text
dashboard.html
```

Generated local standalone dashboard for direct browser preview.

```text
repo_metrics_overrides.json
```

Optional metric backfill for important repositories whose historical markdown records predate star collection. Current example:

```json
{
  "NousResearch/hermes-agent": {
    "stars": 103432,
    "forks": 14759,
    "source": "github_api",
    "updatedAt": "2026-04-20T07:57:24Z"
  }
}
```

## Data Flow

```text
GitHub Trending pages
  -> scraper.py
  -> YYYY-MM-DD.md markdown snapshots
  -> build_dashboard.py
  -> docs/index.html
  -> GitHub Pages
```

The dashboard currently embeds the latest 370 days by default to keep the static HTML shareable. Use `--all` for full history.

## Local Commands

Install dependencies once:

```powershell
cd D:\Trae\github-trending
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Update today's data and regenerate the dashboard:

```powershell
cd D:\Trae\github-trending
.\.venv\Scripts\python.exe scraper.py
.\.venv\Scripts\python.exe build_dashboard.py --output docs\index.html
.\.venv\Scripts\python.exe build_dashboard.py
```

Generate full-history HTML:

```powershell
.\.venv\Scripts\python.exe build_dashboard.py --all --output docs\index.html
```

Publish updates:

```powershell
git add .
git commit -m "Update trending dashboard"
git push
```

## Ranking Modes

The dashboard has two primary ranking modes.

### Hot Ranking

UI label:

```text
🔥 热门榜
```

Score label:

```text
热度分
```

Purpose: surface projects with strong long-term community validation and current heat.

Current formula in `hotScoreRow(row)`:

```text
log10(latestStars + 1) * 44
+ log10(starsToday + 1) * 20
+ log10(growth + 1) * 12
+ max(0, 22 - avgRank)
+ min(count, 10) * 3
```

### Rising Ranking

UI label:

```text
🚀 飙升榜
```

Score label:

```text
飙升分
```

Purpose: surface projects gaining attention quickly during the selected observation window.

Current formula in `risingScoreRow(row)`:

```text
log10(growth + 1) * 54
+ log10(starsToday + 1) * 30
+ min(42, log10((growth / latestStars) * 1000 + 1) * 18)
+ log10(latestStars + 1) * 8
+ max(0, 18 - avgRank)
+ min(count, 7) * 2
```

## Labels

Current project labels:

```text
🔥 高星热门
```

Shown when `latestStars >= 50000`.

```text
🚀 飙升项目
```

Shown when `growth >= 500`.

```text
AI
```

Keyword-based AI domain tag.

```text
金融
```

Keyword-based finance domain tag.

```text
当前指标
```

Shown when metrics come from `repo_metrics_overrides.json` rather than a historical daily snapshot.

## Domain Tabs

The dashboard includes domain tabs:

- `整体视图`
- `AI 项目`
- `金融项目`

Rules live in `DOMAIN_RULES` inside `build_dashboard.py`. They are currently keyword-based and intentionally simple.

## Search

Search is implemented in JavaScript in `build_dashboard.py`:

- `normalizeSearch`
- `subsequenceScore`
- `fuzzyScore`
- `rowSearchText`
- `searchRows`

It supports:

- exact substring matching
- compact substring matching
- loose subsequence matching
- repository names
- organizations/users
- descriptions
- languages
- domain labels

## Non-AI Repo Insight

The dashboard now includes a static "项目速读" drawer inspired by repo deep-dive products, but without calling AI, a backend, or live GitHub APIs.

Entry points:

- left-side repository cards: `速读`
- right-side aggregate leaderboard rows: `项目速读`
- share URLs: the dashboard hash can include `repo=owner/name`

The drawer is generated client-side from already embedded dashboard rows. It includes:

- positioning summary
- reasons to inspect
- suitable audience
- first-read path after opening GitHub
- architecture and technical clues
- risk and verification checklist
- source chips showing the ranking data used

Important implementation functions in `build_dashboard.py`:

- `renderSelectedInsight`
- `renderInsight`
- `buildInsight`
- `inferProjectKind`
- `insightHighlights`
- `insightAudiences`
- `insightReadPath`
- `insightArchitecture`
- `insightRisks`
- `insightSources`

This is intentionally heuristic. It should phrase architecture content as clues, not conclusions, because this version does not read README files or source trees.

## Known Limitations

1. Historical markdown before the star-metadata upgrade lacks total stars, forks, and stars gained today.
2. `repo_metrics_overrides.json` can backfill current total stars/forks, but it cannot reconstruct daily historical star growth.
3. AI and finance tags are keyword-based. They can produce false positives or miss projects with vague descriptions.
4. The dashboard is generated as one large static HTML file. This is simple and portable, but not ideal for very large full-history datasets.
5. GitHub Trending itself is language-section based. Cross-language ranking is a dashboard-level heuristic, not an official GitHub signal.
6. The non-AI repo insight drawer uses ranking metadata and keyword rules only. It does not inspect repository README, docs, dependencies, diagrams, or code.

## Suggested Next Improvements

1. Add an automated GitHub Action to run `scraper.py` and `build_dashboard.py` daily.
2. Store parsed records as JSON in addition to markdown, so the dashboard can evolve without reparsing markdown.
3. Add GitHub API enrichment for selected important projects, with rate-limit handling and caching.
4. Replace keyword-only domain tagging with a curated taxonomy or lightweight classifier.
5. Add a proper changelog/insights panel showing new entrants, dropouts, and biggest movers.
6. Split generated data into a separate JSON asset if `docs/index.html` becomes too large.
7. Add Playwright screenshot regression checks for dashboard layout.
8. Add a second-stage repository detail pipeline that caches README/docs/package metadata for top N projects, then upgrades the insight drawer from heuristic clues to source-backed summaries.

## Release Snapshot

The current stable handoff version should be tagged as:

```text
v0.1-dashboard-stable
```

This version includes:

- GitHub Pages publishing from `docs/index.html`
- static dashboard generation
- hot/rising ranking modes
- AI/finance tabs
- fuzzy search
- non-AI `项目速读` drawer with shareable repo hash links
- star/fork/stars-today metadata parsing
- current metric overrides for important repositories
- GitHub Markdown link fix
- right-side aggregate leaderboard column-width cleanup
