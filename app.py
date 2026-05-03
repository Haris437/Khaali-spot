from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for, session, Response
from flask_cors import CORS
import cv2
import threading
import time
import os
import numpy as np

from detector import run_detection

app = Flask(__name__)
app.secret_key = "khaali_spot_secret_2025"
CORS(app)

# ─── Shared state ─────────────────────────────────────────────────────────────
latest_stats = {
    "total_chairs": 0,
    "occupied": 0,
    "free": 0,
    "occupancy_percent": 0
}
stats_lock = threading.Lock()

# ─── Background webcam thread ──────────────────────────────────────────────────
def webcam_loop():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[WARNING] Webcam not found. Live feed disabled.")
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(1)
            continue
        _, stats = run_detection(frame)
        with stats_lock:
            latest_stats.update(stats)
        time.sleep(2)
    cap.release()

# Detect if running on a cloud server (Render or Hugging Face)
IS_SERVER = os.environ.get("RENDER") is not None or os.environ.get("SPACE_ID") is not None

if not IS_SERVER:
    webcam_thread = threading.Thread(target=webcam_loop, daemon=True)
    webcam_thread.start()
else:
    print("[INFO] Running on server — webcam disabled. Use upload for demo mode.")


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username and password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Please enter username and password.")
    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session["user"])


@app.route("/status")
def status():
    with stats_lock:
        return jsonify(latest_stats)


@app.route("/snapshot")
def snapshot():
    path = "static/output/frame.jpg"
    os.makedirs("static/output", exist_ok=True)
    if not os.path.exists(path):
        return Response(status=204)
    return send_file(path, mimetype="image/jpeg")


@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    file = request.files["image"]
    img_bytes = file.read()
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({"error": "Could not read image"}), 400
    _, stats = run_detection(frame)
    with stats_lock:
        latest_stats.update(stats)
    return jsonify(stats)


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("static/output", exist_ok=True)
    port = int(os.environ.get("PORT", 7860))
    app.run(debug=False, threaded=True, host="0.0.0.0", port=port)
