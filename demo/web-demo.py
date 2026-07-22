#!/usr/bin/env python3
"""Editorial streaming chat UI for the ZeroClaw Solana toolbox demo.

http://127.0.0.1:8899 — you type; the agent (gpt-5.6-sol) runs the Solana tools.
Real runtime-trace events stream to the browser as an editorial pipeline console
(paper/ink, multi-accent, colored offset shadows; active steps sweep, completed
steps turn green, a coral BLOCKED block on failure). Solana Pay URLs render as
scannable QR codes. Python stdlib + zeroclaw + qrencode.
"""
import base64
import json
import os
import re
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ZB = os.path.expanduser("~/zeroclaw/target/release/zeroclaw")
TRACE = os.path.expanduser("~/.zeroclaw/data/state/runtime-trace.jsonl")
SESSION = "/tmp/zeroclaw-demo-session.json"
PORT = 8899

HTML = r"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ZeroClaw · Solana Toolbox</title>
<style>
:root{
  --paper:#f3f1ea;--paper2:#ece9df;--card:#ffffff;
  --ink:#0c0c0d;--ink2:#5f6066;--ink3:#9a9aa0;
  --line:#e3dfd4;
  --blue:#3d5afe;--purple:#7c4dff;--amber:#f5a623;--teal:#12b886;--coral:#ff5a5f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);height:100vh;display:flex;flex-direction:column;overflow:hidden;
  font:15px/1.55 -apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.eyebrow{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink3);font-weight:600}
