# coding: utf-8

import datetime as dt
import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT_FILE = ROOT / "dashboard.html"
DATE_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
ITEM_RE = re.compile(r"^\* \[(?P<title>.+?)\]\((?P<url>https://github\.com/[^)]+)\):(?P<description>.*)$")
DEFAULT_DAYS = 370


def iter_markdown_files():
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts or path.name == "README.md":
            continue
        if DATE_FILE_RE.match(path.name):
            yield path


def parse_file(path):
    date = path.stem
    current_language = None
    rank = 0
    entries = []

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line.startswith("#### "):
            current_language = line.replace("#### ", "", 1).strip()
            rank = 0
            continue

        match = ITEM_RE.match(line)
        if not match or not current_language:
            continue

        rank += 1
        title = match.group("title").strip()
        url = match.group("url").strip()
        owner_repo = url.replace("https://github.com/", "").strip("/")
        entries.append(
            {
                "date": date,
                "language": current_language,
                "rank": rank,
                "title": title,
                "repo": owner_repo,
                "url": url,
                "description": match.group("description").strip(),
            }
        )

    return entries


def collect_data(days=DEFAULT_DAYS):
    entries = []
    for path in iter_markdown_files():
        entries.extend(parse_file(path))

    entries.sort(key=lambda item: (item["date"], item["language"], item["rank"]))
    all_dates = sorted({item["date"] for item in entries})
    dates = all_dates[-days:] if days else all_dates
    allowed_dates = set(dates)
    entries = [item for item in entries if item["date"] in allowed_dates]
    languages = sorted({item["language"] for item in entries})
    generated_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    return {
        "generatedAt": generated_at,
        "includedDays": len(dates),
        "totalDays": len(all_dates),
        "latestDate": dates[-1] if dates else "",
        "dates": dates,
        "languages": languages,
        "entries": entries,
    }


