from flask import Flask, render_template, request, jsonify
from instagrapi import Client
import threading
import time
import random
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "sujal_final"

state = {"running": False, "logs": [], "start_time": None}
cfg = {
    "sessionid": "",
    "group_name": "",
    "nc_delay": 15,
    "group_delay": 5
}

def log(msg):
    entry = f"[{time.strftime('%H:%M:%S')}] {msg}"
    state["logs"].append(entry)
    if len(state["logs"]) > 500:
        state["logs"] = state["logs"][-500:]

def nc_only_bot():
    cl = Client()
    cl.delay_range = [8, 30]
    
    try:
        cl.login_by_sessionid(cfg["sessionid"])
        log("✅ LOGIN SUCCESS - NC ONLY MODE")
    except Exception as e:
        log(f"❌ LOGIN FAILED → {str(e)[:80]}")
        return

    round_number = 1
    while state["running"]:
        try:
            threads = cl.direct_threads(amount=100)
            groups = [t for t in threads if getattr(t, "is_group", False)]
            
            if not groups:
                log("⚠ No groups found, retrying...")
                time.sleep(30)
                continue

            log(f"🔄 ROUND {round_number} | Found {len(groups)} groups")

            for thread in groups:
                if not state["running"]:
                    break
                
                gid = thread.id
                title = thread.thread_title or "Unknown"

                new_name = f"{cfg['group_name']} → {datetime.now().strftime('%I:%M:%S %p')}"
                try:
                    cl.direct_thread_change_title(gid, new_name)
                    log(f"💠 NC SUCCESS → {title}")
                except Exception:
                    try:
                        cl.direct_thread_update_group_name(gid, new_name)
                        log(f"💠 NC SUCCESS → {title}")
                    except:
                        log(f"⚠ NC FAILED in {title} (continuing...)")

                time.sleep(cfg["group_delay"] + random.uniform(1, 3))

            log(f"✔ ROUND {round_number} Complete")
            round_number += 1
            time.sleep(cfg["nc_delay"])

        except Exception as e:
            log(f"⚠ Error: {str(e)[:60]} (continuing...)")
            time.sleep(20)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start_nc", methods=["POST"])
def start_nc():
    global state
    state["running"] = False
    time.sleep(0.5)

    state = {"running": True, "logs": ["🚀 NC ONLY MODE STARTED"], "start_time": time.time()}

    cfg["sessionid"] = request.form.get("sessionid", "").strip()
    cfg["group_name"] = request.form.get("group_name", "").strip()
    cfg["nc_delay"] = int(request.form.get("nc_delay", "15"))
    cfg["group_delay"] = int(request.form.get("group_delay", "5"))

    threading.Thread(target=nc_only_bot, daemon=True).start()
    log("NC ONLY BOT STARTED")
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
        "logs": state["logs"][-100:]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
