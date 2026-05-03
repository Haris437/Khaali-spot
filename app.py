from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import cv2
import threading
import time
import os
import numpy as np
from PIL import Image
import io

from detector import run_detection

app = Flask(__name__)
CORS(app)

# ─── Shared state ────────────────────────────────────────────────────────────
latest_stats = {
    "total_chairs": 0,
    "occupied": 0,
    "free": 0,
    "occupancy_percent": 0
}
stats_lock = threading.Lock()

# ─── Background webcam thread ─────────────────────────────────────────────────
def webcam_loop():
    """Continuously reads from webcam, runs detection every 2 seconds."""
    cap = cv2.VideoCapture(0)  # 0 = default webcam

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

        time.sleep(2)  # Run detection every 2 seconds

    cap.release()


# Start webcam thread only if running locally (not on Render/cloud)
import os
IS_SERVER = os.environ.get("RENDER") is not None  # Render sets this env var automatically

if not IS_SERVER:
    webcam_thread = threading.Thread(target=webcam_loop, daemon=True)
    webcam_thread.start()
else:
    print("[INFO] Running on server — webcam disabled. Use /upload for demo mode.")


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Main student dashboard."""
    return render_template("index.html")


@app.route("/status")
def status():
    """Returns current seat availability as JSON."""
    with stats_lock:
        return jsonify(latest_stats)


@app.route("/snapshot")
def snapshot():
    path = "static/output/frame.jpg"
    os.makedirs("static/output", exist_ok=True)  # ensure folder exists
    if not os.path.exists(path):
        # Return a simple JSON response instead of a file when nothing uploaded yet
        from flask import Response
        return Response(status=204)  # 204 = No Content, no error
    return send_file(path, mimetype="image/jpeg")


@app.route("/demo")
def demo_page():
    """Demo page where user can upload an image."""
    return render_template("index.html", demo=True)


@app.route("/upload", methods=["POST"])
def upload():
    """
    Accepts an uploaded image, runs detection, returns stats + annotated image.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    img_bytes = file.read()

    # Convert uploaded bytes to OpenCV frame
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame  = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({"error": "Could not read image"}), 400

    _, stats = run_detection(frame)

    return jsonify(stats)


# ─── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("static/output", exist_ok=True)
    app.run(debug=True, threaded=True, port=5000)
