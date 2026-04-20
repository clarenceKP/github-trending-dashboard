# coding: utf-8

import datetime as dt
import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT_FILE = ROOT / "dashboard.html"
DATE_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
ITEM_RE = re.compile(
    r"^\* \[(?P<title>.+?)\]\((?P<url>https://github\.com/[^)]+)\):(?P<description>.*?)(?:\s*<!-- (?P<meta>.*?) -->)?$"
)
META_RE = re.compile(r"(stars|forks|stars_today):(\d+)")
DEFAULT_DAYS = 370


def parse_meta(raw_meta):
    values = {"stars": None, "forks": None, "starsToday": None}
    if not raw_meta:
        return values
    key_map = {"stars": "stars", "forks": "forks", "stars_today": "starsToday"}
    for key, value in META_RE.findall(raw_meta):
        values[key_map[key]] = int(value)
    return values


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
        meta = parse_meta(match.group("meta"))
        entries.append(
            {
                "date": date,
                "language": current_language,
                "rank": rank,
                "title": title,
                "repo": owner_repo,
                "url": url,
                "description": match.group("description").strip(),
                "stars": meta["stars"],
                "forks": meta["forks"],
                "starsToday": meta["starsToday"],
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
      --ink: #172033;
      --muted: #667085;
      --line: rgba(132, 152, 179, .32);
      --panel: rgba(255, 255, 255, .74);
      --panel-strong: rgba(255, 255, 255, .88);
      --soft: rgba(246, 248, 251, .86);
      --accent: #087568;
      --accent-2: #b42318;
      --accent-3: #6e56cf;
      --good: #067647;
      --shadow: 0 22px 60px rgba(32, 48, 74, 0.12);
      --glass: saturate(180%) blur(24px);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        linear-gradient(180deg, rgba(246, 249, 252, .98), rgba(231, 238, 247, .94)),
        linear-gradient(120deg, rgba(219, 244, 239, .52), rgba(239, 243, 255, .68));
    }}
    button, input, select {{ font: inherit; }}
    a {{ color: inherit; }}
    .app-shell {{ min-height: 100vh; }}
    .hero {{
      padding: 30px 28px 22px;
      color: #fff;
      background:
        linear-gradient(115deg, rgba(10, 37, 48, .92), rgba(12, 92, 78, .78)),
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
      font-size: 58px;
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
      background: rgba(255,255,255,.16);
      backdrop-filter: var(--glass);
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
      background: rgba(246, 248, 252, .76);
      backdrop-filter: var(--glass);
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
      background: rgba(255,255,255,.76);
      color: var(--ink);
      padding: 8px 10px;
      outline: none;
    }}
    .control:focus {{
      border-color: rgba(8,117,104,.55);
      box-shadow: 0 0 0 4px rgba(8,117,104,.10);
    }}
    .segments {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 4px;
      padding: 4px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,.68);
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
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .stat, .panel, .repo-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
      backdrop-filter: var(--glass);
    }}
    .domain-tabs {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
      padding: 6px;
      width: max-content;
      max-width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,.58);
      backdrop-filter: var(--glass);
      box-shadow: 0 16px 42px rgba(32,48,74,.08);
    }}
    .domain-tab {{
      min-height: 34px;
      border: 0;
      border-radius: 7px;
      padding: 6px 14px;
      color: #475467;
      background: transparent;
      cursor: pointer;
    }}
    .domain-tab.active {{
      color: #fff;
      background: #172033;
      box-shadow: 0 10px 24px rgba(23,32,51,.18);
    }}
    .stat {{ padding: 16px; }}
    .stat .label {{ color: var(--muted); font-size: 13px; }}
    .stat .value {{ margin-top: 5px; font-size: 24px; font-weight: 800; letter-spacing: 0; overflow-wrap: anywhere; }}
    .brief {{
      margin-bottom: 18px;
      padding: 18px;
    }}
    .brief h2 {{
      margin: 0 0 8px;
      font-size: 18px;
      letter-spacing: 0;
    }}
    .brief p {{
      margin: 0;
      color: #344054;
      line-height: 1.7;
      font-size: 15px;
    }}
    .brief strong {{ color: var(--ink); }}
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
    .repo-card {{ box-shadow: none; padding: 14px; background: rgba(255,255,255,.74); }}
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
    .metric-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
      color: #344054;
      font-size: 13px;
    }}
    .metric {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      min-height: 28px;
      border-radius: 8px;
      background: #eef7f4;
      color: #095c51;
      padding: 4px 9px;
      font-weight: 700;
    }}
    .metric.hot {{ background: #fff4e5; color: #9a4b00; }}
    .metric.rising {{ background: #f4efff; color: #6941c6; }}
    .badge {{
      display: inline-flex;
      min-height: 22px;
      align-items: center;
      border-radius: 8px;
      padding: 2px 7px;
      margin-left: 6px;
      color: #fff;
      background: var(--accent);
      font-size: 11px;
      font-weight: 800;
      vertical-align: middle;
    }}
    .badge.rising {{ background: var(--accent-3); }}
    .badge.score {{ background: var(--accent-2); }}
    .badge.ai {{ background: #175cd3; }}
    .badge.finance {{ background: #027a48; }}
    .pill {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 8px;
      border: 1px solid #d8e0ea;
      background: rgba(248,250,252,.82);
      padding: 3px 8px;
      white-space: nowrap;
    }}
    .share-mini {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,.76);
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
      background: rgba(248,250,252,.92);
      position: sticky;
      top: 0;
      z-index: 3;
      backdrop-filter: var(--glass);
      box-shadow: 0 1px 0 var(--line), 0 10px 20px rgba(32,48,74,.06);
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
      .stats {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    }}
    @media (max-width: 680px) {{
      .hero {{ padding: 24px 16px 18px; }}
      h1 {{ font-size: 34px; line-height: 1; }}
      .toolbar-inner, main {{ width: calc(100% - 20px); }}
      .toolbar-inner, .stats {{ grid-template-columns: 1fr; }}
      .domain-tabs {{ width: 100%; }}
      .domain-tab {{ flex: 1; }}
      .leaderboard th:nth-child(4), .leaderboard td:nth-child(4),
      .leaderboard th:nth-child(5), .leaderboard td:nth-child(5),
      .leaderboard th:nth-child(7), .leaderboard td:nth-child(7) {{ display: none; }}
      .repo-top {{ grid-template-columns: auto minmax(0, 1fr); }}
      .share-mini {{ display: none; }}
    }}
    @media (min-width: 681px) and (max-width: 1000px) {{
      h1 {{ font-size: 44px; }}
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
        <input class="control" id="searchInput" type="search" placeholder="模糊搜索：repo、作者、关键词">
      </div>
    </section>

    <main>
      <nav class="domain-tabs" id="domainTabs" aria-label="重点领域">
        <button class="domain-tab active" data-domain="all">整体视图</button>
        <button class="domain-tab" data-domain="ai">AI 项目</button>
        <button class="domain-tab" data-domain="finance">金融项目</button>
      </nav>
      <section class="panel brief" id="periodBrief"></section>
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
              <h2>综合评分榜</h2>
              <div class="hint">以 Stars 和增长为主权重，兼顾上榜频次与排名</div>
            </div>
          </div>
          <div style="overflow:auto; max-height: 820px;">
            <table class="leaderboard">
              <thead>
                <tr>
                  <th>仓库</th>
                  <th title="推荐分由 Stars、增长、上榜次数和排名加权得到">推荐分</th>
                  <th>出现</th>
                  <th>Stars</th>
                  <th>+Stars</th>
                  <th>均排</th>
                  <th title="柱越高代表对应日期的语言排名越靠前">排名走势</th>
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
      domain: 'all',
      range: 'day',
      q: ''
    }};

    const els = {{
      dateSelect: document.getElementById('dateSelect'),
      languageSelect: document.getElementById('languageSelect'),
      searchInput: document.getElementById('searchInput'),
      domainTabs: document.getElementById('domainTabs'),
      periodBrief: document.getElementById('periodBrief'),
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
      const domain = params.get('domain');
      const range = params.get('range');
      const q = params.get('q');
      if (date && DATA.dates.includes(date)) state.date = date;
      if (language && (language === 'all' || DATA.languages.includes(language))) state.language = language;
      if (['all', 'ai', 'finance'].includes(domain)) state.domain = domain;
      if (['day', 'week', 'month'].includes(range)) state.range = range;
      if (q) state.q = q;
    }}

    function syncControls() {{
      els.dateSelect.value = state.date;
      els.languageSelect.value = state.language;
      els.searchInput.value = state.q;
      document.querySelectorAll('.segment').forEach(button => button.classList.toggle('active', button.dataset.range === state.range));
      document.querySelectorAll('.domain-tab').forEach(button => button.classList.toggle('active', button.dataset.domain === state.domain));
    }}

    function updateHash() {{
      const params = new URLSearchParams();
      params.set('date', state.date);
      params.set('language', state.language);
      params.set('domain', state.domain);
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
      return DATA.entries.filter(entry => {{
        if (!dates.has(entry.date)) return false;
        if (state.language !== 'all' && entry.language !== state.language) return false;
        if (state.domain !== 'all' && !entryMatchesDomain(entry, state.domain)) return false;
        return true;
      }});
    }}

    const DOMAIN_RULES = {{
      ai: [
        /(^|[^a-z])ai([^a-z]|$)/, /openai/, /llm/, /gpt/, /agent/, /rag/, /embedding/, /vector/,
        /machine learning/, /deep learning/, /neural/, /transformer/, /diffusion/, /inference/,
        /model/, /chatbot/, /computer vision/, /llama/, /ollama/, /langchain/, /langgraph/,
        /人工智能/, /大模型/, /智能体/, /机器学习/, /深度学习/, /模型/
      ],
      finance: [
        /finance/, /financial/, /fintech/, /market/, /investment/, /investing/, /trading/, /trader/,
        /stock/, /equity/, /portfolio/, /quant/, /hedge/, /bank/, /payment/, /crypto/, /bitcoin/,
        /blockchain/, /economics/, /terminal/, /财富/, /金融/, /投资/, /股票/, /市场/, /交易/, /量化/, /基金/, /银行/
      ]
    }};

    function entryDomains(entry) {{
      const text = `${{entry.title || ''}} ${{entry.repo || ''}} ${{entry.description || ''}}`.toLowerCase();
      return Object.entries(DOMAIN_RULES)
        .filter(([, rules]) => rules.some(rule => rule.test(text)))
        .map(([domain]) => domain);
    }}

    function entryMatchesDomain(entry, domain) {{
      return entryDomains(entry).includes(domain);
    }}

    function domainLabel(domain) {{
      return domain === 'ai' ? 'AI' : domain === 'finance' ? '金融' : '整体';
    }}

    function domainBadges(domains) {{
      return (domains || []).map(domain => `<span class="badge ${{domain}}">${{domainLabel(domain)}}</span>`).join('');
    }}

    function normalizeSearch(value) {{
      return String(value ?? '')
        .toLowerCase()
        .normalize('NFKD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9\u4e00-\u9fff]+/g, ' ')
        .trim();
    }}

    function subsequenceScore(token, haystack) {{
      let tokenIndex = 0;
      let first = -1;
      let previous = -1;
      let gaps = 0;
      for (let i = 0; i < haystack.length && tokenIndex < token.length; i += 1) {{
        if (haystack[i] !== token[tokenIndex]) continue;
        if (first === -1) first = i;
        if (previous !== -1) gaps += i - previous - 1;
        previous = i;
        tokenIndex += 1;
      }}
      if (tokenIndex !== token.length) return -1;
      return 45 + token.length * 6 - gaps * 0.7 - first * 0.15;
    }}

    function fuzzyScore(query, value) {{
      const q = normalizeSearch(query);
      const haystack = normalizeSearch(value);
      if (!q) return 0;
      if (!haystack) return -1;
      const compactHaystack = haystack.replace(/\s+/g, '');
      const tokens = q.split(/\s+/).filter(Boolean);
      let total = 0;
      for (const token of tokens) {{
        const compactToken = token.replace(/\s+/g, '');
        const exactIndex = haystack.indexOf(token);
        if (exactIndex >= 0) {{
          total += 120 + token.length * 4 - Math.min(exactIndex, 80) * 0.45;
          continue;
        }}
        const compactIndex = compactHaystack.indexOf(compactToken);
        if (compactIndex >= 0) {{
          total += 92 + compactToken.length * 3 - Math.min(compactIndex, 80) * 0.35;
          continue;
        }}
        const loose = subsequenceScore(compactToken, compactHaystack);
        if (loose < 0) return -1;
        total += loose;
      }}
      return total;
    }}

    function rowSearchText(row) {{
      return [
        row.title,
        row.repo,
        row.description,
        row.languages,
        ...(row.domains || []).map(domainLabel)
      ].join(' ');
    }}

    function searchRows(rows) {{
      const q = state.q.trim();
      if (!q) return rows;
      return rows
        .map(row => ({{ ...row, searchScore: fuzzyScore(q, rowSearchText(row)) }}))
        .filter(row => row.searchScore >= 0)
        .sort((a, b) => b.searchScore - a.searchScore || b.score - a.score);
    }}

    function render() {{
      updateHash();
      const entries = filteredEntries();
      const dates = selectedDates();
      const allRows = summarize(entries);
      const rows = searchRows(allRows);
      const languages = new Set(rows.flatMap(row => row.languages.split(', ').filter(Boolean)));
      const repos = new Set(rows.map(row => row.repo));
      const repeated = rows.filter(row => row.count > 1).length;
      const starEntries = rows.filter(row => Number.isFinite(row.latestStars));
      const totalStarsToday = rows.reduce((sum, row) => sum + (row.starsToday || 0), 0);
      const hottest = rows.filter(row => Number.isFinite(row.latestStars)).sort((a, b) => b.latestStars - a.latestStars)[0];
      const fastest = rows.filter(row => Number.isFinite(row.growth)).sort((a, b) => b.growth - a.growth)[0];
      const recommended = rankRows(rows);
      renderBrief(recommended, dates);
      renderStats([
        ['数据日期', state.range === 'day' ? state.date : `${{dates[0]}} 至 ${{dates[dates.length - 1]}}`],
        ['仓库数量', repos.size.toLocaleString()],
        ['有 Star 数据', starEntries.length.toLocaleString()],
        ['今日新增 Stars', formatNumber(totalStarsToday)],
        ['最高 Stars', hottest ? formatNumber(hottest.latestStars) : '暂无'],
        ['最快增长', fastest ? `+${{formatNumber(fastest.growth)}}` : '暂无']
      ]);
      renderPrimary(recommended);
      renderLeaderboard(entries, recommended);
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

    function renderBrief(rows, dates) {{
      const top = rows[0];
      const hottest = rows.filter(row => Number.isFinite(row.latestStars)).sort((a, b) => b.latestStars - a.latestStars)[0];
      const fastest = rows.filter(row => Number.isFinite(row.growth)).sort((a, b) => b.growth - a.growth)[0];
      const starEntries = rows.filter(row => Number.isFinite(row.latestStars));
      const periodLabel = state.range === 'day' ? state.date : `${{dates[0]}} 至 ${{dates[dates.length - 1]}}`;
      if (!rows.length) {{
        els.periodBrief.innerHTML = '<h2>周期导读</h2><p>当前筛选条件下没有可展示的项目。</p>';
        return;
      }}
      const coverage = starEntries.length ? `其中 ${{starEntries.length}} 条记录带有 star 快照，排序会优先参考项目体量和增长速度。` : '当前周期大多是历史旧记录，缺少 star 快照，排序会回退参考上榜频次和排名。';
      const topText = `<strong>${{escapeHtml(top.title)}}</strong> 是综合推荐榜首，推荐分 ${{top.score.toFixed(1)}}，最新 Stars ${{formatNumber(top.latestStars)}}，周期新增 ${{top.growth ? '+' + formatNumber(top.growth) : '暂无'}}。`;
      const hotText = hottest ? `最热门项目是 <strong>${{escapeHtml(hottest.title)}}</strong>，总 Stars ${{formatNumber(hottest.latestStars)}}。` : '';
      const fastText = fastest ? `飙升最快的是 <strong>${{escapeHtml(fastest.title)}}</strong>，本周期新增 ${{fastest.growth ? '+' + formatNumber(fastest.growth) : '暂无'}}。` : '';
      const scopeLabel = state.domain === 'all' ? (state.language === 'all' ? '跨语言' : escapeHtml(state.language)) : domainLabel(state.domain);
      els.periodBrief.innerHTML = `<h2>周期导读</h2><p>${{periodLabel}}，${{scopeLabel}}共观察到 ${{rows.length}} 个独立项目。${{coverage}} ${{topText}} ${{hotText}} ${{fastText}}</p>`;
    }}

    function renderPrimary(rows) {{
      const title = state.range === 'day' ? '综合推荐榜' : (state.range === 'week' ? '近一周综合推荐' : '近一月综合推荐');
      els.primaryTitle.textContent = title;
      els.primaryHint.textContent = `${{state.domain === 'all' ? (state.language === 'all' ? '跨语言整体视图' : state.language) : domainLabel(state.domain)}}，按 Stars、增长、上榜稳定性和排名综合排序${{state.q.trim() ? '，已启用模糊搜索' : ''}}`;
      const sorted = rows.slice(0, 80);
      if (!sorted.length) {{
        els.repoList.innerHTML = '<div class="empty">没有匹配的排名记录</div>';
        return;
      }}
      els.repoList.innerHTML = sorted.map((row, index) => `
        <article class="repo-card">
          <div class="repo-top">
            <span class="rank">#${{index + 1}}</span>
            <div>
              <h3><a href="${{row.url}}" target="_blank" rel="noreferrer">${{escapeHtml(row.title)}}</a>${{row.latestStars >= 50000 ? '<span class="badge">高星口碑</span>' : ''}}${{row.growth >= 500 ? '<span class="badge rising">飙升项目</span>' : ''}}${{domainBadges(row.domains)}}<span class="badge score" title="推荐分由 Stars、增长、上榜次数和排名加权得到">推荐分 ${{row.score.toFixed(1)}}</span></h3>
              <p class="desc">${{escapeHtml(row.description || '暂无描述')}}</p>
              <div class="metric-row">${{rowMetrics(row)}}</div>
            </div>
            <button class="share-mini" title="复制该仓库链接" data-url="${{row.url}}">↗</button>
          </div>
          <div class="meta">
            <span class="pill">最新 ${{row.latestDate}}</span>
            <span class="pill">${{escapeHtml(row.languages)}}</span>
            <span class="pill">语言排名 #${{row.latestRank}}</span>
            <span class="pill">${{escapeHtml(row.repo)}}</span>
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
        const starRows = rows.filter(row => Number.isFinite(row.stars));
        const firstStar = starRows[0];
        const latestStar = starRows[starRows.length - 1];
        const avgRank = rows.reduce((sum, item) => sum + item.rank, 0) / rows.length;
        const sameDayGrowth = latest.starsToday || 0;
        const periodGrowth = firstStar && latestStar && firstStar !== latestStar ? latestStar.stars - firstStar.stars : sameDayGrowth;
        return {{
          repo,
          title: latest.title,
          url: latest.url,
          description: latest.description,
          count: rows.length,
          avgRank,
          latestRank: latest.rank,
          latestDate: latest.date,
          latestStars: latestStar ? latestStar.stars : null,
          latestForks: latestStar ? latestStar.forks : null,
          starsToday: sameDayGrowth,
          growth: Number.isFinite(periodGrowth) ? Math.max(0, periodGrowth) : null,
          languages: Array.from(new Set(rows.map(row => row.language))).join(', '),
          domains: Array.from(new Set(rows.flatMap(row => entryDomains(row)))),
          dates: rows.map(row => row.date),
          ranks: rows.map(row => row.rank)
        }};
      }}).map(row => {{
        row.score = scoreRow(row);
        return row;
      }}).sort((a, b) => b.score - a.score || b.count - a.count || a.avgRank - b.avgRank || a.latestRank - b.latestRank);
    }}

    function scoreRow(row) {{
      const starScore = Number.isFinite(row.latestStars) ? Math.log10(row.latestStars + 1) * 28 : 0;
      const growthScore = Number.isFinite(row.growth) ? Math.log10(row.growth + 1) * 34 : 0;
      const todayScore = Number.isFinite(row.starsToday) ? Math.log10(row.starsToday + 1) * 18 : 0;
      const rankScore = Math.max(0, 22 - row.avgRank);
      const stabilityScore = Math.min(row.count, 10) * 3;
      return starScore + growthScore + todayScore + rankScore + stabilityScore;
    }}

    function rankRows(rows) {{
      return rows.slice().sort((a, b) => b.score - a.score || (b.latestStars || 0) - (a.latestStars || 0) || (b.growth || 0) - (a.growth || 0) || a.avgRank - b.avgRank);
    }}

    function renderLeaderboard(entries, summarizedRows) {{
      const rows = rankRows(summarizedRows || summarize(entries)).slice(0, 40);
      if (!rows.length) {{
        els.leaderboard.innerHTML = '<tr><td class="empty" colspan="7">没有匹配的仓库</td></tr>';
        return;
      }}
      els.leaderboard.innerHTML = rows.map(row => `
        <tr>
          <td>
            <a href="${{row.url}}" target="_blank" rel="noreferrer">${{escapeHtml(row.title)}}</a>${{row.latestStars >= 50000 ? '<span class="badge">高星口碑</span>' : ''}}${{row.growth >= 500 ? '<span class="badge rising">飙升项目</span>' : ''}}${{domainBadges(row.domains)}}
            <div class="hint">${{escapeHtml(row.languages)}}</div>
          </td>
          <td>${{row.score.toFixed(1)}}</td>
          <td>${{row.count}}</td>
          <td>${{formatNumber(row.latestStars)}}</td>
          <td>${{row.growth ? '+' + formatNumber(row.growth) : '暂无'}}</td>
          <td>${{row.avgRank.toFixed(1)}}</td>
          <td><div class="spark" title="${{escapeHtml(row.dates.join(', '))}}">${{sparkBars(row.ranks)}}</div></td>
        </tr>
      `).join('');
    }}

    function entryMetrics(entry) {{
      if (!Number.isFinite(entry.stars)) {{
        return '<span class="metric">暂无 star 快照</span>';
      }}
      const starsToday = entry.starsToday ? `+${{formatNumber(entry.starsToday)}} 今日` : '今日暂无';
      const forks = Number.isFinite(entry.forks) ? `Forks ${{formatNumber(entry.forks)}}` : 'Forks 暂无';
      return `
        <span class="metric hot">Stars ${{formatNumber(entry.stars)}}</span>
        <span class="metric rising">${{starsToday}}</span>
        <span class="metric">${{forks}}</span>
      `;
    }}

    function rowMetrics(row) {{
      if (!Number.isFinite(row.latestStars)) {{
        return '<span class="metric">暂无 star 快照</span>';
      }}
      const growth = row.growth ? `+${{formatNumber(row.growth)}} 周期` : '周期暂无';
      const today = row.starsToday ? `+${{formatNumber(row.starsToday)}} 今日` : '今日暂无';
      const forks = Number.isFinite(row.latestForks) ? `Forks ${{formatNumber(row.latestForks)}}` : 'Forks 暂无';
      return `
        <span class="metric hot">Stars ${{formatNumber(row.latestStars)}}</span>
        <span class="metric rising">${{growth}}</span>
        <span class="metric rising">${{today}}</span>
        <span class="metric">${{forks}}</span>
      `;
    }}

    function formatNumber(value) {{
      if (!Number.isFinite(value)) return '暂无';
      if (value >= 1000000) return `${{(value / 1000000).toFixed(value >= 10000000 ? 0 : 1)}}M`;
      if (value >= 1000) return `${{(value / 1000).toFixed(value >= 10000 ? 0 : 1)}}k`;
      return String(value);
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
    document.querySelectorAll('.domain-tab').forEach(button => {{
      button.addEventListener('click', () => {{ state.domain = button.dataset.domain; syncControls(); render(); }});
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
