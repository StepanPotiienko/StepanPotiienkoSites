#!/usr/bin/env python3
"""
Generator for the StepanPotiienkoSites /mockups cloud-disk index page.

Scans <repo>/mockups/*/index.html and emits <repo>/index.html — a SaaS
"soft-UI" cloud-disk listing (design ref: Dribbble "Hotel Guest List UI").

Run from anywhere:
    python3 generate_index.py            # writes index.html at repo root
    python3 generate_index.py --out X    # write to X
    python3 generate_index.py --dry-run  # print metadata, don't write

Auto-detects each mockup's title/description from its <title> and first
<h1>/<p>; falls back to the folder name. New mockups appear automatically.
"""

import argparse
import html
import os
import re
import subprocess
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
MOCKUPS_DIR = os.path.join(REPO_ROOT, "mockups")
OUT_DEFAULT = os.path.join(REPO_ROOT, "index.html")

ICONS = {  # emoji icons per product keyword (fallback: document)
    "ettn": "\U0001F69B",
    "globus": "\U0001F6D2",
    "meta": "\U0001F4E3",
    "ads": "\U0001F4E3",
    "agro": "\U0001F33E",
    "cactus": "\U0001F916",
    "ap": "\U0001F4CA",
}

TYPE_COLORS = {  # soft pastel pill backgrounds for status badges
    "green": ("#E7F2EB", "#2F6B4A"),
    "orange": ("#FBEDE2", "#A85A24"),
    "blue": ("#E7EDFB", "#2B46A8"),
    "gray": ("#EDEEF1", "#5A6070"),
}


