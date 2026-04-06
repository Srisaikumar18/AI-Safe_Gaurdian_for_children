"""
MelodyWings Safe AI — Web Safety Dashboard
-------------------------------------------
Combines chat + video analysis with a real-time web UI.
Run: python dashboard.py
Visit: http://localhost:5000
"""

import json
import os
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response

# Import our analyzers (same directory)
import sys
sys.path.insert(0, os.path.dirname(__file__))
from chat_analyzer import ChatAnalyzer
from video_analyzer import VideoAnalyzer, generate_synthetic_video
from pipeline import SafetyPipeline, Incident, confidence_to_severity, AlertLogger

app     = Flask(__name__)
os.makedirs("logs", exist_ok=True)

# Shared state
pipeline = SafetyPipeline(session_id=datetime.now().strftime("session_%Y%m%d_%H%M%S"))
_event_clients: list = []   # SSE clients
_lock = threading.Lock()


def broadcast(event_type: str, data: dict):
    """Push a server-sent event to all connected dashboard clients."""
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    with _lock:
        for q in list(_event_clients):
            try:
                q.append(msg)
            except Exception:
                pass


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    body    = request.get_json()
    message = (body or {}).get("message", "").strip()
    if not message:
        return jsonify({"error": "empty message"}), 400

    result  = pipeline.chat_analyzer.analyze(message)
    flagged = not result.is_safe
    flags   = []

    if flagged:
        for flag in result.flags:
            severity = confidence_to_severity(flag.confidence, flag.category)
            inc = Incident(
                incident_id = pipeline.logger.next_id(),
                timestamp   = result.timestamp,
                source      = "chat",
                severity    = severity,
                category    = flag.category,
                reason      = flag.reason,
                content     = message,
                confidence  = flag.confidence,
                session_id  = pipeline.session_id,
            )
            pipeline.logger.log(inc)
            flags.append(inc.to_dict())
            broadcast("incident", inc.to_dict())

    return jsonify({
        "message":  message,
        "safe":     not flagged,
        "emotion":  "default",
        "flags":    flags,
        "alert":    flagged,
    })


@app.route("/api/run_demo", methods=["POST"])
def api_run_demo():
    """Run the full simulated session in a background thread."""
    def run():
        chat_stream = [
            ("Hi! I'm really excited to learn drawing today!", 0.5),
            ("You're such an idiot, I hate this stupid app!", 0.8),
            ("Can you help me? I don't understand.", 0.5),
            ("My phone number is 555-867-5309, call me.", 0.8),
            ("I feel so sad today, I cried a lot.", 0.5),
            ("Send me a picture without your shirt on.", 0.8),
            ("That was amazing, I'm so happy!", 0.5),
            ("I live at 47 Oak Street, come visit.", 0.8),
            ("I want to kill this level in the game!", 0.5),
            ("Thank you, you're the best mentor! 😊", 0.5),
        ]
        for msg, delay in chat_stream:
            result  = pipeline.chat_analyzer.analyze(msg)
            payload = {"message": msg, "safe": result.is_safe, "ts": result.timestamp}
            broadcast("chat", payload)
            if not result.is_safe:
                for flag in result.flags:
                    severity = confidence_to_severity(flag.confidence, flag.category)
                    inc = Incident(
                        incident_id = pipeline.logger.next_id(),
                        timestamp   = result.timestamp,
                        source      = "chat",
                        severity    = severity,
                        category    = flag.category,
                        reason      = flag.reason,
                        content     = msg,
                        confidence  = flag.confidence,
                        session_id  = pipeline.session_id,
                    )
                    pipeline.logger.log(inc)
                    broadcast("incident", inc.to_dict())
            time.sleep(delay)

        # Video
        video_path = "logs/test_session.mp4"
        if not os.path.exists(video_path):
            generate_synthetic_video(video_path)

        broadcast("status", {"msg": "🎬 Video analysis starting…"})
        report = pipeline.video_analyzer.analyze(video_path, sample_rate=30)

        for fr in report["frame_results"]:
            broadcast("frame", {
                "frame": fr.frame_index,
                "ts":    round(fr.timestamp_s, 2),
                "status": fr.status,
                "flags": fr.flags,
            })
            if fr.status == "FLAGGED":
                for reason in fr.flags:
                    inc = Incident(
                        incident_id = pipeline.logger.next_id(),
                        timestamp   = datetime.now().strftime("%H:%M:%S"),
                        source      = "video_frame",
                        severity    = confidence_to_severity(fr.confidence, "VISUAL"),
                        category    = "VISUAL_CONTENT",
                        reason      = reason,
                        content     = f"Frame {fr.frame_index} @ {fr.timestamp_s:.1f}s",
                        confidence  = fr.confidence,
                        session_id  = pipeline.session_id,
                    )
                    pipeline.logger.log(inc)
                    broadcast("incident", inc.to_dict())

        for tr in report["transcript"]:
            if not tr["is_safe"]:
                for flag in tr["flags"]:
                    inc = Incident(
                        incident_id = pipeline.logger.next_id(),
                        timestamp   = datetime.now().strftime("%H:%M:%S"),
                        source      = "video_transcript",
                        severity    = confidence_to_severity(flag["confidence"], flag["category"]),
                        category    = flag["category"],
                        reason      = flag["reason"],
                        content     = tr["text"],
                        confidence  = flag["confidence"],
                        session_id  = pipeline.session_id,
                    )
                    pipeline.logger.log(inc)
                    broadcast("incident", inc.to_dict())

        broadcast("status", {"msg": "✅ Demo session complete"})

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"started": True})


@app.route("/api/incidents")
def api_incidents():
    return jsonify([inc.to_dict() for inc in pipeline.logger.incidents])


@app.route("/stream")
def stream():
    """Server-Sent Events endpoint for real-time updates."""
    q: list = []
    with _lock:
        _event_clients.append(q)

    def generate():
        try:
            yield "data: connected\n\n"
            while True:
                if q:
                    yield q.pop(0)
                else:
                    time.sleep(0.1)
        except GeneratorExit:
            with _lock:
                if q in _event_clients:
                    _event_clients.remove(q)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    app.run(debug=False, threaded=True, port=5000)