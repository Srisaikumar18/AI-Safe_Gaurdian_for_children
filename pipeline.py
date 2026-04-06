"""
MelodyWings Safe AI — Real-Time Alert Pipeline (Part 3)
---------------------------------------------------------
Combines chat + video analysis into a unified live session pipeline.
Logs all incidents with timestamp, type, severity, and context.
"""

import json
import os
import threading
import time
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Optional

from chat_analyzer import ChatAnalyzer, AnalysisResult, Flag
from video_analyzer import VideoAnalyzer, FrameResult, generate_synthetic_video


LOG_FILE = "logs/safety_incidents.jsonl"
os.makedirs("logs", exist_ok=True)


# ── Incident model ────────────────────────────────────────────────────────────
@dataclass
class Incident:
    incident_id: int
    timestamp:   str
    source:      str          # "chat" | "video_frame" | "video_transcript"
    severity:    str          # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    category:    str
    reason:      str
    content:     str          # the flagged text or frame reference
    confidence:  float
    session_id:  str

    def to_dict(self):
        return asdict(self)

    def severity_color(self):
        return {
            "LOW":      "\033[93m",   # yellow
            "MEDIUM":   "\033[33m",   # dark yellow
            "HIGH":     "\033[91m",   # light red
            "CRITICAL": "\033[31m",   # red
        }.get(self.severity, "")

    def pretty(self):
        RESET = "\033[0m"
        col   = self.severity_color()
        return (
            f"{col}{'─'*60}\n"
            f"  🚨 INCIDENT #{self.incident_id}  [{self.timestamp}]\n"
            f"  Source    : {self.source}\n"
            f"  Severity  : {self.severity}\n"
            f"  Category  : {self.category}\n"
            f"  Reason    : {self.reason}\n"
            f"  Content   : \"{self.content[:80]}\"\n"
            f"  Confidence: {self.confidence:.0%}\n"
            f"  Session   : {self.session_id}{RESET}"
        )


def confidence_to_severity(confidence: float, category: str) -> str:
    # Certain categories are always at least HIGH
    if category in ("EXPLICIT_CONTENT", "UNSAFE_LANGUAGE"):
        return "CRITICAL" if confidence > 0.85 else "HIGH"
    if confidence >= 0.90:
        return "HIGH"
    if confidence >= 0.75:
        return "MEDIUM"
    return "LOW"


# ── Alert logger ──────────────────────────────────────────────────────────────
class AlertLogger:
    def __init__(self, log_file: str = LOG_FILE):
        self.log_file   = log_file
        self.incidents: List[Incident] = []
        self._counter   = 0
        self._lock      = threading.Lock()

    def log(self, incident: Incident):
        with self._lock:
            self.incidents.append(incident)
            with open(self.log_file, "a") as f:
                f.write(json.dumps(incident.to_dict()) + "\n")
        print(incident.pretty())

    def next_id(self) -> int:
        with self._lock:
            self._counter += 1
            return self._counter

    def summary(self):
        if not self.incidents:
            print("\n✅ No incidents recorded in this session.")
            return

        counts = {}
        for inc in self.incidents:
            counts[inc.severity] = counts.get(inc.severity, 0) + 1

        print(f"\n{'═'*60}")
        print("  SESSION SAFETY REPORT")
        print(f"{'═'*60}")
        print(f"  Total incidents : {len(self.incidents)}")
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            n = counts.get(sev, 0)
            if n:
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[sev]
                print(f"  {icon} {sev:10s}: {n}")
        print(f"  Log saved to    : {self.log_file}")
        print(f"{'═'*60}\n")