header{padding:16px 26px;border-bottom:1.5px solid var(--ink);display:flex;align-items:center;gap:14px;background:var(--paper)}
header .mark{width:26px;height:26px;border:1.5px solid var(--ink);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:14px}
header h1{font-size:17px;font-weight:800;margin:0;letter-spacing:-.02em}
header .dot{width:8px;height:8px;border-radius:50%;background:var(--teal)}
header .sub{color:var(--ink2);font-size:11px;letter-spacing:.12em;text-transform:uppercase;font-weight:600}
.tools{display:flex;gap:7px;margin-left:auto;flex-wrap:wrap}
.chip{font-size:10.5px;color:var(--ink2);background:var(--card);border:1px solid var(--line);border-radius:4px;padding:4px 9px;font-weight:600}
.chip b{color:var(--ink)}
#thread{flex:1;overflow-y:auto;padding:30px 26px;display:flex;flex-direction:column;gap:20px}
.msg{max-width:min(740px,90%);padding:14px 17px;line-height:1.6}
.user{align-self:flex-end;background:var(--ink);color:var(--paper);border-radius:3px;font-weight:500;box-shadow:5px 5px 0 var(--blue)}
.bot{align-self:flex-start;background:var(--card);border:1.5px solid var(--ink);border-radius:3px;box-shadow:6px 6px 0 var(--teal);white-space:pre-wrap;word-wrap:break-word}
.bot a{color:var(--blue);font-weight:600}
.bot strong,.bot b{font-weight:800}
.bot code{font-family:ui-monospace,Menlo,monospace;font-size:12.5px;background:var(--paper2);border:1px solid var(--line);border-radius:3px;padding:1px 5px;word-break:break-all}
.bot pre{background:var(--paper2);border:1px solid var(--line);border-radius:3px;padding:11px 13px;overflow-x:auto;margin:11px 0}
.bot pre code{background:none;border:0;padding:0;font-size:12px;white-space:pre-wrap;word-break:break-all}
.qr{margin-top:14px;background:#fff;padding:12px;border:1.5px solid var(--ink);display:inline-block;box-shadow:5px 5px 0 var(--amber)}
.qr img{display:block;width:184px;height:184px}
.qr .cap{color:var(--ink);font-size:10px;text-align:center;margin-top:7px;font-weight:700;letter-spacing:.1em;text-transform:uppercase}
/* pipeline console */
.console{align-self:flex-start;width:min(740px,94%);background:var(--card);border:1.5px solid var(--ink);border-radius:3px;padding:16px 16px 10px;box-shadow:7px 7px 0 var(--purple);transition:box-shadow .2s}
.console .hd{display:flex;align-items:center;gap:9px;margin:0 2px 14px}
.console .hd .l{width:20px;height:4px;background:var(--purple);border-radius:2px}
.console.blocked{box-shadow:7px 7px 0 var(--coral);animation:shake .28s steps(2) 2}
.console.blocked .hd .l{background:var(--coral)}
.step{display:flex;align-items:center;gap:12px;padding:6px 2px;opacity:0;transform:translateX(-10px);animation:slidein .2s forwards}
.step .idx{width:20px;font-size:11px;font-weight:700;color:var(--ink3);text-align:right}
.step .lb{flex:0 0 auto;min-width:172px;font-size:12.5px;font-weight:600;color:var(--ink);letter-spacing:.01em}
.step .bar{flex:1;height:8px;background:var(--paper2);border-radius:2px;position:relative;overflow:hidden}
.step .bar i{position:absolute;inset:0;border-radius:2px;background:var(--ac,var(--ink2))}
.step .tk{width:18px;text-align:center;font-weight:800;color:var(--ink3);font-size:13px}
/* active = indeterminate sweep (never a dead gap) */
.step.active .bar i{background:linear-gradient(90deg,transparent 0,var(--ac) 42%,var(--ac) 58%,transparent 100%);background-size:42% 100%;background-repeat:no-repeat;animation:sweep 1.05s linear infinite}
.step.active .tk{color:var(--ac);animation:pulse .9s ease-in-out infinite}
/* done = fills solid green */
.step.done .bar i{background:var(--teal);animation:fill .35s ease-out forwards;width:100%}
.step.done .tk{color:var(--teal)}
.step.fail .bar i{background:var(--coral);animation:none;width:100%}
.step.fail .lb{color:var(--coral)}
.step.fail .tk{color:var(--coral)}
.blockbar{margin:10px 2px 4px;background:var(--coral);color:#fff;font-weight:800;font-size:12px;letter-spacing:.22em;padding:9px 12px;border-radius:2px;text-align:center;animation:blink .6s steps(2) infinite}
@keyframes slidein{to{opacity:1;transform:none}}
@keyframes sweep{0%{background-position:-42% 0}100%{background-position:142% 0}}
@keyframes fill{from{transform:scaleX(.15);transform-origin:left}to{transform:scaleX(1);transform-origin:left}}
@keyframes pulse{50%{opacity:.3}}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-3px)}75%{transform:translateX(3px)}}
@keyframes blink{50%{opacity:.55}}
.empty{margin:auto;max-width:640px}
.empty .eyebrow{margin-bottom:16px}
.empty h2{font-size:46px;line-height:1.02;font-weight:800;letter-spacing:-.03em;margin:0 0 18px}
.empty h2 .hl{background:var(--ink);color:var(--paper);padding:0 10px;margin-right:4px}
.empty p{color:var(--ink2);font-size:15px;max-width:480px;margin:0 0 26px}
.sugg{display:flex;flex-direction:column;gap:10px;max-width:560px}
.sugg button{background:var(--card);border:1.5px solid var(--ink);border-radius:3px;color:var(--ink);padding:13px 16px;text-align:left;cursor:pointer;font-size:14px;font-weight:500;box-shadow:4px 4px 0 var(--line);transition:box-shadow .12s,transform .12s}
.sugg button:nth-child(1):hover{box-shadow:5px 5px 0 var(--blue)}
.sugg button:nth-child(2):hover{box-shadow:5px 5px 0 var(--purple)}
.sugg button:nth-child(3):hover{box-shadow:5px 5px 0 var(--amber)}
.sugg button:hover{transform:translate(-1px,-1px)}
footer{border-top:1.5px solid var(--ink);padding:16px 26px;display:flex;gap:12px;background:var(--paper)}
#msg{flex:1;background:var(--card);border:1.5px solid var(--ink);color:var(--ink);border-radius:3px;padding:13px 15px;font:inherit;resize:none;max-height:120px}
#msg:focus{outline:none;box-shadow:4px 4px 0 var(--blue)}
#send{background:var(--ink);color:var(--paper);border:0;border-radius:3px;padding:0 26px;font-weight:800;cursor:pointer;letter-spacing:.02em}
#send:disabled{opacity:.4;cursor:default}
</style></head><body>
<header>
  <span class="mark">💀</span>
  <div><h1>ZeroClaw · Solana Toolbox</h1><div class="sub"><span class="dot" style="display:inline-block;vertical-align:middle;margin-right:5px"></span>gpt-5.6-sol · canlı ajan</div></div>
  <div class="tools"><span class="chip"><b>4</b> araç</span><span class="chip">token-risk-check</span><span class="chip">sns-resolve</span><span class="chip">solana-pay-request</span><span class="chip">unsigned-transfer</span></div>