def _read_head_text(path):
    """Extract <title>, description and h1 from a mockup."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read(200000)
    except OSError:
        return None, None, None

    title = None
    m = re.search(r"<title>([^<]+)</title>", text, re.I | re.S)
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()

    desc = None
    for pat in (
        r'<meta\s+name="description"\s+content="([^"]+)"',
        r"<p[^>]*>([^<]{20,})</p>",
        r"<h1[^>]*>([^<]{5,})</h1>",
    ):
        mm = re.search(pat, text, re.I | re.S)
        if mm:
            cand = re.sub(r"\s+", " ", mm.group(1)).strip()
            if cand:
                desc = cand
                break

    h1 = None
    mm = re.search(r"<h1[^>]*>([^<]+)</h1>", text, re.I | re.S)
    if mm:
        h1 = re.sub(r"\s+", " ", mm.group(1)).strip()

    return title, desc, h1


def _git_date(folder, full=False):
    """Best-effort first-commit timestamp for a mockup folder."""
    try:
        out = subprocess.run(
            ["git", "log", "--reverse", "--format=%ai", "--",
             os.path.join("mockups", folder)],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
        ).stdout.strip().splitlines()
        if out:
            ts = out[0]  # YYYY-MM-DD HH:MM:SS +0300
            return ts if full else ts.split(" ")[0]
    except Exception:
        pass
    return ""


def _icon_for(folder, title):
    low = (folder + " " + (title or "")).lower()
    for key, icon in ICONS.items():
        if key in low:
            return icon
    return "\U0001F4C4"


def scan_mockups():
    items = []
    if not os.path.isdir(MOCKUPS_DIR):
        return items
    for folder in sorted(os.listdir(MOCKUPS_DIR)):
        idx = os.path.join(MOCKUPS_DIR, folder, "index.html")
        if not os.path.isfile(idx):
            continue
        title, desc, h1 = _read_head_text(idx)
        if not title:
            title = folder
        items.append({
            "folder": folder,
            "title": title,
            "desc": desc or h1 or "",
            "date": _git_date(folder),
            "icon": _icon_for(folder, title),
            "href": "mockups/{}/index.html".format(folder),
        })
    return items


def _badge(item):
    return ("green", "New") if item.get("new") else ("gray", "Mockup")


def _build_cards(items):
    cards = []
    for it in items:
        bg, fg = TYPE_COLORS[_badge(it)[0]]
        badge_label = _badge(it)[1]
        date = it["date"] or "\u2014"
        desc = it["desc"] or "Marketing performance dashboard mockup"
        cards.append("""
        <a class="file-card" href="{href}" target="_blank" rel="noopener">
          <div class="card-icon">{icon}</div>
          <div class="card-body">
            <div class="card-top">
              <span class="card-name">{title}</span>
              <span class="pill" style="background:{bg};color:{fg}">{badge}</span>
            </div>
            <div class="card-desc">{desc}</div>
            <div class="card-meta">
              <span class="meta-path">mockups/{folder}/</span>
              <span class="dot">\u00b7</span>
              <span class="meta-date">{date}</span>
            </div>
          </div>
          <div class="card-arrow" aria-hidden="true">\u2197</div>
        </a>""".format(
            href=html.escape(it["href"]),
            icon=it["icon"],
            title=html.escape(it["title"]),
            bg=bg,
            fg=fg,
            badge=badge_label,
            desc=html.escape(desc),
            folder=html.escape(it["folder"]),
            date=date,
        ))
    return "".join(cards)


_TEMPLATE = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Мокапи — Cloud Disk</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#F4F4F4;
    --surface:#FFFFFF;
    --ink:#1B2320;
    --ink-soft:#5A6771;
    --ink-faint:#9AA3AD;
    --line:#E4E7EA;
    --brand:#437952;              /* deep forest green, primary */
    --brand-dark:#32603D;
    --brand-soft:#E7F2EB;
    --shadow:0 1px 2px rgba(16,24,32,.04),0 8px 24px rgba(16,24,32,.06);
    --radius:14px;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%}
  body{
    font-family:'Inter',system-ui,-apple-system,"Segoe UI",sans-serif;
    background:var(--bg);color:var(--ink);
    -webkit-font-smoothing:antialiased;
    font-size:14px;
  }

  /* ---------- Main ---------- */
  .main{padding:26px 34px 40px;min-width:0;max-width:1100px;margin:0 auto}
  .head{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:22px}
  .head h1{font-size:24px;font-weight:700;letter-spacing:-.02em;display:flex;align-items:center;gap:11px}
  .head h1 .h-icon{width:30px;height:30px;border-radius:9px;background:var(--brand-soft);color:var(--brand);display:grid;place-items:center;font-size:16px}
  .subhead{font-size:12.5px;color:var(--ink-faint);margin-top:5px;font-weight:500}

  .canvas{
    background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
    box-shadow:var(--shadow);overflow:hidden;
  }
  .toolbar{
    display:flex;align-items:center;gap:12px;padding:16px 18px;
    border-bottom:1px solid var(--line);flex-wrap:wrap;
  }
  .search{
    flex:1;min-width:220px;display:flex;align-items:center;gap:9px;
    background:var(--bg);border:1px solid var(--line);border-radius:9px;padding:9px 13px;
  }
  .search svg{width:15px;height:15px;stroke:var(--ink-faint);fill:none;stroke-width:2;stroke-linecap:round}
  .search input{border:none;background:none;outline:none;flex:1;font:inherit;font-size:13px;color:var(--ink)}
  .search input::placeholder{color:var(--ink-faint)}
  .count{font-size:12px;color:var(--ink-faint);font-weight:500;white-space:nowrap}

  .grid-head, .file-card{
    display:grid;grid-template-columns:44px 1fr auto;gap:14px;align-items:center;
  }
  .grid-head{
    padding:10px 18px;background:#FAFBFC;border-bottom:1px solid var(--line);
    font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--ink-faint);
  }
  .file-card{
    padding:14px 18px;text-decoration:none;color:inherit;border-bottom:1px solid var(--line);
    transition:background .12s;position:relative;
  }
  .file-card:last-child{border-bottom:none}
  .file-card:hover{background:#FAFBF9}
  .card-icon{
    width:44px;height:44px;border-radius:11px;background:var(--brand-soft);
    display:grid;place-items:center;font-size:21px;
  }
  .card-body{min-width:0}
  .card-top{display:flex;align-items:center;gap:10px;min-width:0}
  .card-name{font-weight:600;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .pill{
    flex-shrink:0;font-size:10.5px;font-weight:700;padding:3px 9px;border-radius:99px;letter-spacing:.02em;
  }
  .card-desc{font-size:12.5px;color:var(--ink-soft);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .card-meta{display:flex;align-items:center;gap:7px;margin-top:5px;font-size:11px;color:var(--ink-faint);font-weight:500}
  .meta-path{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10.5px}
  .dot{opacity:.6}
  .card-arrow{
    width:30px;height:30px;border-radius:50%;display:grid;place-items:center;
    background:var(--bg);color:var(--ink-soft);font-size:15px;transition:background .12s,color .12s;
  }
  .file-card:hover .card-arrow{background:var(--brand);color:#fff}

  .footer{
    display:flex;align-items:center;justify-content:space-between;padding:16px 18px;
    color:var(--ink-faint);font-size:12px;
  }
  .footer .total{font-weight:500}
  .pager{display:flex;gap:6px}
  .pg{width:30px;height:30px;border-radius:8px;display:grid;place-items:center;font-weight:600;font-size:12.5px}
  .pg.on{background:var(--brand);color:#fff}
  .pg.off{background:var(--bg);color:var(--ink-soft)}

  .empty{
    padding:60px 20px;text-align:center;color:var(--ink-faint);
  }
  .empty h3{font-size:15px;font-weight:600;color:var(--ink-soft);margin-bottom:4px}

  @media (max-width:820px){
    .main{padding:20px 16px}
  }
</style>
</head>
<body>
<main class="main">
    <div class="head">
      <div>
        <h1><span class="h-icon">&#9729;</span> Всі мокапи</h1>
        <div class="subhead">Автооновлення за скануванням теки · __NOW__</div>
      </div>
    </div>

    <div class="canvas">
      <div class="toolbar">
        <div class="search">
          <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          <input id="searchInput" type="text" placeholder="Пошук мокапів…" autocomplete="off">
        </div>
        <span class="count" id="countLabel">__TOTAL__ елементів</span>
      </div>

      <div class="grid-head">
        <span>Тип</span>
        <span>Назва / Опис</span>
        <span></span>
      </div>

      <div id="fileList">__CARDS__</div>

      <div class="footer">
        <span class="total" id="shownLabel">__TOTAL__ з __TOTAL__ показано</span>
        <div class="pager">
          <div class="pg off">&#8249;</div>
          <div class="pg on">1</div>
          <div class="pg off">&#8250;</div>
        </div>
      </div>
    </div>
  </main>

<script>
  var cards = Array.prototype.slice.call(document.querySelectorAll('#fileList .file-card'));
  var search = document.getElementById('searchInput');
  var countLabel = document.getElementById('countLabel');
  var shownLabel = document.getElementById('shownLabel');
  var list = document.getElementById('fileList');
  var emptyBox = document.createElement('div');
  emptyBox.className = 'empty';
  emptyBox.innerHTML = '<h3>Нічого не знайдено</h3><p>Спробуйте змінити запит.</p>';

  function applyFilter() {
    var q = search.value.trim().toLowerCase();
    var visible = 0;
    cards.forEach(function (c) {
      var hit = !q || c.textContent.toLowerCase().indexOf(q) !== -1;
      c.style.display = hit ? '' : 'none';
      if (hit) visible++;
    });
    countLabel.textContent = visible + ' елементів';
    shownLabel.textContent = visible + ' з ' + cards.length + ' показано';
    if (visible === 0 && !list.contains(emptyBox)) list.appendChild(emptyBox);
    else if (visible > 0 && list.contains(emptyBox)) list.removeChild(emptyBox);
  }
  search.addEventListener('input', applyFilter);
</script>
</body>
</html>
"""