def render_html(payload):
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GitHub Trending Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #111827;
      --muted: #667085;
      --line: #d7dee8;
      --panel: #ffffff;
      --soft: #f4f7fb;
      --accent: #0f766e;
      --accent-2: #b42318;
      --accent-3: #7a5af8;
      --good: #067647;
      --shadow: 0 18px 45px rgba(16, 24, 40, 0.10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #eef3f8;
    }}
    button, input, select {{ font: inherit; }}
    a {{ color: inherit; }}
    .app-shell {{ min-height: 100vh; }}
    .hero {{
      padding: 30px 28px 22px;
      color: #fff;
      background:
        linear-gradient(120deg, rgba(8, 51, 68, .92), rgba(20, 83, 45, .76)),
        url("https://images.unsplash.com/photo-1556075798-4825dfaaf498?auto=format&fit=crop&w=1800&q=80");
      background-size: cover;
      background-position: center;
    }}
    .hero-inner {{
      width: min(1440px, 100%);
      margin: 0 auto;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      align-items: end;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: clamp(32px, 5vw, 66px);
      line-height: .95;
      letter-spacing: 0;
    }}
    .hero p {{ max-width: 760px; margin: 0; color: rgba(255,255,255,.82); font-size: 16px; line-height: 1.7; }}
    .hero-actions {{ display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      min-height: 38px;
      border: 1px solid rgba(255,255,255,.24);
      border-radius: 8px;
      padding: 8px 13px;
      color: #fff;
      background: rgba(255,255,255,.14);
      cursor: pointer;
      text-decoration: none;
    }}
    .button.dark {{
      color: var(--ink);
      border-color: var(--line);
      background: var(--panel);
    }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 5;
      border-bottom: 1px solid var(--line);
      background: rgba(244, 247, 251, .92);
      backdrop-filter: blur(14px);
    }}
    .toolbar-inner {{
      width: min(1440px, calc(100% - 32px));
      margin: 0 auto;
      padding: 14px 0;
      display: grid;
      grid-template-columns: 190px 180px 1fr 280px;
      gap: 12px;
      align-items: center;
    }}
    .control {{
      width: 100%;
      min-height: 40px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--ink);
      padding: 8px 10px;
      outline: none;
    }}
    .segments {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 4px;
      padding: 4px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }}
    .segment {{
      border: 0;
      border-radius: 6px;
      min-height: 32px;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
    }}
    .segment.active {{ background: #12343b; color: #fff; }}
    main {{
      width: min(1440px, calc(100% - 32px));
      margin: 20px auto 48px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .stat, .panel, .repo-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }}
    .stat {{ padding: 16px; }}
    .stat .label {{ color: var(--muted); font-size: 13px; }}
    .stat .value {{ margin-top: 5px; font-size: 28px; font-weight: 800; letter-spacing: 0; }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(360px, .85fr);
      gap: 18px;
      align-items: start;
    }}
    .panel {{ overflow: hidden; }}
    .panel-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      padding: 16px 16px 12px;
      border-bottom: 1px solid var(--line);
    }}
    .panel h2 {{ margin: 0; font-size: 17px; letter-spacing: 0; }}
    .hint {{ color: var(--muted); font-size: 13px; }}
    .repo-list {{ display: grid; gap: 10px; padding: 14px; }}
    .repo-card {{ box-shadow: none; padding: 14px; }}
    .repo-top {{
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto;
      gap: 10px;
      align-items: start;
    }}
    .rank {{
      min-width: 36px;
      height: 30px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      background: #e7f6f2;
      color: var(--accent);
      font-weight: 800;
    }}
    .repo-card h3 {{
      margin: 2px 0 5px;
      font-size: 15px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }}
    .repo-card h3 a {{ text-decoration: none; }}
    .repo-card h3 a:hover {{ text-decoration: underline; }}
    .desc {{
      color: #475467;
      font-size: 13px;
      line-height: 1.55;
      margin: 0;
      overflow-wrap: anywhere;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
      color: var(--muted);
      font-size: 12px;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 8px;
      border: 1px solid #d8e0ea;
      background: #f8fafc;
      padding: 3px 8px;
      white-space: nowrap;
    }}
    .share-mini {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      min-width: 34px;
      height: 34px;
      cursor: pointer;
    }}
    .leaderboard {{ width: 100%; border-collapse: collapse; }}
    .leaderboard th, .leaderboard td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      font-size: 13px;
    }}
    .leaderboard th {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      background: #f8fafc;
      position: sticky;
      top: 69px;
      z-index: 2;
    }}
    .leaderboard a {{ text-decoration: none; font-weight: 750; overflow-wrap: anywhere; }}
    .leaderboard a:hover {{ text-decoration: underline; }}
    .spark {{
      display: grid;
      grid-auto-flow: column;
      grid-auto-columns: 8px;
      align-items: end;
      gap: 3px;
      height: 34px;
      min-width: 84px;
    }}
    .bar {{
      width: 8px;
      border-radius: 4px 4px 0 0;
      background: var(--accent-3);
      opacity: .82;
    }}
    .empty {{
      padding: 28px;
      color: var(--muted);
      text-align: center;
    }}
    .footer-note {{
      margin: 18px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }}
    @media (max-width: 1000px) {{
      .hero-inner, .grid {{ grid-template-columns: 1fr; }}
      .hero-actions {{ justify-content: flex-start; }}
      .toolbar-inner {{ grid-template-columns: 1fr 1fr; }}
      .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 680px) {{
      .hero {{ padding: 24px 16px 18px; }}
      .toolbar-inner, main {{ width: calc(100% - 20px); }}
      .toolbar-inner, .stats {{ grid-template-columns: 1fr; }}
      .leaderboard th:nth-child(4), .leaderboard td:nth-child(4) {{ display: none; }}
      .repo-top {{ grid-template-columns: auto minmax(0, 1fr); }}
      .share-mini {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div class="app-shell">
    <header class="hero">
      <div class="hero-inner">
        <div>
          <h1>GitHub Trending Dashboard</h1>
          <p>从本仓库每天抓取的 Markdown 排名生成。支持按日期、语言、近一周、近一月浏览，链接可以带上当前筛选状态直接分享。</p>
        </div>
        <div class="hero-actions">
          <button class="button" id="copyShare">复制分享链接</button>
          <a class="button" id="openLatestMd" href="#" target="_blank" rel="noreferrer">打开当天 Markdown</a>
        </div>
      </div>
    </header>

    <section class="toolbar">
      <div class="toolbar-inner">
        <select class="control" id="dateSelect" aria-label="日期"></select>
        <select class="control" id="languageSelect" aria-label="语言"></select>
        <div class="segments" aria-label="时间范围">
          <button class="segment active" data-range="day">当天</button>
          <button class="segment" data-range="week">近一周</button>
          <button class="segment" data-range="month">近一月</button>
        </div>
        <input class="control" id="searchInput" type="search" placeholder="搜索仓库、作者或描述">
      </div>
    </section>

    <main>
      <section class="stats" id="stats"></section>
      <section class="grid">
        <section class="panel">
          <div class="panel-head">
            <div>
              <h2 id="primaryTitle">当天排名</h2>
              <div class="hint" id="primaryHint"></div>
            </div>
          </div>
          <div class="repo-list" id="repoList"></div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>周期热度榜</h2>
              <div class="hint">按出现次数、平均排名和最新排名综合展示</div>
            </div>
          </div>
          <div style="overflow:auto; max-height: 820px;">
            <table class="leaderboard">
              <thead>
                <tr>
                  <th>仓库</th>
                  <th>出现</th>
                  <th>均排</th>
                  <th>趋势</th>
                </tr>
              </thead>
              <tbody id="leaderboard"></tbody>
            </table>
          </div>
        </section>
      </section>
      <p class="footer-note" id="footerNote"></p>
    </main>
  </div>

  <script id="dashboard-data" type="application/json">{data}</script>
  <script>
    const DATA = JSON.parse(document.getElementById('dashboard-data').textContent);
    const state = {{
      date: DATA.latestDate,
      language: 'all',
      range: 'day',
      q: ''
    }};

    const els = {{
      dateSelect: document.getElementById('dateSelect'),
      languageSelect: document.getElementById('languageSelect'),
      searchInput: document.getElementById('searchInput'),
      stats: document.getElementById('stats'),
      repoList: document.getElementById('repoList'),
      leaderboard: document.getElementById('leaderboard'),
      primaryTitle: document.getElementById('primaryTitle'),
      primaryHint: document.getElementById('primaryHint'),
      footerNote: document.getElementById('footerNote'),
      copyShare: document.getElementById('copyShare'),
      openLatestMd: document.getElementById('openLatestMd')
    }};

    const byDate = new Map();
    for (const entry of DATA.entries) {{
      if (!byDate.has(entry.date)) byDate.set(entry.date, []);
      byDate.get(entry.date).push(entry);
    }}

    function initControls() {{
      els.dateSelect.innerHTML = DATA.dates.slice().reverse().map(date => `<option value="${{date}}">${{date}}</option>`).join('');
      els.languageSelect.innerHTML = '<option value="all">全部语言</option>' + DATA.languages.map(lang => `<option value="${{escapeHtml(lang)}}">${{escapeHtml(lang)}}</option>`).join('');
      readHash();
      syncControls();
    }}

    function readHash() {{
      const params = new URLSearchParams(location.hash.replace(/^#/, ''));
      const date = params.get('date');
      const language = params.get('language');
      const range = params.get('range');
      const q = params.get('q');
      if (date && DATA.dates.includes(date)) state.date = date;
      if (language && (language === 'all' || DATA.languages.includes(language))) state.language = language;
      if (['day', 'week', 'month'].includes(range)) state.range = range;
      if (q) state.q = q;
    }}

    function syncControls() {{
      els.dateSelect.value = state.date;
      els.languageSelect.value = state.language;
      els.searchInput.value = state.q;
      document.querySelectorAll('.segment').forEach(button => button.classList.toggle('active', button.dataset.range === state.range));
    }}

    function updateHash() {{
      const params = new URLSearchParams();
      params.set('date', state.date);
      params.set('language', state.language);
      params.set('range', state.range);
      if (state.q) params.set('q', state.q);
      history.replaceState(null, '', '#' + params.toString());
    }}

    function selectedDates() {{
      const endIndex = DATA.dates.indexOf(state.date);
      const count = state.range === 'month' ? 30 : state.range === 'week' ? 7 : 1;
      return DATA.dates.slice(Math.max(0, endIndex - count + 1), endIndex + 1);
    }}

    function filteredEntries() {{
      const dates = new Set(selectedDates());
      const q = state.q.trim().toLowerCase();
      return DATA.entries.filter(entry => {{
        if (!dates.has(entry.date)) return false;
        if (state.language !== 'all' && entry.language !== state.language) return false;
        if (!q) return true;
        return [entry.title, entry.repo, entry.description, entry.language].some(value => (value || '').toLowerCase().includes(q));
      }});
    }}

    function render() {{
      updateHash();
      const entries = filteredEntries();
      const dates = selectedDates();
      const daily = entries.filter(entry => entry.date === state.date);
      const languages = new Set(entries.map(entry => entry.language));
      const repos = new Set(entries.map(entry => entry.repo));
      const repeated = summarize(entries).filter(row => row.count > 1).length;
      renderStats([
        ['数据日期', state.range === 'day' ? state.date : `${{dates[0]}} 至 ${{dates[dates.length - 1]}}`],
        ['仓库数量', repos.size.toLocaleString()],
        ['语言数量', languages.size.toLocaleString()],
        ['重复上榜', repeated.toLocaleString()]
      ]);
      renderPrimary(state.range === 'day' ? daily : entries);
      renderLeaderboard(entries);
      const mdPath = state.date.startsWith('2025') || state.date.startsWith('2026') ? `${{state.date}}.md` : `${{state.date.slice(0, 4)}}/${{state.date}}.md`;
      els.openLatestMd.href = mdPath;
      els.footerNote.textContent = `数据生成时间：${{new Date(DATA.generatedAt).toLocaleString()}}。当前 HTML 内嵌最近 ${{DATA.includedDays}} 天 / 总计 ${{DATA.totalDays}} 天中的 ${{DATA.entries.length.toLocaleString()}} 条排名记录，可以作为单个 HTML 文件分享。`;
    }}

    function renderStats(items) {{
      els.stats.innerHTML = items.map(([label, value]) => `
        <article class="stat">
          <div class="label">${{escapeHtml(label)}}</div>
          <div class="value">${{escapeHtml(value)}}</div>
        </article>
      `).join('');
    }}

    function renderPrimary(entries) {{
      const title = state.range === 'day' ? '当天排名' : (state.range === 'week' ? '近一周明细' : '近一月明细');
      els.primaryTitle.textContent = title;
      els.primaryHint.textContent = `${{state.language === 'all' ? '全部语言' : state.language}}，${{entries.length}} 条记录`;
      const sorted = entries.slice().sort((a, b) => b.date.localeCompare(a.date) || a.language.localeCompare(b.language) || a.rank - b.rank).slice(0, 80);
      if (!sorted.length) {{
        els.repoList.innerHTML = '<div class="empty">没有匹配的排名记录</div>';
        return;
      }}
      els.repoList.innerHTML = sorted.map(entry => `
        <article class="repo-card">
          <div class="repo-top">
            <span class="rank">#${{entry.rank}}</span>
            <div>
              <h3><a href="${{entry.url}}" target="_blank" rel="noreferrer">${{escapeHtml(entry.title)}}</a></h3>
              <p class="desc">${{escapeHtml(entry.description || '暂无描述')}}</p>
            </div>
            <button class="share-mini" title="复制该仓库链接" data-url="${{entry.url}}">↗</button>
          </div>
          <div class="meta">
            <span class="pill">${{entry.date}}</span>
            <span class="pill">${{escapeHtml(entry.language)}}</span>
            <span class="pill">${{escapeHtml(entry.repo)}}</span>
          </div>
        </article>
      `).join('');
    }}

    function summarize(entries) {{
      const groups = new Map();
      for (const entry of entries) {{
        if (!groups.has(entry.repo)) groups.set(entry.repo, []);
        groups.get(entry.repo).push(entry);
      }}
      return Array.from(groups.entries()).map(([repo, rows]) => {{
        rows.sort((a, b) => a.date.localeCompare(b.date));
        const latest = rows[rows.length - 1];
        const avgRank = rows.reduce((sum, item) => sum + item.rank, 0) / rows.length;
        return {{
          repo,
          title: latest.title,
          url: latest.url,
          description: latest.description,
          count: rows.length,
          avgRank,
          latestRank: latest.rank,
          languages: Array.from(new Set(rows.map(row => row.language))).join(', '),
          dates: rows.map(row => row.date),
          ranks: rows.map(row => row.rank)
        }};
      }}).sort((a, b) => b.count - a.count || a.avgRank - b.avgRank || a.latestRank - b.latestRank);
    }}

    function renderLeaderboard(entries) {{
      const rows = summarize(entries).slice(0, 40);
      if (!rows.length) {{
        els.leaderboard.innerHTML = '<tr><td class="empty" colspan="4">没有匹配的仓库</td></tr>';
        return;
      }}
      els.leaderboard.innerHTML = rows.map(row => `
        <tr>
          <td>
            <a href="${{row.url}}" target="_blank" rel="noreferrer">${{escapeHtml(row.title)}}</a>
            <div class="hint">${{escapeHtml(row.languages)}}</div>
          </td>
          <td>${{row.count}}</td>
          <td>${{row.avgRank.toFixed(1)}}</td>
          <td><div class="spark" title="${{escapeHtml(row.dates.join(', '))}}">${{sparkBars(row.ranks)}}</div></td>
        </tr>
      `).join('');
    }}

    function sparkBars(ranks) {{
      return ranks.slice(-14).map(rank => {{
        const height = Math.max(8, 36 - Math.min(rank, 20) * 1.45);
        return `<span class="bar" style="height:${{height}}px"></span>`;
      }}).join('');
    }}

    function escapeHtml(value) {{
      return String(value ?? '').replace(/[&<>"']/g, char => ({{
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      }}[char]));
    }}

    els.dateSelect.addEventListener('change', event => {{ state.date = event.target.value; render(); }});
    els.languageSelect.addEventListener('change', event => {{ state.language = event.target.value; render(); }});
    els.searchInput.addEventListener('input', event => {{ state.q = event.target.value; render(); }});
    document.querySelectorAll('.segment').forEach(button => {{
      button.addEventListener('click', () => {{ state.range = button.dataset.range; syncControls(); render(); }});
    }});
    els.copyShare.addEventListener('click', async () => {{
      updateHash();
      const url = location.href;
      try {{
        await navigator.clipboard.writeText(url);
        els.copyShare.textContent = '已复制链接';
      }} catch (error) {{
        prompt('复制这个链接分享', url);
      }}
      setTimeout(() => els.copyShare.textContent = '复制分享链接', 1600);
    }});
    document.body.addEventListener('click', async event => {{
      const button = event.target.closest('.share-mini');
      if (!button) return;
      try {{
        await navigator.clipboard.writeText(button.dataset.url);
        button.textContent = '✓';
        setTimeout(() => button.textContent = '↗', 1200);
      }} catch (error) {{
        prompt('复制仓库链接', button.dataset.url);
      }}
    }});

    initControls();
    render();
  </script>
</body>
</html>
"""


def parse_args():
    parser = argparse.ArgumentParser(description="Build a shareable GitHub Trending dashboard.")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help=f"days to include, default {DEFAULT_DAYS}")
    parser.add_argument("--all", action="store_true", help="include all historical markdown files")
    parser.add_argument("--output", default=str(OUT_FILE), help="output html path")
    return parser.parse_args()


def main():
    args = parse_args()
    days = 0 if args.all else max(args.days, 1)
    payload = collect_data(days=days)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    global OUT_FILE
    OUT_FILE = output
    OUT_FILE.write_text(render_html(payload), encoding="utf-8")
    print(f"Wrote {OUT_FILE}")
    print(
        "Dates: {included}/{total}, languages: {languages}, entries: {entries}".format(
            included=len(payload["dates"]),
            total=payload["totalDays"],
            languages=len(payload["languages"]),
            entries=len(payload["entries"]),
        )
    )


if __name__ == "__main__":
    main()