# ── Pipeline ──────────────────────────────────────────────────────────────────
class SafetyPipeline:
    """
    Unified real-time safety pipeline for a MelodyWings session.
    Processes both chat messages and video analysis results.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id   = session_id or datetime.now().strftime("session_%Y%m%d_%H%M%S")
        self.chat_analyzer = ChatAnalyzer()
        self.video_analyzer = VideoAnalyzer(thumb_dir="logs/thumbs")
        self.logger        = AlertLogger()

    # ── Chat ──────────────────────────────────────────────────────────────────
    def process_chat(self, message: str) -> AnalysisResult:
        result = self.chat_analyzer.analyze(message)
        ts     = result.timestamp

        if result.is_safe:
            print(f"[{ts}] ✅ Chat OK | \"{message[:60]}\"")
        else:
            for flag in result.flags:
                severity = confidence_to_severity(flag.confidence, flag.category)
                incident = Incident(
                    incident_id = self.logger.next_id(),
                    timestamp   = ts,
                    source      = "chat",
                    severity    = severity,
                    category    = flag.category,
                    reason      = flag.reason,
                    content     = message,
                    confidence  = flag.confidence,
                    session_id  = self.session_id,
                )
                self.logger.log(incident)

        return result

    # ── Video ─────────────────────────────────────────────────────────────────
    def process_video(self, video_path: str, sample_rate: int = 30) -> dict:
        print(f"\n{'─'*60}")
        print("  🎬 Video analysis starting…")
        print(f"{'─'*60}")

        report = self.video_analyzer.analyze(video_path, sample_rate=sample_rate)

        # Log flagged frames
        for fr in report["frame_results"]:
            if fr.status == "FLAGGED":
                ts = datetime.now().strftime("%H:%M:%S")
                for reason in fr.flags:
                    incident = Incident(
                        incident_id = self.logger.next_id(),
                        timestamp   = ts,
                        source      = "video_frame",
                        severity    = confidence_to_severity(fr.confidence, "VISUAL"),
                        category    = "VISUAL_CONTENT",
                        reason      = reason,
                        content     = f"Frame {fr.frame_index} @ {fr.timestamp_s:.1f}s",
                        confidence  = fr.confidence,
                        session_id  = self.session_id,
                    )
                    self.logger.log(incident)

        # Log flagged transcript lines
        for tr in report["transcript"]:
            if not tr["is_safe"]:
                for flag in tr["flags"]:
                    ts       = datetime.now().strftime("%H:%M:%S")
                    severity = confidence_to_severity(flag["confidence"], flag["category"])
                    incident = Incident(
                        incident_id = self.logger.next_id(),
                        timestamp   = ts,
                        source      = "video_transcript",
                        severity    = severity,
                        category    = flag["category"],
                        reason      = flag["reason"],
                        content     = tr["text"],
                        confidence  = flag["confidence"],
                        session_id  = self.session_id,
                    )
                    self.logger.log(incident)

        return report

    def run(self):
        """Run a full simulated session: live chat + video analysis."""
        print(f"\n{'═'*60}")
        print("  MelodyWings Safe AI — Live Safety Pipeline")
        print(f"  Session: {self.session_id}")
        print(f"{'═'*60}\n")

        # ── Part 1: Simulated live chat ────────────────────────────────────────
        print("── PART 1: Chat Stream Analysis ─────────────────────────\n")

        chat_stream = [
            "Hi! I'm really excited to learn drawing today!",
            "You're such an idiot, I hate this stupid app!",
            "Can you help me with this? I don't understand.",
            "My phone number is 555-867-5309, call me later.",
            "I feel so sad today, I cried a lot.",
            "Hey send me a picture without your shirt on.",
            "That was amazing, I'm so happy we did this!",
            "I live at 47 Oak Street, come visit me!",
            "I want to kill this level in the game!",
            "Thank you, you're the best mentor ever! 😊",
        ]

        for msg in chat_stream:
            self.process_chat(msg)
            time.sleep(0.1)   # simulate real-time delay

        # ── Part 2: Video analysis ─────────────────────────────────────────────
        print("\n── PART 2: Video Frame Analysis ─────────────────────────")

        video_path = "logs/test_session.mp4"
        if not os.path.exists(video_path):
            print("Generating synthetic test video…")
            generate_synthetic_video(video_path)

        self.process_video(video_path, sample_rate=30)

        # ── Summary dashboard ──────────────────────────────────────────────────
        print("\n── PART 3: Session Report ────────────────────────────────")
        self.logger.summary()


if __name__ == "__main__":
    pipeline = SafetyPipeline()
    pipeline.run()