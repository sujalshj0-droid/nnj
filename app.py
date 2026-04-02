from flask import Flask, render_template, request, jsonify
from instagrapi import Client
import threading
import time
import random
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "sujal_final"

state = {"running": False, "sent": 0, "logs": [], "start_time": None}
cfg = {
    "sessionid": "",
    "messages": [],
    "delay": 12,          # Fast message delay
    "group_delay": 3      # Fast group switch
}

def log(msg):
    entry = f"[{time.strftime('%H:%M:%S')}] {msg}"
    state["logs"].append(entry)
    if len(state["logs"]) > 500:
        state["logs"] = state["logs"][-500:]

def spam_bot():
    cl = Client()
    cl.delay_range = [6, 18]
    
    try:
        cl.login_by_sessionid(cfg["sessionid"])
        log("✅ LOGIN SUCCESS - FAST SPAM MODE")
    except Exception as e:
        log(f"❌ LOGIN FAILED → {str(e)[:80]}")
        return

    while state["running"]:
        try:
            threads = cl.direct_threads(amount=100)
            groups = [t for t in threads if getattr(t, "is_group", False)]
            
            if not groups:
                log("⚠ No groups found, retrying in 20s...")
                time.sleep(20)
                continue

            log(f"🔄 Found {len(groups)} groups - Fast Rotation")

            for thread in groups:
                if not state["running"]:
                    break
                
                gid = thread.id
                title = thread.thread_title or "Unknown"

                msg = cfg["messages"][0]
                try:
                    cl.direct_send(msg, thread_ids=[gid])
                    state["sent"] += 1
                    log(f"📨 SENT to → {title}")
                except Exception:
                    log(f"⚠ SEND FAILED in {title} (continuing...)")

                time.sleep(cfg["group_delay"] + random.uniform(0.8, 2.2))

            time.sleep(cfg["delay"])

        except Exception as e:
            log(f"⚠ MAJOR ERROR: {str(e)[:60]} → Continuing loop...")
            time.sleep(15)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    global state
    state["running"] = False
    time.sleep(0.3)

    state = {"running": True, "sent": 0, "logs": ["🚀 FAST SPAM BOT STARTED"], "start_time": time.time()}

    cfg["sessionid"] = request.form.get("sessionid", "").strip()
    raw_text = request.form.get("messages", "").strip()
    cfg["messages"] = [raw_text] if raw_text else []
    cfg["delay"] = float(request.form.get("delay", "12"))
    cfg["group_delay"] = int(request.form.get("group_delay", "3"))

    threading.Thread(target=spam_bot, daemon=True).start()
    log("SPAM BOT STARTED - Continuous Mode")
    return jsonify({"ok": True})

@app.route("/stop", methods=["POST"])
def stop():
    state["running"] = False
    log("⛔ STOPPED BY USER")
    return jsonify({"ok": True})

@app.route("/status")
def status():
    uptime = "00:00:00"
    if state.get("start_time"):
        t = int(time.time() - state["start_time"])
        h, r = divmod(t, 3600)
        m, s = divmod(r, 60)
        uptime = f"{h:02d}:{m:02d}:{s:02d}"
    return jsonify({
        "running": state["running"],
        "sent": state["sent"],
        "uptime": uptime,
        "logs": state["logs"][-100:]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
