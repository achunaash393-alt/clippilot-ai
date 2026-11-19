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
<title>ClipPilot AI — Creator Studio</title>
<style>
:root{--bg:#070912;--panel:#101426;--panel2:#151b31;--line:#252d4b;--text:#f3f5ff;--muted:#929bb8;--cyan:#23e7ff;--blue:#5478ff;--violet:#a855f7;--green:#36e0b2;--pink:#ff4fd8;--shadow:0 0 26px rgba(35,231,255,.07),0 12px 38px rgba(0,0,0,.24)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(ellipse at 75% -10%,rgba(84,120,255,.17),transparent 36%),radial-gradient(ellipse at 8% 18%,rgba(168,85,247,.10),transparent 30%),var(--bg);color:var(--text);font:14px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Arial,sans-serif}
a{color:#8ceeff;text-decoration:none}a:hover{color:#fff}button,.btn{border:1px solid rgba(35,231,255,.42);background:linear-gradient(110deg,rgba(35,231,255,.16),rgba(84,120,255,.22));color:#eefdff;padding:10px 15px;border-radius:10px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:7px;box-shadow:0 0 18px rgba(35,231,255,.08);transition:.18s}button:hover,.btn:hover{transform:translateY(-1px);border-color:var(--cyan);box-shadow:0 0 22px rgba(35,231,255,.2)}input,select,textarea{width:100%;padding:11px 12px;border-radius:10px;border:1px solid #303956;background:#090e1d;color:#f5f7ff;margin:6px 0 13px;outline:none}input:focus,select:focus,textarea:focus{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(35,231,255,.09)}label{font-size:12px;font-weight:700;color:#b6c0df;letter-spacing:.03em}header{height:72px;position:sticky;top:0;z-index:5;display:flex;align-items:center;justify-content:space-between;padding:0 max(18px,calc((100% - 1440px)/2));background:rgba(7,9,18,.82);backdrop-filter:blur(18px);border-bottom:1px solid rgba(93,115,173,.22)}.brand{display:flex;align-items:center;gap:12px;font-size:18px;font-weight:850;letter-spacing:-.03em}.brandmark{width:36px;height:36px;border-radius:11px;display:grid;place-items:center;background:linear-gradient(135deg,var(--cyan),var(--blue),var(--violet));color:#070912;font-size:20px;box-shadow:0 0 24px rgba(35,231,255,.28)}.brand small{display:block;color:var(--muted);font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase}.topright{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:12px}.live-dot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 12px var(--green);display:inline-block}
.shell{max-width:1440px;margin:auto;padding:24px 18px 60px;display:grid;grid-template-columns:220px minmax(0,1fr);gap:22px}.sidebar{align-self:start;position:sticky;top:92px;background:rgba(16,20,38,.74);border:1px solid var(--line);border-radius:17px;padding:14px;box-shadow:var(--shadow)}.navlabel{color:#687392;font-size:10px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;padding:12px 10px 7px}.nav a{display:flex;align-items:center;gap:11px;padding:10px;border-radius:10px;color:#aeb8d6;margin:3px 0;font-size:13px}.nav a:hover,.nav a.active{background:linear-gradient(90deg,rgba(35,231,255,.12),rgba(84,120,255,.08));color:#f4fdff;border:1px solid rgba(35,231,255,.15)}.navicon{width:20px;text-align:center;color:var(--cyan);font-size:15px}.sidefoot{border-top:1px solid var(--line);margin-top:14px;padding:14px 8px 3px;color:var(--muted);font-size:11px}
main{min-width:0}.hero{display:flex;align-items:flex-end;justify-content:space-between;gap:15px;margin:3px 0 20px}.eyebrow{color:var(--cyan);font-size:10px;font-weight:850;letter-spacing:.18em;text-transform:uppercase}.hero h1{font-size:clamp(25px,4vw,36px);letter-spacing:-.045em;line-height:1.1;margin:7px 0}.hero p{color:var(--muted);margin:0}
.hero-actions{display:flex;gap:9px;flex-wrap:wrap}
.hero-visual{width:190px;height:150px;flex:0 0 190px;display:grid;place-items:center;perspective:700px;isolation:isolate}
.clip-core{width:104px;height:104px;position:relative;transform-style:preserve-3d;animation:core-float 5s ease-in-out infinite}
.core-face{position:absolute;inset:10px;border:1px solid #6f9fc4;border-radius:18px;background:linear-gradient(145deg,#294b68,#172635);display:grid;place-items:center;color:#e9f5ff;font-size:34px;box-shadow:inset 0 0 24px #5c91b733}
.core-face.front{transform:translateZ(24px)}
.core-face.back{transform:rotateY(180deg) translateZ(24px)}
.core-face.left{transform:rotateY(-90deg) translateZ(24px)}
.core-face.right{transform:rotateY(90deg) translateZ(24px)}
.core-ring{position:absolute;inset:-17px;border:1px solid #6e9fc566;border-radius:50%;transform:rotateX(68deg) rotateZ(-18deg);animation:ring-turn 12s linear infinite}
.core-ring.ring-two{inset:-28px;transform:rotateY(68deg) rotateZ(24deg);border-color:#8b7bd866;animation-direction:reverse;animation-duration:17s}
.core-dot{position:absolute;width:9px;height:9px;border-radius:50%;background:#8fc5ee;top:4px;right:22px;box-shadow:0 0 0 5px #8fc5ee20}
@keyframes core-float{0%,100%{transform:rotateX(-12deg) rotateY(-20deg) translateY(0)}50%{transform:rotateX(10deg) rotateY(22deg) translateY(-9px)}}
@keyframes ring-turn{to{transform:rotateX(68deg) rotateZ(342deg)}}
@media(max-width:900px){.hero-visual{width:130px;flex-basis:130px;height:125px}.clip-core{transform:scale(.82)}}
@media(max-width:720px){.hero-visual{display:none}}
@media(prefers-reduced-motion:reduce){.clip-core,.core-ring{animation:none}}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px}.metric{position:relative;overflow:hidden;background:linear-gradient(145deg,rgba(21,27,49,.95),rgba(12,16,31,.96));border:1px solid var(--line);border-radius:15px;padding:17px;box-shadow:var(--shadow)}.metric:after{content:"";position:absolute;width:90px;height:90px;border-radius:50%;right:-35px;top:-40px;background:var(--glow,rgba(35,231,255,.16));filter:blur(22px)}.metric small{color:var(--muted);font-size:11px}.metric strong{display:block;font-size:25px;letter-spacing:-.04em;margin-top:6px}.metric .micon{float:right;color:var(--accent,var(--cyan));font-size:18px}.section{margin-top:19px;scroll-margin-top:92px}.card{background:linear-gradient(145deg,rgba(17,22,41,.96),rgba(12,16,30,.96));border:1px solid var(--line);border-radius:16px;padding:19px;margin-bottom:15px;box-shadow:var(--shadow)}.cardhead{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:13px}.card h2{font-size:16px;letter-spacing:-.02em;margin:0}.card p{color:var(--muted)}.sub{color:var(--muted);font-size:12px;margin:5px 0 0}.tag{display:inline-flex;align-items:center;padding:4px 8px;border-radius:99px;background:rgba(35,231,255,.08);border:1px solid rgba(35,231,255,.18);color:#9cf5ff;font-size:10px;font-weight:800}.notice{background:rgba(255,184,77,.07);border:1px solid rgba(255,184,77,.26);padding:12px 14px;border-radius:11px;color:#e7d5ae;margin-bottom:15px;font-size:12px}.row{display:flex;gap:12px;flex-wrap:wrap}.row>*{flex:1;min-width:145px}.tablewrap{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:650px}td,th{text-align:left;padding:11px 9px;border-bottom:1px solid rgba(75,88,128,.28);vertical-align:top}th{color:#7f8aa9;font-size:10px;text-transform:uppercase;letter-spacing:.1em}td{font-size:12px;color:#dce3fa}small,.muted{color:var(--muted)}.pill{display:inline-block;padding:4px 8px;border-radius:99px;background:rgba(84,120,255,.13);border:1px solid rgba(84,120,255,.22);font-size:10px;color:#c3d0ff}.btn-secondary{background:rgba(255,255,255,.035);border-color:#343d5a;color:#c9d3ed;box-shadow:none}.btn-small{padding:7px 10px;font-size:11px}.two{display:grid;grid-template-columns:1fr 1fr;gap:15px}.empty{padding:22px;text-align:center;color:var(--muted);border:1px dashed #343d5a;border-radius:12px}.earn-total{font-size:30px;font-weight:850;letter-spacing:-.04em;color:#e9fbff}.status-approved{color:var(--green)}.status-pending{color:#ffd17c}.status-rejected{color:#ff7b9c}.flash{padding:10px 13px;border-radius:10px;background:rgba(54,224,178,.08);border:1px solid rgba(54,224,178,.22);margin-bottom:12px;color:#b9f9e7}
@media(max-width:1000px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.shell{grid-template-columns:190px minmax(0,1fr)}}@media(max-width:720px){header{height:62px}.topright .statusword{display:none}.shell{display:block;padding:16px 12px 45px}.sidebar{position:static;margin-bottom:17px;padding:8px;overflow-x:auto}.nav{display:flex;gap:4px;min-width:max-content}.navlabel,.sidefoot{display:none}.nav a{padding:9px 11px}.nav a span:last-child{white-space:nowrap}.hero{display:block}.hero-actions{margin-top:14px}.card{padding:15px}.two{grid-template-columns:1fr}.grid{gap:9px}.metric{padding:13px}.metric strong{font-size:21px}}


.campaign-result{padding:15px 0;border-top:1px solid var(--line)}
.campaign-result-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap}
.campaign-facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin:12px 0}
.campaign-facts>div{background:#111a24;border:1px solid var(--line);border-radius:9px;padding:10px}
.campaign-facts small,.campaign-facts b{display:block}
.campaign-facts small{font-size:10px;margin-bottom:4px}
.campaign-facts b{font-size:12px;font-weight:650}
.download-ready{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:14px;background:#172d27;border:1px solid #315b4b;border-radius:10px;margin:12px 0}
.download-ready b{display:block;color:#d4f3e4}
@media(max-width:520px){.campaign-facts{grid-template-columns:1fr 1fr}.campaign-result-head{display:block}.campaign-result-head .pill{margin-top:8px}}

/* Clean, organized interface — flat surfaces, no glow */
:root{--bg:#0d1118;--panel:#151c26;--panel2:#1b2532;--line:#2a3544;--text:#edf2f7;--muted:#9aa8b8;--cyan:#63b3ed;--blue:#4f83cc;--violet:#8b7bd8;--green:#55b98b;--pink:#d77aa8;--shadow:none}
body{background:var(--bg)}
header{background:#111821;backdrop-filter:none;border-bottom:1px solid var(--line)}
.brandmark{background:#24384b;color:#b9dcf5;box-shadow:none}
.live-dot{box-shadow:none}
.sidebar{background:var(--panel);box-shadow:none}
.nav a:hover,.nav a.active{background:#202d3b;color:#f3f7fb;border:1px solid #34485b}
.navicon{color:#8bbce3}
.hero .eyebrow,.eyebrow{color:#8bbce3}
.hero h1 span{background:none!important;color:var(--text)!important}
.metric,.card{background:var(--panel);box-shadow:none;border:1px solid var(--line)}
.metric:after{display:none}
button,.btn{background:#294b68;border:1px solid #3b6688;color:#f4f8fc;box-shadow:none;transition:background .15s,border-color .15s}
button:hover,.btn:hover{transform:none;background:#345d80;border-color:#6e9fc5;box-shadow:none}
.btn-secondary{background:#202a36;border-color:#3a4655;color:#d4deea}
input:focus,select:focus,textarea:focus{border-color:#6e9fc5;box-shadow:none}
.tag{background:#202d3a;border:1px solid #3b4d60;color:#c4d8e9}
.pill{background:#202d3a;border:1px solid #3b4d60;color:#c4d8e9}
.flash{background:#172d27;border:1px solid #315b4b;color:#c3ead8}
.section{margin-top:22px}
.card{padding:20px}
.cardhead{align-items:center}
.card h2{font-size:17px}
.grid{gap:14px}
.metric{min-height:100px}
.metric strong{font-size:26px}
.two{align-items:start}
form{min-width:0}
table{min-width:580px}
a{color:#8fc5ee}
a:hover{color:#c5e4fb}
@media(max-width:720px){
 .card{padding:15px}
 .section{margin-top:16px}
 .metric{min-height:88px}
 .grid{grid-template-columns:repeat(2,minmax(0,1fr))}
 .hero h1{font-size:29px}
 .topright .tag{display:none}
}


/* Restrained 3D interaction layer */
.btn,button{transform:translateZ(0);transform-style:preserve-3d;transition:transform .18s ease,background .18s ease,border-color .18s ease}
.btn:active,button:active{transform:translateY(2px) scale(.985)}
.metric,.campaign-result,.download-ready{transition:transform .2s ease,border-color .2s ease}
.metric:hover{transform:perspective(700px) rotateX(1.5deg) translateY(-2px);border-color:#49647b}
.studio-stage{display:grid;grid-template-columns:170px minmax(0,1fr);gap:18px;align-items:center;padding:17px;margin:0 0 17px;background:#111a24;border:1px solid #2a3b4c;border-radius:13px;perspective:850px}
.studio-object{height:142px;display:grid;place-items:center;position:relative;transform-style:preserve-3d}
.studio-frame{width:88px;height:116px;border:1px solid #6e9fc5;border-radius:13px;background:linear-gradient(145deg,#294b68,#172635);transform:rotateY(-18deg) rotateX(7deg);box-shadow:12px 12px 0 #0b121b,13px 13px 0 1px #38566d;display:grid;place-items:center;animation:studio-hover 5s ease-in-out infinite}
.studio-frame-inner{width:64px;height:88px;border:1px solid #8ab5d2;border-radius:7px;background:linear-gradient(160deg,#213b50,#101b27);display:grid;place-items:center;color:#b9dcf5;font-size:28px}
.studio-orbit{position:absolute;width:140px;height:45px;border:1px solid #6489a766;border-radius:50%;transform:rotate(-24deg)}
.studio-copy b{display:block;font-size:13px;margin-bottom:5px}.studio-copy p{font-size:12px;color:#9aa8b8;margin:0}
.studio-chips{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}.studio-chips span{font-size:10px;color:#c4d8e9;background:#202d3a;border:1px solid #3b4d60;border-radius:20px;padding:4px 8px}
@keyframes studio-hover{0%,100%{transform:rotateY(-18deg) rotateX(7deg) translateY(0)}50%{transform:rotateY(12deg) rotateX(-3deg) translateY(-5px)}}
@media(max-width:600px){.studio-stage{grid-template-columns:95px minmax(0,1fr);gap:10px;padding:12px}.studio-object{height:112px}.studio-frame{transform:scale(.78) rotateY(-18deg)}}
@media(prefers-reduced-motion:reduce){.studio-frame{animation:none}.btn,button,.metric{transition:none}}


/* ClipPilot UI refresh v2 — editorial dashboard, consistent spacing, accessible controls */
:root{--bg:#0b1016;--panel:#121a23;--panel2:#182330;--line:#293746;--text:#edf3f8;--muted:#9aaaba;--cyan:#8fc5ee;--blue:#4e82ae;--shadow:none}
body{background:#0b1016;color:var(--text);letter-spacing:.005em}
header{height:66px;padding-left:max(20px,calc((100% - 1360px)/2));padding-right:max(20px,calc((100% - 1360px)/2));background:#0e151d;border-bottom:1px solid #263442}
.brand{font-size:16px;gap:10px}.brandmark{width:34px;height:34px;border-radius:9px;background:#24435c;color:#e6f4ff;font-size:18px}
.brand small{letter-spacing:.1em;font-size:9px}.topright{font-size:10px;letter-spacing:.07em}
.shell{max-width:1360px;grid-template-columns:205px minmax(0,1fr);gap:25px;padding-top:25px}
.sidebar{background:#101821;border:1px solid #263442;border-radius:12px;padding:11px;top:83px}
.navlabel{padding:11px 10px 8px;color:#718397;font-size:9px;letter-spacing:.14em}
.nav a{padding:10px 11px;border-radius:8px;color:#aebdca;font-size:12px;border:1px solid transparent}
.nav a.active{background:#1b2b39;border:1px solid #30485d;color:#f1f7fb}
.navicon{color:#8fc5ee;font-size:14px}
.sidefoot{border-color:#293746;color:#a1b1c0}
.hero{align-items:center;padding:24px 25px;margin:0 0 17px;background:#121c26;border:1px solid #293746;border-radius:13px;min-height:175px}
.hero h1{font-size:clamp(27px,3.4vw,38px);font-weight:720;letter-spacing:-.05em}
.hero p{font-size:13px;color:#a8b6c3}
.hero .eyebrow,.eyebrow{color:#91c6eb;letter-spacing:.14em;font-size:9px}
.hero-visual{margin:0 8px}
.hero-actions{gap:8px}
.grid{gap:11px}
.metric{background:#121a23;border:1px solid #293746;border-radius:11px;padding:15px;min-height:92px}
.metric strong{font-size:24px;font-weight:700}.metric small{font-size:10px;color:#9aabba}
.card{background:#121a23;border:1px solid #293746;border-radius:12px;padding:19px;margin-bottom:12px}
.card h2{font-size:16px;font-weight:680;letter-spacing:-.02em}
.cardhead{margin-bottom:15px}
.sub,.card p{color:#9aabba}
.tag,.pill{background:#1b2b39;border:1px solid #344b5f;color:#c4dced;border-radius:6px;font-weight:600}
button,.btn{background:#285273;border:1px solid #47789c;border-radius:8px;padding:10px 14px;color:#f4f9fc;font-size:12px;font-weight:650;box-shadow:none}
button:hover,.btn:hover{background:#326487;border-color:#6d9fc2;transform:translateY(-1px);box-shadow:none}
.btn-secondary{background:#1a2631;border-color:#344554;color:#d4e0e9}
.btn-secondary:hover{background:#233443}
input,select,textarea{background:#0d151d;border:1px solid #30404e;border-radius:8px;color:#edf3f8;padding:11px 12px;font-size:13px}
input:focus,select:focus,textarea:focus{border-color:#7fb4dc;box-shadow:0 0 0 2px #7fb4dc20}
label{color:#b8c7d3;font-size:11px;letter-spacing:.01em}
.notice{background:#241f16;border:1px solid #574a32;color:#e3d4b8;border-radius:9px}
.flash{border-radius:9px}
.campaign-result{padding:17px 0}
.campaign-facts>div{background:#0f1821;border:1px solid #293746;border-radius:8px}
.download-ready{background:#14271f;border:1px solid #315743;border-radius:9px}
.studio-stage{background:#0f1821;border-color:#293746;border-radius:11px}
.tablewrap{border:1px solid #293746;border-radius:9px}
table{min-width:560px}
td,th{border-bottom:1px solid #293746;padding:12px 10px}
th{color:#8296a8;font-size:9px;letter-spacing:.12em}
td{font-size:12px}
.empty{border-color:#344554;color:#9aabba}
.section{margin-top:17px;scroll-margin-top:82px}
@media(max-width:900px){.shell{grid-template-columns:180px minmax(0,1fr);gap:15px}.hero{padding:20px}}
@media(max-width:720px){
 header{height:60px;padding:0 13px}
 .shell{display:block;padding:12px 11px 38px}
 .sidebar{position:static;margin:0 0 13px;padding:6px;border-radius:9px;overflow-x:auto}
 .nav{display:flex;gap:4px;min-width:max-content}
 .nav a{padding:8px 10px;font-size:11px;margin:0}
 .hero{display:flex;align-items:center;padding:17px;min-height:0}
 .hero-visual{display:grid;width:88px;height:90px;flex:0 0 88px}
 .clip-core{transform:scale(.62)}
 .hero h1{font-size:26px}
 .hero-actions{margin-top:11px}
 .grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
 .metric{min-height:82px;padding:11px}
 .metric strong{font-size:21px}
 .card{padding:14px}
 .two{grid-template-columns:1fr}
 .studio-stage{grid-template-columns:90px minmax(0,1fr)}
 .studio-object{height:105px}
 .campaign-facts{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:390px){.hero-visual{display:none}.hero h1{font-size:25px}.topright .statusword{display:none}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}


/* ClipPilot typography + text motion v1 */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
body{font-family:'DM Sans','Avenir Next','Segoe UI',sans-serif;font-feature-settings:'ss01' on}
h1,h2,h3,.brand,.metric strong,.earn-total{font-family:'Space Grotesk','DM Sans',sans-serif;letter-spacing:-.035em}
.hero .eyebrow{animation:text-rise .55s both}
.hero h1{animation:text-rise .7s .06s both}
.hero p{animation:text-rise .7s .13s both}
.cardhead h2,.metric small{animation:text-soft-in .55s both}
.metric strong{animation:number-pop .55s .08s both}
.nav a{transition:background .18s ease,color .18s ease,transform .18s ease}
.nav a:hover{transform:translateX(2px)}
@keyframes text-rise{from{opacity:0;transform:translateY(9px);filter:blur(2px)}to{opacity:1;transform:translateY(0);filter:blur(0)}}
@keyframes text-soft-in{from{opacity:0}to{opacity:1}}
@keyframes number-pop{from{opacity:.35;transform:translateY(5px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
@media(prefers-reduced-motion:reduce){.hero .eyebrow,.hero h1,.hero p,.cardhead h2,.metric small,.metric strong{animation:none!important}.nav a{transition:none!important}}

</style></head><body>
<header><div class="brand"><div class="brandmark">✂</div><div>ClipPilot AI<small>Creator campaign intelligence</small></div></div><div class="topright"><span class="live-dot"></span><span class="statusword">SYSTEM ONLINE · LOCAL MVP</span><span class="tag">CREATOR STUDIO</span></div></header>
<div class="shell"><aside class="sidebar"><div class="navlabel">Workspace</div><nav class="nav"><a class="active" href="#overview"><span class="navicon">◈</span><span>Overview</span></a><a href="#campaigns"><span class="navicon">⌕</span><span>Campaign Finder</span></a><a href="#clip-studio"><span class="navicon">▣</span><span>Clip Studio</span></a><a href="#my-clips"><span class="navicon">▶</span><span>My Clips</span></a><a href="#earnings"><span class="navicon">₹</span><span>My Earnings</span></a><a href="#connections"><span class="navicon">⌘</span><span>AI Connections</span></a><a href="/automation"><span class="navicon">⚡</span><span>Automation jobs</span></a></nav><div class="sidefoot">Built for creators<br><span style="color:#64718f">Campaigns · Clips · Insights</span></div></aside>
<main><section id="overview" class="hero"><div><div class="eyebrow">Creator command centre</div><h1>Make every moment <span style="background:linear-gradient(90deg,var(--cyan),#9b8cff,var(--pink));background-clip:text;color:transparent">count.</span></h1><p>Your campaign workspace, clip production and earnings in one place.</p></div><div class="hero-visual" aria-label="Animated three-dimensional ClipPilot processing core"><div class="clip-core"><div class="core-face front">✂</div><div class="core-face back">▶</div><div class="core-face left">▣</div><div class="core-face right">✦</div><div class="core-ring"></div><div class="core-ring ring-two"></div><span class="core-dot"></span></div></div><div class="hero-actions"><a class="btn" href="#campaigns">＋ Add campaign</a><a class="btn btn-secondary" href="#clip-studio">Create a clip ↗</a></div></section>
{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="flash">{{message}}</div>{% endfor %}{% endwith %}
<div class="notice"><b>Current capabilities:</b> manual campaign tracking, best-effort public directory scanning, FFmpeg vertical clipping and manually recorded earnings. AI moment detection, automatic creator discovery, live clipping and marketplace earnings verification still require integrations. Only process footage you own or are authorized to use.</div>
<div class="grid"><div class="metric" style="--accent:var(--cyan);--glow:rgba(35,231,255,.2)"><span class="micon">◈</span><small>Campaigns saved</small><strong>{{total}}</strong></div><div class="metric" style="--accent:var(--violet);--glow:rgba(168,85,247,.2)"><span class="micon">↗</span><small>Best saved rate</small><strong>{{best_rate}}</strong><small>per 1,000 eligible views</small></div><div class="metric" style="--accent:var(--pink);--glow:rgba(255,79,216,.16)"><span class="micon">▣</span><small>Clips created</small><strong>{{clips}}</strong></div><div class="metric" style="--accent:var(--green);--glow:rgba(54,224,178,.16)"><span class="micon">✓</span><small>Submissions tracked</small><strong>{{submitted}}</strong></div></div>
<section id="campaigns" class="section"><div class="card"><div class="cardhead"><div><div class="eyebrow">01 / Discover</div><h2>Campaign Finder</h2><p class="sub">Scan public campaign directories for visible listings.</p></div><span class="tag">PUBLIC SCAN</span></div><form method="post" action="/discover"><button type="submit">⌕ Scan public campaigns</button></form><div class="row" style="margin-top:12px"><a class="btn btn-secondary btn-small" href="https://contentrewards.com/c/discover" target="_blank" rel="noopener">Content Rewards ↗</a><a class="btn btn-secondary btn-small" href="https://clipping.net/c/discover" target="_blank" rel="noopener">CLIPPING ↗</a></div>{% if discovery_error %}<p class="notice" style="margin-top:12px">{{discovery_error}}</p>{% endif %}{% if discovered %}<h3 style="font-size:13px;margin-top:18px">Public results · {{discovered|length}}</h3><p class="sub">Verify eligibility, payment terms, deadlines and clipping rights on the campaign page.</p>{% for d in discovered %}<div class="campaign-result"><div class="campaign-result-head"><div><b>{{d.name}}</b><div class="sub">{{d.source}} · {{d.status}}</div></div><span class="pill">{{d.rate_detail}}</span></div><div class="campaign-facts"><div><small>Budget</small><b>{{d.budget_left}}</b></div><div><small>Minimum views</small><b>{{d.minimum_views}}</b></div><div><small>Platforms</small><b>{{d.platforms|join(', ')}}</b></div></div><p class="sub">{{d.india_note}}</p><small>{{d.detail}}</small><p style="margin:9px 0 0"><a class="btn btn-secondary btn-small" href="{{d.url}}" target="_blank" rel="noopener">Check campaign & rules ↗</a> <form method="post" action="/save-discovered/{{loop.index0}}" style="display:inline"><button class="btn-small" type="submit">＋ Save to my campaigns</button></form></p></div>{% endfor %}{% endif %}</div>
<div class="two"><div class="card"><div class="eyebrow">02 / Track</div><h2>Add a campaign</h2><p class="sub">Save campaign details you have verified.</p><form method="post" action="/campaign"><label>Campaign / creator name</label><input name="name" required placeholder="Creator or campaign name"><label>Campaign URL</label><input name="url" type="url" placeholder="https://..."><div class="row"><div><label>Pay per 1,000 views (₹)</label><input name="rate" type="number" min="0" step="0.01" required></div><div><label>Maximum payout (₹)</label><input name="cap" type="number" min="0" step="0.01"></div></div><label>Deadline</label><input name="deadline" type="date"><label>Rules / notes</label><textarea name="notes" rows="3" placeholder="Eligibility, platforms, minimum views, rights..."></textarea><button type="submit">Save campaign</button></form></div>
<div class="card"><div class="eyebrow">03 / Compare</div><h2>Campaign ranking</h2><p class="sub">Transparent estimate based on saved rate, cap and deadline.</p>{% if campaigns %}<div class="tablewrap"><table><tr><th>Campaign</th><th>Rate / 1K</th><th>Score</th><th>Status</th></tr>{% for c in campaigns %}<tr><td><b>{{c.name}}</b><br><small>{{c.notes or ''}}</small>{% if c.url %}<br><a href="{{c.url}}" target="_blank" rel="noopener">Open ↗</a>{% endif %}</td><td>₹{{'%.2f'|format(c.rate)}}</td><td><span class="pill">{{c.score}}/100</span><br><form method="post" action="/automation/start/{{c.id}}" style="margin-top:7px"><button class="btn-small" type="submit">Start automatic discovery</button></form></td><td><form method="post" action="/status/{{c.id}}"><select name="status"><option {{'selected' if c.status=='research' else ''}}>research</option><option {{'selected' if c.status=='applied' else ''}}>applied</option><option {{'selected' if c.status=='accepted' else ''}}>accepted</option><option {{'selected' if c.status=='submitted' else ''}}>submitted</option><option {{'selected' if c.status=='paid' else ''}}>paid</option></select><button class="btn-small">Update</button></form></td></tr>{% endfor %}</table></div>{% else %}<div class="empty">No campaigns saved yet.</div>{% endif %}</div></div></section>
<section id="clip-studio" class="section"><div class="card"><div class="cardhead"><div><div class="eyebrow">04 / Produce</div><h2>Clip Studio</h2><p class="sub">Turn an authorized source video segment into a vertical 9:16 MP4.</p></div><span class="tag">FFMPEG</span></div>{% if latest_clip %}<div class="download-ready"><div><b>Your clip is ready</b><span class="sub">{{latest_clip}}</span></div><a class="btn" href="/clips/{{latest_clip}}">Download MP4 ↓</a></div>{% endif %}<div class="studio-stage"><div class="studio-object" aria-hidden="true"><div class="studio-orbit"></div><div class="studio-frame"><div class="studio-frame-inner">▶</div></div></div><div class="studio-copy"><b>Clip rendering workspace</b><p>Upload authorized footage, choose a segment and render a vertical 9:16 MP4. This animated frame is a visual guide, not a live video preview.</p><div class="studio-chips"><span>9:16 vertical</span><span>FFmpeg render</span><span>Up to 180 sec</span></div></div></div><div class="two"><form method="post" action="/make-clip" enctype="multipart/form-data"><label>Upload source video</label><input type="file" name="video" accept="video/*" required><div class="row"><div><label>Start time · seconds</label><input type="number" name="start" min="0" step="0.1" value="0" required></div><div><label>Duration · seconds (max 180)</label><input type="number" name="duration" min="1" max="180" step="0.1" value="30" required></div></div><button type="submit">✦ Render vertical clip</button></form><form method="post" action="/submit-youtube"><label>Or paste a YouTube video / Shorts / livestream link</label><input type="url" name="youtube_url" placeholder="https://www.youtube.com/watch?v=..." required><p class="sub">Submit a video you own or have permission to clip. The link is saved for processing; it is not downloaded automatically in this version.</p><button type="submit">↗ Submit YouTube link</button></form></div><div class="card" style="margin-top:15px"><div class="eyebrow">Source queue</div><h2>Submitted YouTube links</h2>{% if youtube_sources %}{% for y in youtube_sources %}<div style="padding:9px 0;border-bottom:1px solid var(--line)"><a href="{{y.url}}" target="_blank" rel="noopener">{{y.url}}</a><span class="pill" style="float:right">{{y.status}}</span></div>{% endfor %}{% else %}<div class="empty">No YouTube links submitted yet.</div>{% endif %}</div></div></section>
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
    con.execute("""CREATE TABLE IF NOT EXISTS youtube_sources(
        id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, status TEXT DEFAULT 'submitted', created TEXT NOT NULL)""")
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
    youtube_sources = [dict(x) for x in con.execute("SELECT * FROM youtube_sources ORDER BY id DESC LIMIT 20").fetchall()]
    con.close()
    latest_clip = session.get("latest_clip")
    if latest_clip and not (OUTPUT_DIR / latest_clip).is_file():
        latest_clip = None
    return render_template_string(PAGE, latest_clip=latest_clip, youtube_sources=youtube_sources,
        total=len(rows), best_rate=f"₹{best:.2f}", clips=len(files),
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

def _enrich_campaign(item):
    """Read only public campaign details; never infer India eligibility or earnings."""
    headers = {"User-Agent": "ClipPilotAI/1.0 (public campaign details)"}
    data = dict(item)
    data.update({
        "status": "Status not confirmed",
        "rate_detail": item.get("pay") or "Rate not found",
        "budget_left": "Not shown publicly",
        "minimum_views": "Not shown publicly",
        "platforms": [],
        "india_note": "India eligibility and bank payout are not verified",
    })
    try:
        response = requests.get(item["url"], headers=headers, timeout=8)
        response.raise_for_status()
        if len(response.content) > 2_000_000:
            return data
        text = _clean_text(BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True))
        if re.search(r"(?i)paused|closed|ended|not accepting", text):
            data["status"] = "Public page indicates campaign is paused or closed"
        elif re.search(r"(?i)accepting clips|taking clips| live ", " " + text + " "):
            data["status"] = "Public page indicates clips are being accepted"

        platforms = ["YouTube", "TikTok", "Instagram", "Facebook", "X", "Kick"]
        data["platforms"] = [p for p in platforms if re.search(r"(?i)\b" + re.escape(p) + r"\b", text)]
        rates = re.findall(r"(?i)\$\s?[\d,.]+\s*(?:to\s*\$?\s?[\d,.]+)?\s*/\s*(?:100K|1K|1M)\b", text)
        if not rates:
            rates = re.findall(r"(?i)\$\s?[\d,.]+\s*/\s*1K\s*views", text)
        if not rates:
            rates = re.findall(r"(?i)per\s*1K\s*views\s*\$\s?[\d,.]+", text)
        if rates:
            data["rate_detail"] = " · ".join(dict.fromkeys(_clean_text(x) for x in rates[:4]))

        budget = re.search(r"\$([\d,.]+)\s*/\s*\$([\d,.]+)", text)
        if budget:
            spent = float(budget.group(1).replace(",", ""))
            total = float(budget.group(2).replace(",", ""))
            left = max(0, total - spent)
            data["budget_left"] = f"${left:,.0f} of ${total:,.0f} shown remaining"
        elif re.search(r"(?i)\$[\d,.]+\s+in pools?", text):
            pool = re.search(r"(?i)\$[\d,.]+\s+in pools?", text)
            data["budget_left"] = _clean_text(pool.group(0))

        minimum = re.search(r"(?i)to qualify\s*(?:from\s*)?([\d,.]+\s*[KkMm]?)\s*views", text)
        if minimum:
            data["minimum_views"] = minimum.group(1).replace(" ", "") + " views"

        if not data["platforms"]:
            data["platforms"] = ["Check campaign page"]
    except (requests.RequestException, ValueError, TypeError):
        pass
    return data

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
    # Enrich a small, bounded set of public results to keep scans responsive.
    enriched = []
    for item in results[:8]:
        enriched.append(_enrich_campaign(item))
    session["discovered_campaigns"] = enriched
    if not results:
        session["discovery_error"] = (
            "No campaign cards could be read right now. The sites may have changed their public page layout or blocked automated requests. "
            + "Use the official directory links above; no login or access controls were bypassed."
        )
    elif errors:
        session["discovery_error"] = "Some sources could not be scanned: " + " ".join(errors)
    return redirect(url_for("home"))

@app.post("/save-discovered/<int:index>")
def save_discovered(index):
    items = session.get("discovered_campaigns", [])
    if index < 0 or index >= len(items):
        flash("That discovery result has expired. Scan campaigns again.")
        return redirect(url_for("home") + "#campaigns")
    item = items[index]
    raw_url = (item.get("url") or "").strip()
    parsed = urlparse(raw_url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "clipping.net" or host.endswith(".clipping.net") or host == "contentrewards.com" or host.endswith(".contentrewards.com")):
        flash("This result is not from a supported campaign directory, so it was not saved.")
        return redirect(url_for("home") + "#campaigns")
    name = (item.get("name") or "Discovered campaign").strip()[:100]
    notes = "Discovered from " + str(item.get("source") or "public directory") + ". Public details: " + str(item.get("rate_detail") or "rate not found") + ". India eligibility, bank payout and clipping permission must be checked manually."
    con = db()
    exists = con.execute("SELECT id FROM campaigns WHERE url=?", (raw_url,)).fetchone()
    if exists:
        con.close()
        flash("This campaign is already in your saved campaigns.")
        return redirect(url_for("home") + "#campaigns")
    con.execute("INSERT INTO campaigns(name,url,rate,cap,deadline,notes,status,created) VALUES(?,?,?,?,?,?,?,?)",
        (name, raw_url, 0, None, None, notes, "research", datetime.utcnow().isoformat()))
    con.commit()
    con.close()
    flash("Campaign saved for review. Add its verified INR rate and check India eligibility, payout and clipping rules before applying.")
    return redirect(url_for("home") + "#campaigns")


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

@app.post("/submit-youtube")
def submit_youtube():
    raw = (request.form.get("youtube_url") or "").strip()
    try:
        parsed = urlparse(raw)
        host = (parsed.hostname or "").lower()
        allowed = host in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtube-nocookie.com"}
        video_path = parsed.path.startswith(("/watch", "/shorts/", "/live/", "/embed/")) or host == "youtu.be"
        if parsed.scheme != "https" or not allowed or not video_path:
            raise ValueError()
        if host.endswith("youtube.com") and parsed.path == "/watch" and not parsed.query:
            raise ValueError()
    except ValueError:
        flash("Enter a valid HTTPS YouTube video, Shorts or livestream URL.")
        return redirect(url_for("home") + "#clip-studio")
    con = db()
    con.execute("INSERT INTO youtube_sources(url,status,created) VALUES(?,?,?)",
                (raw, "submitted — permission review", datetime.utcnow().isoformat()))
    con.commit()
    con.close()
    flash("YouTube link submitted. It is saved in your source queue; automatic downloading and clipping are not enabled yet.")
    return redirect(url_for("home") + "#clip-studio")


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
    session["latest_clip"] = out.name
    flash("Your vertical clip is ready. Download it directly below.")
    return redirect(url_for("home") + "#clip-studio")

@app.route("/clips/<path:filename>")
def clips(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.get("/health")
def health(): return {"ok": True, "app": "ClipPilot AI"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","5000")))