</header>
<div id="thread"><div class="empty" id="empty">
  <div class="eyebrow">Live agent field · Zero-custody</div>
  <h2><span class="hl">Ajan</span>nöbette.</h2>
  <p>Solana araçlarını doğal dille çalıştır. Ajan aracı çağırır, canlı zincir verisi çeker — pipeline'ı kalem kalem izlersin.</p>
  <div class="sugg">
    <button onclick="fill(this)">EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v token'ı güvenli mi?</button>
    <button onclick="fill(this)">bonfida.sol'e 0.1 SOL ödeme isteği (Solana Pay URL) oluştur</button>
    <button onclick="fill(this)">bonfida.sol kimin?</button>
  </div>
</div></div>
<footer>
  <textarea id="msg" rows="1" placeholder="Bir şey yaz… (örn: bu token güvenli mi: <mint>)"></textarea>
  <button id="send" onclick="send()">Gönder</button>
</footer>
<script>
const thread=document.getElementById('thread'),input=document.getElementById('msg'),btn=document.getElementById('send');
const KC={info:'#5f6066',tool:'#3d5afe',plugin:'#7c4dff',verify:'#f5a623',ok:'#12b886',fail:'#ff5a5f'};
let stepN=0;
function fill(b){input.value=b.textContent;input.focus();}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function md(s){s=esc(s);const B=[];
  s=s.replace(/```[a-zA-Z0-9]*\n?([\s\S]*?)```/g,function(m,c){B.push('<pre><code>'+c.replace(/\s+$/,'')+'</code></pre>');return '@@'+(B.length-1)+'@@';});
  s=s.replace(/`([^`\n]+)`/g,function(m,c){B.push('<code>'+c+'</code>');return '@@'+(B.length-1)+'@@';});
  s=s.replace(/\[([^\]]+)\]\((solana:[^)\s]+|https?:\/\/[^)\s]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');
  s=s.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
  s=s.replace(/(^|[\s(>])(solana:[^\s\)\]"'<]+|https?:\/\/[^\s\)\]"'<]+)/g,'$1<a href="$2" target="_blank" rel="noopener">$2</a>');
  return s.replace(/@@(\d+)@@/g,function(m,i){return B[+i];});}
function add(role,text,qr){const e=document.getElementById('empty');if(e)e.remove();
  const d=document.createElement('div');d.className='msg '+role;d.innerHTML=role==='bot'?md(text):esc(text);
  if(qr){const q=document.createElement('div');q.className='qr';q.innerHTML='<img src="'+qr+'"><div class="cap">Phantom ile okut</div>';d.appendChild(q);}
  thread.appendChild(d);thread.scrollTop=thread.scrollHeight;return d;}
function autg(){input.style.height='auto';input.style.height=Math.min(input.scrollHeight,120)+'px';}
input.addEventListener('input',autg);
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});

function newConsole(){const e=document.getElementById('empty');if(e)e.remove();stepN=0;
  const c=document.createElement('div');c.className='console';
  c.innerHTML='<div class="hd"><span class="l"></span><span class="eyebrow">Pipeline · canlı</span></div><div class="body"></div>';
  thread.appendChild(c);thread.scrollTop=thread.scrollHeight;return c;}
function markDone(s){s.classList.remove('active');s.classList.add('done');s.querySelector('.tk').textContent='✓';}
function addStep(con,d){const b=con.querySelector('.body');
  const prev=b.querySelector('.step.active');if(prev)markDone(prev);
  const col=KC[d.kind]||KC.info;stepN++;
  const s=document.createElement('div');s.className='step active';s.style.setProperty('--ac',col);
  s.innerHTML='<span class="idx mono">'+String(stepN).padStart(2,'0')+'</span><span class="lb">'+esc(d.label)+'</span><span class="bar"><i></i></span><span class="tk">▸</span>';
  b.appendChild(s);thread.scrollTop=thread.scrollHeight;return s;}
function finishSteps(con){con.querySelectorAll('.step.active').forEach(markDone);}
function failConsole(con,label){con.classList.add('blocked');
  const a=con.querySelector('.step.active')||con.querySelector('.step:last-child');
  if(a){a.classList.remove('active');a.classList.add('fail');a.querySelector('.tk').textContent='✕';}
  const bb=document.createElement('div');bb.className='blockbar';bb.textContent='⛔ İŞLEM ENGELLENDİ';con.querySelector('.body').appendChild(bb);
  thread.scrollTop=thread.scrollHeight;}

let es=null;
function send(){const text=input.value.trim();if(!text)return;
  add('user',text);input.value='';autg();btn.disabled=true;
  const con=newConsole();
  es=new EventSource('/stream?message='+encodeURIComponent(text));
  es.addEventListener('step',ev=>addStep(con,JSON.parse(ev.data)));
  es.addEventListener('done',ev=>{const d=JSON.parse(ev.data);finishSteps(con);add('bot',d.reply||'(boş)',d.qr);es.close();btn.disabled=false;input.focus();});
  es.addEventListener('fail',ev=>{const d=JSON.parse(ev.data);failConsole(con,d.label);if(d.reply)add('bot',d.reply,null);es.close();btn.disabled=false;input.focus();});
  es.onerror=()=>{failConsole(con,'bağlantı koptu');es.close();btn.disabled=false;};
}
</script></body></html>"""


# Our Solana toolbox (blue) vs external cross-verification tools (amber).
OUR_TOOLS = {
    "token_risk_check": "token risk",
    "sns_resolve": ".sol çözümü",
    "solana_pay_request": "pay isteği",
    "unsigned_transfer": "imzasız tx",
}
VERIFY_TOOLS = {
    "web_search_tool": "web araması",
    "web_search": "web araması",
    "web_fetch": "kaynak okunuyor",
    "http_request": "HTTP isteği",
    "browser": "sayfa açılıyor",
    "browse": "sayfa açılıyor",
}


def step_for(rec):
    ev = rec.get("event", {}) or {}
    cat, act = ev.get("category"), ev.get("action")
    msg = rec.get("message", "")
    at = rec.get("attributes", {}) or {}
    tool = at.get("tool") or at.get("plugin") or ""
    verify = tool in VERIFY_TOOLS
    name = OUR_TOOLS.get(tool) or VERIFY_TOOLS.get(tool) or tool
    if msg == "llm_request":
        return ("modele danışılıyor", "info")
    if cat == "tool" and act == "start":
        if verify:
            return (f"çapraz doğrulama · {name}", "verify")
        return (f"araç · {name}", "tool")
    if cat == "internal" and at.get("plugin"):
        return (msg or name, "plugin")
    if cat == "tool" and act == "complete":
        if verify:
            return (f"doğrulandı · {name}", "ok")
        return (f"sonuç · {name}", "ok")
    if cat == "tool" and act in ("reject", "fail"):
        return ("__FAIL__" + (msg or "araç reddedildi"), "fail")
    if msg == "llm_response":
        return ("model yanıtı hazır", "info")
    return None


def qr_data_uri(url):
    try:
        png = subprocess.run(["qrencode", "-o", "-", "-s", "6", "-m", "2", url],
                             capture_output=True, timeout=10).stdout
        if png:
            return "data:image/png;base64," + base64.b64encode(png).decode()
    except Exception:
        pass
    return None


class Handler(BaseHTTPRequestHandler):
    def _html(self, body):
        b = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _sse(self, event, data):
        try:
            self.wfile.write(f"event: {event}\ndata: {json.dumps(data)}\n\n".encode())
            self.wfile.flush()
        except Exception:
            pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            self._html(HTML)
            return
        if u.path != "/stream":
            self.send_response(404); self.end_headers(); return
        msg = (parse_qs(u.query).get("message", [""])[0]).strip()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        self._sse("step", {"label": "ajan başlatıldı", "kind": "info"})
        try:
            pos = os.path.getsize(TRACE)
        except OSError:
            pos = 0
        result = {"reply": None, "err": None}

        def run():
            try:
                out = subprocess.run(
                    [ZB, "agent", "-a", "demo", "-m", msg, "--session-state-file", SESSION],
                    capture_output=True, text=True, timeout=220)
                result["reply"] = (out.stdout or "").strip() or (out.stderr or "").strip()
            except subprocess.TimeoutExpired:
                result["err"] = "zaman aşımı"
            except Exception as e:
                result["err"] = str(e)

        t = threading.Thread(target=run, daemon=True)
        t.start()
        seen_fail = None
        while t.is_alive():
            time.sleep(0.15)
            try:
                with open(TRACE, "r") as f:
                    f.seek(pos)
                    chunk = f.read()
                    pos = f.tell()
            except OSError:
                chunk = ""
            for line in chunk.splitlines():
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                st = step_for(rec)
                if not st:
                    continue
                label, kind = st
                if label.startswith("__FAIL__"):
                    seen_fail = label[8:]
                    continue
                self._sse("step", {"label": label, "kind": kind})
        t.join(timeout=1)
        if result["err"] or seen_fail:
            self._sse("fail", {"label": result["err"] or seen_fail or "hata",
                               "reply": result["reply"]})
            return
        reply = result["reply"] or "(boş yanıt)"
        qr = None
        m = re.search(r"solana:[^\s\)\]\"']+", reply)
        if m:
            qr = qr_data_uri(m.group(0))
        self._sse("done", {"reply": reply, "qr": qr})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"ZeroClaw web demo → http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