def render(items, out_path):
    now = datetime.now().strftime("%Y-%m-%d")
    total = len(items)
    cards_html = _build_cards(items)
    html_doc = _TEMPLATE.replace("__CARDS__", cards_html)
    html_doc = html_doc.replace("__TOTAL__", str(total))
    html_doc = html_doc.replace("__NOW__", now)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html_doc)
    return total


def main():
    ap = argparse.ArgumentParser(description="Generate mockup cloud-disk index")
    ap.add_argument("--out", default=OUT_DEFAULT, help="output HTML path")
    ap.add_argument("--dry-run", action="store_true", help="print metadata only")
    args = ap.parse_args()

    items = scan_mockups()
    if items:
        newest = max(items, key=lambda it: _git_date(it["folder"], full=True))
        newest["new"] = True

    if args.dry_run:
        for it in items:
            print("{} {:<12} {} {}".format(
                it["date"] or "-", it["folder"], it["icon"], it["title"]))
        print("\n{} mockup(s) found in {}".format(len(items), MOCKUPS_DIR))
        return

    if not items:
        print("Error: no mockups found under {}".format(MOCKUPS_DIR), file=sys.stderr)
        sys.exit(1)

    n = render(items, args.out)
    print("\u2713 Generated {} with {} mockup(s)".format(args.out, n))


if __name__ == "__main__":
    main()
