"""
MelodyWings Real-Time Alert System
-----------------------------------
Combines chat and video analysis into a unified safety monitoring pipeline.
Features:
- Real-time chat message monitoring
- Video frame-by-frame analysis
- Centralized alert logging
- Safety dashboard with live updates
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from chat_analyser import ChatAnalyzer
from video_analyser import VideoAnalyzer


@dataclass
class Alert:
    timestamp: str
    session_id: str
    alert_type: str  # "CHAT" or "VIDEO"
    severity: str    # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    category: str    # "PROFANITY", "PERSONAL_INFO", "UNSAFE_LANGUAGE", etc.
    message: str
    confidence: float
    details: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)


class SafetyAlertSystem:
    """Centralized safety monitoring and alert system."""
    
    def __init__(self, log_dir: str = "logs"):
        self.chat_analyzer = ChatAnalyzer()
        self.video_analyzer = VideoAnalyzer()
        self.alerts: List[Alert] = []
        self.log_dir = log_dir
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize log file
        self.log_file = os.path.join(log_dir, f"safety_log_{self.session_id}.json")
        self._initialize_log()
    
    def _initialize_log(self):
        """Initialize the safety log file."""
        log_data = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "alerts": [],
            "statistics": {
                "total_messages": 0,
                "total_videos": 0,
                "total_alerts": 0,
                "chat_alerts": 0,
                "video_alerts": 0
            }
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def _log_alert(self, alert: Alert):
        """Log an alert to file and memory."""
        self.alerts.append(alert)
        
        # Update log file
        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            log_data["alerts"].append(alert.to_dict())
            
            # Update statistics
            stats = log_data["statistics"]
            stats["total_alerts"] += 1
            
            if alert.alert_type == "CHAT":
                stats["chat_alerts"] += 1
            elif alert.alert_type == "VIDEO":
                stats["video_alerts"] += 1
            
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"❌ Error logging alert: {str(e)}")
    
    def analyze_chat_message(self, message: str, user_id: str = "unknown") -> Dict:
        """
        Analyze a chat message for safety concerns.
        
        Args:
            message: The chat message text
            user_id: ID of the user who sent the message
            
        Returns:
            Dictionary with analysis results and any alerts
        """
        result = self.chat_analyzer.analyze(message)
        
        response = {
            "is_safe": result.is_safe,
            "message": message,
            "timestamp": result.timestamp,
            "flags": []
        }
        
        # Generate alerts for each flag
        for flag in result.flags:
            # Determine severity based on category and confidence
            if flag.category == "PERSONAL_INFO":
                severity = "CRITICAL"
            elif flag.category == "UNSAFE_LANGUAGE" and flag.confidence > 0.9:
                severity = "HIGH"
            elif flag.category == "PROFANITY":
                severity = "MEDIUM"
            else:
                severity = "LOW"
            
            alert = Alert(
                timestamp=datetime.now().isoformat(),
                session_id=self.session_id,
                alert_type="CHAT",
                severity=severity,
                category=flag.category,
                message=f"User {user_id}: {message[:100]}",
                confidence=flag.confidence,
                details={
                    "user_id": user_id,
                    "matched_text": flag.matched,
                    "reason": flag.reason
                }
            )
            
            self._log_alert(alert)
            
            response["flags"].append({
                "category": flag.category,
                "reason": flag.reason,
                "confidence": flag.confidence,
                "severity": severity
            })
        
        # Print immediate alert if unsafe
        if not result.is_safe:
            print(f"\n{'='*60}")
            print(f"🚨 CHAT SAFETY ALERT - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            print(f"User: {user_id}")
            print(f"Message: {message}")
            print(f"\n⚠️ Issues Detected:")
            for flag in result.flags:
                print(f"  • [{flag.category}] {flag.reason} (Confidence: {flag.confidence:.0%})")
            print(f"{'='*60}\n")
        
        return response
    
    def analyze_video(self, video_path: str) -> Dict:
        """
        Analyze a video file for safety concerns.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video analysis results and alerts
        """
        if not os.path.exists(video_path):
            return {"error": f"Video file not found: {video_path}"}
        
        print(f"\n🎬 Starting video analysis: {os.path.basename(video_path)}")
        
        # Analyze video
        result = self.video_analyzer.analyze_video(video_path, max_frames=30, include_transcript=True)
        
        response = {
            "video_path": video_path,
            "overall_safety": result.overall_safety,
            "total_frames": result.total_frames,
            "safe_frames": result.safe_frames,
            "unsafe_frames": result.unsafe_frames,
            "transcript": result.transcript,
            "frame_alerts": [],
            "transcript_alerts": []
        }
        
        # Generate alerts for unsafe frames
        if result.unsafe_frames > 0:
            severity = "HIGH" if result.unsafe_frames > result.safe_frames else "MEDIUM"
            
            for frame_analysis in result.frame_analyses:
                if not frame_analysis.is_safe:
                    alert = Alert(
                        timestamp=datetime.now().isoformat(),
                        session_id=self.session_id,
                        alert_type="VIDEO",
                        severity=severity,
                        category="VISUAL_CONTENT",
                        message=f"Unsafe visual content in frame {frame_analysis.frame_number}",
                        confidence=frame_analysis.confidence,
                        details={
                            "frame_number": frame_analysis.frame_number,
                            "timestamp_in_video": frame_analysis.timestamp,
                            "reasons": frame_analysis.reasons
                        }
                    )
                    
                    self._log_alert(alert)
                    
                    response["frame_alerts"].append({
                        "frame_number": frame_analysis.frame_number,
                        "timestamp": frame_analysis.timestamp,
                        "reasons": frame_analysis.reasons,
                        "confidence": frame_analysis.confidence
                    })
        
        # Generate alerts for transcript
        if result.transcript and not result.transcript_analysis.get('is_safe', True):
            for flag in result.transcript_analysis.get('flags', []):
                alert = Alert(
                    timestamp=datetime.now().isoformat(),
                    session_id=self.session_id,
                    alert_type="VIDEO",
                    severity="HIGH" if flag['confidence'] > 0.9 else "MEDIUM",
                    category=flag['category'],
                    message=f"Unsafe language in video transcript: {result.transcript[:50]}...",
                    confidence=flag['confidence'],
                    details={
                        "reason": flag['reason'],
                        "transcript_excerpt": result.transcript[:100]
                    }
                )
                
                self._log_alert(alert)
                
                response["transcript_alerts"].append({
                    "category": flag['category'],
                    "reason": flag['reason'],
                    "confidence": flag['confidence']
                })
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 VIDEO ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"Overall Safety: {result.overall_safety}")
        print(f"Safe Frames: {result.safe_frames}/{result.total_frames}")
        
        if result.unsafe_frames > 0:
            print(f"\n⚠️ {result.unsafe_frames} UNSAFE FRAMES DETECTED:")
            for alert in response["frame_alerts"][:5]:  # Show first 5
                print(f"  • Frame {alert['frame_number']} ({alert['timestamp']}s)")
                for reason in alert['reasons']:
                    print(f"    - {reason}")
        
        if response["transcript_alerts"]:
            print(f"\n⚠️ TRANSCRIPT ISSUES:")
            for alert in response["transcript_alerts"]:
                print(f"  • [{alert['category']}] {alert['reason']}")
        
        print(f"{'='*60}\n")
        
        return response
    
    def get_statistics(self) -> Dict:
        """Get current session statistics."""
        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            return log_data["statistics"]
        except Exception as e:
            return {"error": str(e)}
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get most recent alerts."""
        return [alert.to_dict() for alert in self.alerts[-limit:]]
    
    def export_report(self, output_path: str = None):
        """Export comprehensive safety report."""
        if not output_path:
            output_path = os.path.join(self.log_dir, f"report_{self.session_id}.txt")
        
        stats = self.get_statistics()
        
        with open(output_path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("MELODYWINGS SAFETY MONITORING REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("STATISTICS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Messages Analyzed: {stats.get('total_messages', 0)}\n")
            f.write(f"Total Videos Analyzed: {stats.get('total_videos', 0)}\n")
            f.write(f"Total Alerts Generated: {stats.get('total_alerts', 0)}\n")
            f.write(f"  - Chat Alerts: {stats.get('chat_alerts', 0)}\n")
            f.write(f"  - Video Alerts: {stats.get('video_alerts', 0)}\n\n")
            
            f.write("RECENT ALERTS\n")
            f.write("-" * 60 + "\n")
            
            for alert in self.get_recent_alerts(20):
                f.write(f"\n[{alert['timestamp']}] {alert['severity']} - {alert['category']}\n")
                f.write(f"Type: {alert['alert_type']}\n")
                f.write(f"Message: {alert['message'][:100]}\n")
                f.write(f"Confidence: {alert['confidence']:.0%}\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 60 + "\n")
        
        print(f"✅ Report exported to: {output_path}")
        return output_path


# ── Demo/Test Functions ───────────────────────────────────────────────────────

def demo_chat_monitoring():
    """Demonstrate real-time chat monitoring."""
    print("\n" + "=" * 60)
    print("  MELODYWINGS CHAT SAFETY MONITORING DEMO")
    print("=" * 60)
    print("\nType chat messages to analyze. Type 'quit' to exit.\n")
    
    alert_system = SafetyAlertSystem()
    
    test_messages = [
        ("user1", "Hey! Nice to meet you!"),
        ("user2", "My phone number is 555-123-4567"),
        ("user1", "This is damn frustrating!"),
        ("user2", "I live at 123 Main Street, Springfield"),
        ("user1", "Let's work on our project together"),
        ("user2", "I hate this stupid platform"),
        ("user1", "You're an idiot if you think that"),
        ("user2", "I want to hurt you"),
    ]
    
    print("Running automated demo with test messages...\n")
    
    for user_id, message in test_messages:
        input(f"Press Enter to send message from {user_id}: {message}")
        result = alert_system.analyze_chat_message(message, user_id)
        
        if result['is_safe']:
            print("✅ Message is SAFE")
        else:
            print(f"⚠️ FLAGGED: {len(result['flags'])} issues detected")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print(f"Total alerts generated: {len(alert_system.alerts)}")
    print("=" * 60)


if __name__ == "__main__":
    demo_chat_monitoring()
