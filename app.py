import os, sqlite3, subprocess, uuid, re
from datetime import datetime, date
from pathlib import Path
from flask import Flask, request, redirect, url_for, flash, render_template_string, send_from_directory, session
from automation import automation_bp, start_worker
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

APP_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv("DATA_DIR", APP_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "clips"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
DB = DATA_DIR / "agent.db"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-before-deploy")
app.register_blueprint(automation_bp)
start_worker()

PAGE = r"""
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClipPilot AI — Neon Studio</title>
<style>
:root{--bg:#070912;--panel:#101426;--panel2:#151b31;--line:#252d4b;--text:#f3f5ff;--muted:#929bb8;--cyan:#23e7ff;--blue:#5478ff;--violet:#a855f7;--green:#36e0b2;--pink:#ff4fd8;--shadow:0 0 26px rgba(35,231,255,.07),0 12px 38px rgba(0,0,0,.24)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(ellipse at 75% -10%,rgba(84,120,255,.17),transparent 36%),radial-gradient(ellipse at 8% 18%,rgba(168,85,247,.10),transparent 30%),var(--bg);color:var(--text);font:14px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Arial,sans-serif}
a{color:#8ceeff;text-decoration:none}a:hover{color:#fff}button,.btn{border:1px solid rgba(35,231,255,.42);background:linear-gradient(110deg,rgba(35,231,255,.16),rgba(84,120,255,.22));color:#eefdff;padding:10px 15px;border-radius:10px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:7px;box-shadow:0 0 18px rgba(35,231,255,.08);transition:.18s}button:hover,.btn:hover{transform:translateY(-1px);border-color:var(--cyan);box-shadow:0 0 22px rgba(35,231,255,.2)}input,select,textarea{width:100%;padding:11px 12px;border-radius:10px;border:1px solid #303956;background:#090e1d;color:#f5f7ff;margin:6px 0 13px;outline:none}input:focus,select:focus,textarea:focus{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(35,231,255,.09)}label{font-size:12px;font-weight:700;color:#b6c0df;letter-spacing:.03em}header{height:72px;position:sticky;top:0;z-index:5;display:flex;align-items:center;justify-content:space-between;padding:0 max(18px,calc((100% - 1440px)/2));background:rgba(7,9,18,.82);backdrop-filter:blur(18px);border-bottom:1px solid rgba(93,115,173,.22)}.brand{display:flex;align-items:center;gap:12px;font-size:18px;font-weight:850;letter-spacing:-.03em}.brandmark{width:36px;height:36px;border-radius:11px;display:grid;place-items:center;background:linear-gradient(135deg,var(--cyan),var(--blue),var(--violet));color:#070912;font-size:20px;box-shadow:0 0 24px rgba(35,231,255,.28)}.brand small{display:block;color:var(--muted);font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase}.topright{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:12px}.live-dot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 12px var(--green);display:inline-block}
.shell{max-width:1440px;margin:auto;padding:24px 18px 60px;display:grid;grid-template-columns:220px minmax(0,1fr);gap:22px}.sidebar{align-self:start;position:sticky;top:92px;background:rgba(16,20,38,.74);border:1px solid var(--line);border-radius:17px;padding:14px;box-shadow:var(--shadow)}.navlabel{color:#687392;font-size:10px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;padding:12px 10px 7px}.nav a{display:flex;align-items:center;gap:11px;padding:10px;border-radius:10px;color:#aeb8d6;margin:3px 0;font-size:13px}.nav a:hover,.nav a.active{background:linear-gradient(90deg,rgba(35,231,255,.12),rgba(84,120,255,.08));color:#f4fdff;border:1px solid rgba(35,231,255,.15)}.navicon{width:20px;text-align:center;color:var(--cyan);font-size:15px}.sidefoot{border-top:1px solid var(--line);margin-top:14px;padding:14px 8px 3px;color:var(--muted);font-size:11px}
main{min-width:0}.hero{display:flex;align-items:flex-end;justify-content:space-between;gap:15px;margin:3px 0 20px}.eyebrow{color:var(--cyan);font-size:10px;font-weight:850;letter-spacing:.18em;text-transform:uppercase}.hero h1{font-size:clamp(25px,4vw,36px);letter-spacing:-.045em;line-height:1.1;margin:7px 0}.hero p{color:var(--muted);margin:0}.hero-actions{display:flex;gap:9px;flex-wrap:wrap}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px}.metric{position:relative;overflow:hidden;background:linear-gradient(145deg,rgba(21,27,49,.95),rgba(12,16,31,.96));border:1px solid var(--line);border-radius:15px;padding:17px;box-shadow:var(--shadow)}.metric:after{content:"";position:absolute;width:90px;height:90px;border-radius:50%;right:-35px;top:-40px;background:var(--glow,rgba(35,231,255,.16));filter:blur(22px)}.metric small{color:var(--muted);font-size:11px}.metric strong{display:block;font-size:25px;letter-spacing:-.04em;margin-top:6px}.metric .micon{float:right;color:var(--accent,var(--cyan));font-size:18px}.section{margin-top:19px;scroll-margin-top:92px}.card{background:linear-gradient(145deg,rgba(17,22,41,.96),rgba(12,16,30,.96));border:1px solid var(--line);border-radius:16px;padding:19px;margin-bottom:15px;box-shadow:var(--shadow)}.cardhead{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:13px}.card h2{font-size:16px;letter-spacing:-.02em;margin:0}.card p{color:var(--muted)}.sub{color:var(--muted);font-size:12px;margin:5px 0 0}.tag{display:inline-flex;align-items:center;padding:4px 8px;border-radius:99px;background:rgba(35,231,255,.08);border:1px solid rgba(35,231,255,.18);color:#9cf5ff;font-size:10px;font-weight:800}.notice{background:rgba(255,184,77,.07);border:1px solid rgba(255,184,77,.26);padding:12px 14px;border-radius:11px;color:#e7d5ae;margin-bottom:15px;font-size:12px}.row{display:flex;gap:12px;flex-wrap:wrap}.row>*{flex:1;min-width:145px}.tablewrap{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:650px}td,th{text-align:left;padding:11px 9px;border-bottom:1px solid rgba(75,88,128,.28);vertical-align:top}th{color:#7f8aa9;font-size:10px;text-transform:uppercase;letter-spacing:.1em}td{font-size:12px;color:#dce3fa}small,.muted{color:var(--muted)}.pill{display:inline-block;padding:4px 8px;border-radius:99px;background:rgba(84,120,255,.13);border:1px solid rgba(84,120,255,.22);font-size:10px;color:#c3d0ff}.btn-secondary{background:rgba(255,255,255,.035);border-color:#343d5a;color:#c9d3ed;box-shadow:none}.btn-small{padding:7px 10px;font-size:11px}.two{display:grid;grid-template-columns:1fr 1fr;gap:15px}.empty{padding:22px;text-align:center;color:var(--muted);border:1px dashed #343d5a;border-radius:12px}.earn-total{font-size:30px;font-weight:850;letter-spacing:-.04em;color:#e9fbff}.status-approved{color:var(--green)}.status-pending{color:#ffd17c}.status-rejected{color:#ff7b9c}.flash{padding:10px 13px;border-radius:10px;background:rgba(54,224,178,.08);border:1px solid rgba(54,224,178,.22);margin-bottom:12px;color:#b9f9e7}
@media(max-width:1000px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.shell{grid-template-columns:190px minmax(0,1fr)}}@media(max-width:720px){header{height:62px}.topright .statusword{display:none}.shell{display:block;padding:16px 12px 45px}.sidebar{position:static;margin-bottom:17px;padding:8px;overflow-x:auto}.nav{display:flex;gap:4px;min-width:max-content}.navlabel,.sidefoot{display:none}.nav a{padding:9px 11px}.nav a span:last-child{white-space:nowrap}.hero{display:block}.hero-actions{margin-top:14px}.card{padding:15px}.two{grid-template-columns:1fr}.grid{gap:9px}.metric{padding:13px}.metric strong{font-size:21px}}
</style></head><body>
<header><div class="brand"><div class="brandmark">✂</div><div>ClipPilot AI<small>Creator campaign intelligence</small></div></div><div class="topright"><span class="live-dot"></span><span class="statusword">SYSTEM ONLINE · LOCAL MVP</span><span class="tag">NEON STUDIO</span></div></header>
<div class="shell"><aside class="sidebar"><div class="navlabel">Workspace</div><nav class="nav"><a class="active" href="#overview"><span class="navicon">◈</span><span>Overview</span></a><a href="#campaigns"><span class="navicon">⌕</span><span>Campaign Finder</span></a><a href="#clip-studio"><span class="navicon">▣</span><span>Clip Studio</span></a><a href="#my-clips"><span class="navicon">▶</span><span>My Clips</span></a><a href="#earnings"><span class="navicon">₹</span><span>My Earnings</span></a><a href="#connections"><span class="navicon">⌘</span><span>AI Connections</span></a></nav><div class="sidefoot">Built for creators<br><span style="color:#64718f">Campaigns · Clips · Insights</span></div></aside>
<main><section id="overview" class="hero"><div><div class="eyebrow">Creator command centre</div><h1>Make every moment <span style="background:linear-gradient(90deg,var(--cyan),#9b8cff,var(--pink));background-clip:text;color:transparent">count.</span></h1><p>Your campaign workspace, clip production and earnings in one place.</p></div><div class="hero-actions"><a class="btn" href="#campaigns">＋ Add campaign</a><a class="btn btn-secondary" href="#clip-studio">Create a clip ↗</a></div></section>
{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="flash">{{message}}</div>{% endfor %}{% endwith %}
<div class="notice"><b>Current capabilities:</b> manual campaign tracking, best-effort public directory scanning, FFmpeg vertical clipping and manually recorded earnings. AI moment detection, automatic creator discovery, live clipping and marketplace earnings verification still require integrations. Only process footage you own or are authorized to use.</div>
<div class="grid"><div class="metric" style="--accent:var(--cyan);--glow:rgba(35,231,255,.2)"><span class="micon">◈</span><small>Campaigns saved</small><strong>{{total}}</strong></div><div class="metric" style="--accent:var(--violet);--glow:rgba(168,85,247,.2)"><span class="micon">↗</span><small>Best saved rate</small><strong>{{best_rate}}</strong><small>per 1,000 eligible views</small></div><div class="metric" style="--accent:var(--pink);--glow:rgba(255,79,216,.16)"><span class="micon">▣</span><small>Clips created</small><strong>{{clips}}</strong></div><div class="metric" style="--accent:var(--green);--glow:rgba(54,224,178,.16)"><span class="micon">✓</span><small>Submissions tracked</small><strong>{{submitted}}</strong></div></div>
<section id="campaigns" class="section"><div class="card"><div class="cardhead"><div><div class="eyebrow">01 / Discover</div><h2>Campaign Finder</h2><p class="sub">Scan public campaign directories for visible listings.</p></div><span class="tag">PUBLIC SCAN</span></div><form method="post" action="/discover"><button type="submit">⌕ Scan public campaigns</button></form><div class="row" style="margin-top:12px"><a class="btn btn-secondary btn-small" href="https://contentrewards.com/c/discover" target="_blank" rel="noopener">Content Rewards ↗</a><a class="btn btn-secondary btn-small" href="https://clipping.net/c/discover" target="_blank" rel="noopener">CLIPPING ↗</a></div>{% if discovery_error %}<p class="notice" style="margin-top:12px">{{discovery_error}}</p>{% endif %}{% if discovered %}<h3 style="font-size:13px;margin-top:18px">Public results · {{discovered|length}}</h3><p class="sub">Verify eligibility, payment terms, deadlines and clipping rights on the campaign page.</p>{% for d in discovered %}<div style="border-top:1px solid var(--line);padding:12px 0"><b>{{d.name}}</b> <span class="pill">{{d.source}}</span>{% if d.pay %}<p style="margin:5px 0">{{d.pay}}</p>{% endif %}<small>{{d.detail}}</small><p style="margin:7px 0"><a href="{{d.url}}" target="_blank" rel="noopener">View campaign terms ↗</a></p></div>{% endfor %}{% endif %}</div>
<div class="two"><div class="card"><div class="eyebrow">02 / Track</div><h2>Add a campaign</h2><p class="sub">Save campaign details you have verified.</p><form method="post" action="/campaign"><label>Campaign / creator name</label><input name="name" required placeholder="Creator or campaign name"><label>Campaign URL</label><input name="url" type="url" placeholder="https://..."><div class="row"><div><label>Pay per 1,000 views (₹)</label><input name="rate" type="number" min="0" step="0.01" required></div><div><label>Maximum payout (₹)</label><input name="cap" type="number" min="0" step="0.01"></div></div><label>Deadline</label><input name="deadline" type="date"><label>Rules / notes</label><textarea name="notes" rows="3" placeholder="Eligibility, platforms, minimum views, rights..."></textarea><button type="submit">Save campaign</button></form></div>
<div class="card"><div class="eyebrow">03 / Compare</div><h2>Campaign ranking</h2><p class="sub">Transparent estimate based on saved rate, cap and deadline.</p>{% if campaigns %}<div class="tablewrap"><table><tr><th>Campaign</th><th>Rate / 1K</th><th>Score</th><th>Status</th></tr>{% for c in campaigns %}<tr><td><b>{{c.name}}</b><br><small>{{c.notes or ''}}</small>{% if c.url %}<br><a href="{{c.url}}" target="_blank" rel="noopener">Open ↗</a>{% endif %}</td><td>₹{{'%.2f'|format(c.rate)}}</td><td><span class="pill">{{c.score}}/100</span><br><form method="post" action="/automation/start/{{c.id}}" style="margin-top:7px"><button class="btn-small" type="submit">Start automatic discovery</button></form></td><td><form method="post" action="/status/{{c.id}}"><select name="status"><option {{'selected' if c.status=='research' else ''}}>research</option><option {{'selected' if c.status=='applied' else ''}}>applied</option><option {{'selected' if c.status=='accepted' else ''}}>accepted</option><option {{'selected' if c.status=='submitted' else ''}}>submitted</option><option {{'selected' if c.status=='paid' else ''}}>paid</option></select><button class="btn-small">Update</button></form></td></tr>{% endfor %}</table></div>{% else %}<div class="empty">No campaigns saved yet.</div>{% endif %}</div></div></section>
<section id="clip-studio" class="section"><div class="card"><div class="cardhead"><div><div class="eyebrow">04 / Produce</div><h2>Clip Studio</h2><p class="sub">Turn an authorized source video segment into a vertical 9:16 MP4.</p></div><span class="tag">FFMPEG</span></div><form method="post" action="/make-clip" enctype="multipart/form-data"><label>Upload source video</label><input type="file" name="video" accept="video/*" required><div class="row"><div><label>Start time · seconds</label><input type="number" name="start" min="0" step="0.1" value="0" required></div><div><label>Duration · seconds (max 180)</label><input type="number" name="duration" min="1" max="180" step="0.1" value="30" required></div></div><button type="submit">✦ Render vertical clip</button></form></div></section>
<section id="my-clips" class="section"><div class="card"><div class="eyebrow">05 / Library</div><h2>My Clips</h2><p class="sub">Download clips rendered by this app.</p>{% if clip_files %}{% for f in clip_files %}<div style="padding:9px 0;border-bottom:1px solid var(--line)"><span>▣ {{f}}</span><a style="float:right" href="/clips/{{f}}">Download ↓</a></div>{% endfor %}{% else %}<div class="empty">Your rendered clips will appear here.</div>{% endif %}</div></section>
<section id="earnings" class="section"><div class="card"><div class="cardhead"><div><div class="eyebrow">06 / Revenue tracking</div><h2>My Earnings</h2><p class="sub">Record amounts shown in your campaign account. These are not independently verified by ClipPilot.</p></div><span class="tag">PERSONAL TRACKER</span></div><div class="grid" style="grid-template-columns:repeat(4,minmax(0,1fr));margin-bottom:16px"><div class="metric"><small>Total recorded</small><strong>₹{{'%.2f'|format(earnings_total)}}</strong></div><div class="metric"><small>Approved</small><strong style="color:var(--green)">₹{{'%.2f'|format(earnings_approved)}}</strong></div><div class="metric"><small>Pending</small><strong style="color:#ffd17c">₹{{'%.2f'|format(earnings_pending)}}</strong></div><div class="metric"><small>Rejected</small><strong style="color:#ff7b9c">₹{{'%.2f'|format(earnings_rejected)}}</strong></div></div><div class="two"><form method="post" action="/earnings"><label>Campaign</label><select name="campaign_id" required>{% for c in campaigns %}<option value="{{c.id}}">{{c.name}}</option>{% endfor %}</select><label>Clip name</label><input name="clip_name" placeholder="Clip title" required><div class="row"><div><label>Views</label><input name="views" type="number" min="0" value="0"></div><div><label>Recorded earnings (₹)</label><input name="amount" type="number" min="0" step="0.01" required></div></div><label>Clip / submission URL</label><input name="clip_url" type="url" placeholder="https://..."><label>Status</label><select name="status"><option value="pending">pending</option><option value="approved">approved</option><option value="rejected">rejected</option></select><label>Notes</label><textarea name="notes" rows="2"></textarea><button type="submit">＋ Record earnings</button></form><div><h3 style="font-size:13px;margin-top:0">Earnings history</h3>{% if earnings %}<div class="tablewrap"><table><tr><th>Clip / campaign</th><th>Amount</th><th>Status</th></tr>{% for e in earnings %}<tr><td><b>{{e.clip_name}}</b><br><small>{{e.campaign_name}} · {{e.views}} views</small>{% if e.clip_url %}<br><a href="{{e.clip_url}}" target="_blank" rel="noopener">Open clip ↗</a>{% endif %}</td><td>₹{{'%.2f'|format(e.amount)}}</td><td><form method="post" action="/earnings/{{e.id}}"><select name="status"><option value="pending" {{'selected' if e.status=='pending' else ''}}>pending</option><option value="approved" {{'selected' if e.status=='approved' else ''}}>approved</option><option value="rejected" {{'selected' if e.status=='rejected' else ''}}>rejected</option></select><button class="btn-small">Save</button></form></td></tr>{% endfor %}</table></div>{% else %}<div class="empty">No earnings recorded yet.</div>{% endif %}</div></div></div></section>
<section id="connections" class="section"><div class="card"><div class="eyebrow">07 / Integrations</div><h2>AI Connections</h2><p class="sub">Provider connections are not configured in this build. When added, use server-side API keys and never expose secrets in browser code.</p><div class="row"><span class="pill">ChatGPT · Not connected</span><span class="pill">Gemini · Not connected</span><span class="pill">Claude · Not connected</span></div><p class="sub" style="margin-top:14px">No wallet or payment processing is included. Campaign payments remain on the campaign platform.</p></div></section>
</main></div></body></html>

"""

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS campaigns(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, url TEXT,
        rate REAL NOT NULL, cap REAL, deadline TEXT, notes TEXT,
        status TEXT DEFAULT 'research', created TEXT NOT NULL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS earnings(
        id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id INTEGER NOT NULL,
        clip_name TEXT NOT NULL, clip_url TEXT, views INTEGER DEFAULT 0,
        amount REAL NOT NULL, status TEXT DEFAULT 'pending', notes TEXT,
        created TEXT NOT NULL, FOREIGN KEY(campaign_id) REFERENCES campaigns(id))""")
    con.commit()
    return con

def score_campaign(row):
    # Transparent baseline score: rate is primary; cap and deadline add small modifiers.
    rate = max(0, float(row["rate"] or 0))
    score = min(75, rate / 20 * 75)
    if row["cap"] and float(row["cap"]) >= 5000: score += 10
    if row["deadline"]:
        try:
            days = (date.fromisoformat(row["deadline"]) - date.today()).days
            score += 10 if 2 <= days <= 21 else (3 if days > 21 else -15)
        except ValueError: pass
    return max(0, min(100, round(score)))

@app.route("/")
def home():
    con = db()
    rows = con.execute("SELECT * FROM campaigns").fetchall()
    campaigns = []
    for r in rows:
        item = dict(r); item["score"] = score_campaign(r); campaigns.append(item)
    campaigns.sort(key=lambda x: x["score"], reverse=True)
    files = sorted([p.name for p in OUTPUT_DIR.glob("*.mp4")], reverse=True)
    best = max([float(r["rate"]) for r in rows], default=0)
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in ["submitted","paid"]}
    earnings_rows = con.execute("""SELECT e.*, c.name AS campaign_name FROM earnings e
        LEFT JOIN campaigns c ON c.id=e.campaign_id ORDER BY e.id DESC LIMIT 100""").fetchall()
    totals = con.execute("SELECT status, COALESCE(SUM(amount),0) AS amount FROM earnings GROUP BY status").fetchall()
    amounts = {r["status"]: float(r["amount"] or 0) for r in totals}
    earnings_total = sum(amounts.values())
    con.close()
    return render_template_string(PAGE, total=len(rows), best_rate=f"₹{best:.2f}", clips=len(files),
        submitted=counts["submitted"]+counts["paid"], campaigns=campaigns, clip_files=files,
        earnings=[dict(e) for e in earnings_rows], earnings_total=earnings_total,
        earnings_approved=amounts.get("approved",0), earnings_pending=amounts.get("pending",0),
        earnings_rejected=amounts.get("rejected",0),
        discovered=session.get("discovered_campaigns", []), discovery_error=session.pop("discovery_error", None))


DISCOVERY_SOURCES = [
    ("CLIPPING", "https://clipping.net/c/discover"),
    ("Content Rewards", "https://contentrewards.com/c/discover"),
]

def _clean_text(value):
    return " ".join((value or "").split())

def _extract_public_campaigns(source_name, page_url, html):
    """Extract visible campaign cards/links from a public directory page."""
    soup = BeautifulSoup(html, "html.parser")
    found = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(page_url, a["href"])
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc not in {"clipping.net", "www.clipping.net", "contentrewards.com", "www.contentrewards.com"}:
            continue

        anchor_text = _clean_text(a.get_text(" ", strip=True))
        parent = a
        # Campaign cards generally wrap the title and pay details in a nearby card.
        for _ in range(4):
            if parent.parent:
                parent = parent.parent
            text = _clean_text(parent.get_text(" ", strip=True))
            if len(text) > len(anchor_text) + 25:
                break
        else:
            text = anchor_text

        path = parsed.path.lower()
        looks_like_campaign = (
            "campaign" in (anchor_text + " " + text).lower()
            or (source_name == "CLIPPING" and path.startswith("/c/") and path != "/c/discover")
            or (source_name == "Content Rewards" and path.startswith("/c/") and path != "/c/discover")
        )
        if not looks_like_campaign:
            continue

        # Avoid navigation links and generic category pages.
        if not anchor_text and len(text) < 20:
            continue
        title = anchor_text
        title = re.sub(r"\s+", " ", title).strip()
        if not title or title.lower() in {"discover", "view all", "see all", "campaigns"}:
            continue

        # Keep the pay/terms excerpt short and avoid duplicating the title.
        excerpt = text.replace(anchor_text, " ", 1).strip() if anchor_text else text
        excerpt = _clean_text(excerpt)
        pay_match = re.search(
            r"(?i)(?:pays?\s*)?((?:\$|€|£)\s?[\d,.]+(?:\s*(?:to|–|-|—)\s*(?:\$|€|£)?\s?[\d,.]+)?\s*(?:/\s*(?:100K|1K|1M)|per\s*1M|in\s*pools)?|\$[\d,.]+\s*(?:pool|budget))",
            text
        )
        pay = pay_match.group(0) if pay_match else ""
        # A stable key avoids duplicate cards from repeated page sections.
        key = (source_name, href)
        if key in seen:
            continue
        seen.add(key)
        found.append({
            "source": source_name,
            "name": title[:100],
            "url": href,
            "pay": pay[:100],
            "detail": excerpt[:120],
        })
    return found

@app.post("/discover")
def discover_campaigns():
    results = []
    errors = []
    headers = {"User-Agent": "ClipPilotAI/1.0 (public campaign directory discovery; contact: site owner)"}
    for source_name, page_url in DISCOVERY_SOURCES:
        try:
            response = requests.get(page_url, headers=headers, timeout=12)
            response.raise_for_status()
            if len(response.content) > 5_000_000:
                errors.append(f"{source_name}: response too large; skipped.")
                continue
            results.extend(_extract_public_campaigns(source_name, page_url, response.text))
        except requests.RequestException as exc:
            errors.append(f"{source_name}: could not load public directory ({type(exc).__name__}).")
    # Keep results bounded and stable for mobile.
    session["discovered_campaigns"] = results[:8]
    if not results:
        session["discovery_error"] = (
            "No campaign cards could be read right now. The sites may have changed their public page layout or blocked automated requests. "
            + "Use the official directory links above; no login or access controls were bypassed."
        )
    elif errors:
        session["discovery_error"] = "Some sources could not be scanned: " + " ".join(errors)
    return redirect(url_for("home"))

@app.post("/campaign")
def add_campaign():
    f = request.form
    try:
        rate = float(f.get("rate", 0)); cap = float(f["cap"]) if f.get("cap") else None
        if rate < 0 or (cap is not None and cap < 0): raise ValueError()
    except ValueError:
        flash("Enter valid non-negative amounts."); return redirect(url_for("home"))
    con = db()
    con.execute("INSERT INTO campaigns(name,url,rate,cap,deadline,notes,status,created) VALUES(?,?,?,?,?,?,?,?)",
        (f["name"].strip(), f.get("url","").strip(), rate, cap, f.get("deadline") or None,
         f.get("notes","").strip(), "research", datetime.utcnow().isoformat()))
    con.commit(); con.close()
    return redirect(url_for("home"))

@app.post("/status/<int:cid>")
def update_status(cid):
    status = request.form.get("status","research")
    if status not in {"research","applied","accepted","submitted","paid"}: return "Invalid status", 400
    con = db(); con.execute("UPDATE campaigns SET status=? WHERE id=?", (status,cid)); con.commit(); con.close()
    return redirect(url_for("home"))


@app.post("/earnings")
def add_earning():
    f = request.form
    try:
        campaign_id = int(f.get("campaign_id", ""))
        views = max(0, int(f.get("views", 0)))
        amount = float(f.get("amount", 0))
        if amount < 0: raise ValueError()
    except (ValueError, TypeError):
        flash("Enter a valid campaign, view count and non-negative earnings amount.")
        return redirect(url_for("home") + "#earnings")
    status = f.get("status", "pending")
    if status not in {"pending", "approved", "rejected"}:
        return "Invalid status", 400
    con = db()
    exists = con.execute("SELECT id FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
    if not exists:
        con.close(); flash("Select a saved campaign first.")
        return redirect(url_for("home") + "#earnings")
    con.execute("""INSERT INTO earnings(campaign_id,clip_name,clip_url,views,amount,status,notes,created)
        VALUES(?,?,?,?,?,?,?,?)""", (campaign_id, f.get("clip_name", "").strip(),
        f.get("clip_url", "").strip(), views, amount, status, f.get("notes", "").strip(),
        datetime.utcnow().isoformat()))
    con.commit(); con.close()
    return redirect(url_for("home") + "#earnings")

@app.post("/earnings/<int:eid>")
def update_earning(eid):
    status = request.form.get("status", "pending")
    if status not in {"pending", "approved", "rejected"}:
        return "Invalid status", 400
    con = db(); con.execute("UPDATE earnings SET status=? WHERE id=?", (status, eid)); con.commit(); con.close()
    return redirect(url_for("home") + "#earnings")

@app.post("/make-clip")
def make_clip():
    f = request.files.get("video")
    try:
        start = float(request.form.get("start",0)); duration = float(request.form.get("duration",30))
        if start < 0 or duration <= 0 or duration > 180: raise ValueError()
    except ValueError:
        flash("Invalid clip timing."); return redirect(url_for("home"))
    if not f or not f.filename: return "Video file required", 400
    ext = Path(f.filename).suffix.lower()
    if ext not in {".mp4",".mov",".mkv",".webm",".m4v"}: return "Unsupported video format", 400
    token = uuid.uuid4().hex[:10]
    src = UPLOAD_DIR / f"{token}{ext}"
    out = OUTPUT_DIR / f"clip_{token}.mp4"
    f.save(src)
    cmd = ["ffmpeg","-y","-ss",str(start),"-i",str(src),"-t",str(duration),
           "-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
           "-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-b:a","128k","-movflags","+faststart",str(out)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=240)
    except FileNotFoundError:
        return "FFmpeg is not installed. Deploy with the included Dockerfile.", 500
    except subprocess.CalledProcessError as e:
        return "Clip processing failed: " + e.stderr.decode(errors="ignore")[-1200:], 500
    finally:
        try: src.unlink()
        except OSError: pass
    return redirect(url_for("home"))

@app.route("/clips/<path:filename>")
def clips(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.get("/health")
def health(): return {"ok": True, "app": "ClipPilot AI"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","5000")))
