"""
MelodyWings Video Analyzer
---------------------------
Analyzes video content for safety concerns:
- Extracts frames using OpenCV
- Detects inappropriate visual content
- Analyzes audio transcript for unsafe language
- Provides frame-by-frame safety assessment
"""

import cv2
import os
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional

# TASK 1: Import moviepy for audio extraction
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    VideoFileClip = None

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None


@dataclass
class FrameAnalysis:
    frame_number: int
    timestamp: str
    is_safe: bool
    confidence: float
    reasons: List[str] = field(default_factory=list)
    frame_data: Optional[np.ndarray] = None  # For potential thumbnail generation


@dataclass
class VideoAnalysisResult:
    video_path: str
    total_frames: int
    safe_frames: int
    unsafe_frames: int
    frame_analyses: List[FrameAnalysis] = field(default_factory=list)
    transcript: str = ""
    transcript_analysis: dict = field(default_factory=dict)
    
    @property
    def overall_safety(self) -> str:
        """
        TASK 5: Calculate overall safety rating combining visual and audio/text analysis.
        
        Final Decision Logic:
        - If text is unsafe OR visual is unsafe → HIGH RISK
        - Otherwise → LOW RISK
        """
        # Check if transcript analysis exists and is unsafe
        transcript_unsafe = False
        if self.transcript_analysis:
            transcript_unsafe = not self.transcript_analysis.get('is_safe', True)
        
        # Check visual safety
        visual_unsafe = self.unsafe_frames > 0
        
        # TASK 5: Combined decision - if EITHER is unsafe, overall is HIGH RISK
        if transcript_unsafe or visual_unsafe:
            if transcript_unsafe and visual_unsafe:
                return "HIGH RISK (Visual + Audio)"
            elif transcript_unsafe:
                return "HIGH RISK (Audio)"
            else:
                return "HIGH RISK (Visual)"
        
        # Both are safe
        return "SAFE"
    
    def summary(self) -> str:
        """TASK 6: Enhanced summary with transcription and toxic word detection."""
        lines = [
            f"\n{'='*60}",
            f"🎬 Video Analysis Report (with Audio Transcription)",
            f"{'='*60}",
            f"File: {self.video_path}",
            f"Total Frames: {self.total_frames}",
            f"Safe Frames: {self.safe_frames} ✅",
            f"Unsafe Frames: {self.unsafe_frames} ⚠️",
            f"🔴 OVERALL SAFETY: {self.overall_safety}",
            f"{'='*60}"
        ]
        
        # Display transcription (TASK 6)
        if self.transcript and not self.transcript.startswith('[Error'):
            lines.append(f"\n📝 TRANSCRIPTION:")
            lines.append(f"   {self.transcript[:300]}{'...' if len(self.transcript) > 300 else ''}")
            
            # Display toxic words detected (TASK 6)
            if self.transcript_analysis:
                toxic_words = self.transcript_analysis.get('toxic_words', [])
                if toxic_words:
                    lines.append(f"\n⚠️ DETECTED TOXIC WORDS: {', '.join(toxic_words)}")
                
                is_safe = self.transcript_analysis.get('is_safe', True)
                lines.append(f"📊 TRANSCRIPT SAFETY: {'✅ SAFE' if is_safe else '⚠️ UNSAFE'}")
                
                if not is_safe and self.transcript_analysis.get('flags'):
                    lines.append(f"\n🚩 FLAGS:")
                    for flag in self.transcript_analysis['flags']:
                        lines.append(f"   - [{flag['category']}] {flag['reason']} (confidence: {flag['confidence']:.2f})")
        
        elif self.transcript:
            lines.append(f"\n⚠️ Transcription Error: {self.transcript}")
        
        lines.append(f"\n{'='*60}")
        return "\n".join(lines)


class VideoAnalyzer:
    """Video content safety analyzer with audio transcription."""
    
    def __init__(self):
        # Check for required dependencies
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
            
        if not MOVIEPY_AVAILABLE:
            print("⚠️ moviepy not available - audio extraction will be limited")
        
        # Simple color/motion-based heuristics for demo
        # In production, replace with actual ML models
        self.skin_color_lower = np.array([0, 48, 0])
        self.skin_color_upper = np.array([20, 255, 255])
        
    def extract_frames(self, video_path: str, max_frames: int = 30) -> List[tuple]:
        """Extract frames from video at regular intervals."""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        # Calculate frame interval to sample evenly
        frame_interval = max(1, total_frames // max_frames)
        
        frame_count = 0
        sampled_count = 0
        
        while sampled_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                frames.append((sampled_count, frame, timestamp))
                sampled_count += 1
            
            frame_count += 1
        
        cap.release()
        return frames
    
    def analyze_frame(self, frame: np.ndarray, frame_num: int, timestamp: float) -> FrameAnalysis:
        """
        Analyze a single frame for safety concerns.
        
        Uses simple heuristics with IMPROVED ACCURACY:
        - Higher thresholds to reduce false positives
        - Multiple conditions required for flagging
        - Conservative approach
        
        In production, replace with pretrained NSFW detection models.
        """
        reasons = []
        confidence = 0.0
        is_safe = True
        
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Skin tone detection (very basic heuristic)
        mask = cv2.inRange(hsv, self.skin_color_lower, self.skin_color_upper)
        skin_percentage = np.sum(mask > 0) / mask.size
        
        # Analyze brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        
        # Analyze contrast
        contrast = np.std(gray)
        
        # Analyze blur (motion detection)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # IMPROVED Heuristic rules - HIGHER THRESHOLDS
        # Only flag if MULTIPLE indicators present
        
        skin_flag = False
        motion_flag = False
        lighting_flag = False
        
        # Skin detection: Much higher threshold (>60% instead of >40%)
        if skin_percentage > 0.6:
            skin_flag = True
            reasons.append("High skin exposure detected")
            confidence = min(0.7, skin_percentage * 1.2)
            is_safe = False
        
        # Very dark conditions: Lowered sensitivity
        if avg_brightness < 20:  # Was 30
            lighting_flag = True
            reasons.append("Very low lighting conditions")
            confidence = max(confidence, 0.25)
        
        # Motion detection: More conservative
        if laplacian_var < 50:  # Was 100 - less sensitive
            motion_flag = True
            reasons.append("Rapid motion detected")
            confidence = max(confidence, 0.3)
        
        # ONLY flag as unsafe if at least 2 indicators OR very strong single indicator
        if skin_flag and (motion_flag or lighting_flag):
            # Multiple red flags - more confident it's real
            confidence = max(confidence, 0.65)
            reasons.append("Multiple concerning visual indicators")
        elif not skin_flag:
            # No skin detection alone is not enough to flag
            is_safe = True
            confidence = min(confidence, 0.4)
        
        # Content warnings: Much higher threshold
        if contrast > 100 and avg_brightness > 220:  # Was 80 and 200
            reasons.append("Potentially disturbing visual content")
            confidence = max(confidence, 0.4)
        
        ts = datetime.now().strftime("%H:%M:%S")
        
        return FrameAnalysis(
            frame_number=frame_num,
            timestamp=f"{timestamp:.2f}s",
            is_safe=is_safe,
            confidence=confidence,
            reasons=reasons
        )
    
    def extract_audio(self, video_path: str) -> str:
        """
        TASK 1: Extract audio from video using moviepy.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file (.wav)
        """
        if not MOVIEPY_AVAILABLE:
            raise Exception("moviepy not available - please install: pip install moviepy")
        
        try:
            # Extract audio path from video path
            audio_path = video_path.rsplit('.', 1)[0] + '_extracted.wav'
            
            # Load video and extract audio
            clip = VideoFileClip(video_path)
            
            # Write audio to WAV file
            if clip.audio is not None:
                clip.audio.write_audiofile(audio_path, codec='pcm_s16le')
                clip.close()
                return audio_path
            else:
                clip.close()
                raise Exception("Video has no audio track")
                
        except Exception as e:
            raise Exception(f"Audio extraction failed: {str(e)}")
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        TASK 2: Transcribe audio file to text using SpeechRecognition.
        
        Args:
            audio_path: Path to audio file (.wav)
            
        Returns:
            Transcribed text
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            return "[Speech recognition not available]"
        
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
                try:
                    # Use Google Speech Recognition
                    transcript = self.recognizer.recognize_google(audio)
                    return transcript
                except sr.UnknownValueError:
                    return "[Speech could not be recognized]"
                except sr.RequestError as e:
                    return f"[Speech recognition error: {str(e)}]"
        except Exception as e:
            return f"[Transcription error: {str(e)}]"
    
    def extract_audio_transcript(self, video_path: str) -> tuple:
        """
        Complete audio extraction and transcription pipeline.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (audio_path, transcript_text)
        """
        # Step 1: Extract audio from video
        audio_path = self.extract_audio(video_path)
        
        # Step 2: Transcribe audio to text
        transcript = self.transcribe_audio(audio_path)
        
        return audio_path, transcript
    
    def analyze_video(self, video_path: str, max_frames: int = 30, 
                     include_transcript: bool = True) -> VideoAnalysisResult:
        """
        Complete video analysis pipeline.
        
        Args:
            video_path: Path to video file
            max_frames: Maximum frames to sample
            include_transcript: Whether to extract and analyze audio transcript
            
        Returns:
            VideoAnalysisResult with comprehensive analysis
        """
        print(f"\n🎬 Analyzing video: {os.path.basename(video_path)}")
        print("=" * 60)
        
        # Extract frames
        print("📸 Extracting frames...")
        frames = self.extract_frames(video_path, max_frames)
        print(f"✅ Extracted {len(frames)} frames")
        
        # Analyze each frame
        print("🔍 Analyzing frames for safety...")
        frame_analyses = []
        safe_count = 0
        unsafe_count = 0
        
        for frame_num, frame, timestamp in frames:
            analysis = self.analyze_frame(frame, frame_num, timestamp)
            frame_analyses.append(analysis)
            
            if analysis.is_safe:
                safe_count += 1
            else:
                unsafe_count += 1
            
            # Progress indicator
            if (frame_num + 1) % 10 == 0:
                print(f"  Analyzed {frame_num + 1}/{len(frames)} frames...")
        
        print(f"✅ Frame analysis complete: {safe_count} safe, {unsafe_count} unsafe")
        
        # Extract and analyze transcript (TASK 3 & TASK 4)
        transcript = ""
        transcript_analysis = {}
        audio_path = None
        
        if include_transcript:
            print("🎤 Extracting audio from video...")
            try:
                # Step 1: Extract audio from video
                audio_path, transcript = self.extract_audio_transcript(video_path)
                print(f"✅ Audio extracted to: {os.path.basename(audio_path)}")
                print(f"✅ Transcript: {transcript[:100]}...")
                
                # Step 2: Analyze transcribed text for toxicity (TASK 3)
                print("🔍 Analyzing transcript for toxic content...")
                from chat_analyser import ChatAnalyzer
                chat_analyzer = ChatAnalyzer()
                result = chat_analyzer.analyze(transcript)
                
                transcript_analysis = {
                    'is_safe': result.is_safe,
                    'toxic_words': result.toxic_words if hasattr(result, 'toxic_words') else [],
                    'flags': [
                        {
                            'category': flag.category,
                            'reason': flag.reason,
                            'confidence': flag.confidence
                        }
                        for flag in result.flags
                    ]
                }
                
                if not result.is_safe:
                    print(f"⚠️ Transcript contains unsafe content!")
                    if result.toxic_words:
                        print(f"   Toxic words detected: {', '.join(result.toxic_words)}")
                        
            except Exception as e:
                print(f"⚠️ Audio extraction/transcription failed: {str(e)}")
                transcript = f"[Error: {str(e)}]"
        
        # Create result
        video_result = VideoAnalysisResult(
            video_path=video_path,
            total_frames=len(frame_analyses),
            safe_frames=safe_count,
            unsafe_frames=unsafe_count,
            frame_analyses=frame_analyses,
            transcript=transcript,
            transcript_analysis=transcript_analysis
        )
        
        print(video_result.summary())
        return video_result


# ── Demo/Test Functions ───────────────────────────────────────────────────────

def test_video_analysis(video_path: str):
    """Test video analysis on a specific video file."""
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    analyzer = VideoAnalyzer()
    result = analyzer.analyze_video(video_path, max_frames=30, include_transcript=True)
    
    print("\n" + "=" * 60)
    print("🔴 FINAL SAFETY ASSESSMENT")
    print("=" * 60)
    print(f"OVERALL RISK LEVEL: {result.overall_safety}")
    print(f"Visual Analysis: {result.unsafe_frames}/{result.total_frames} unsafe frames")
    
    # TASK 6: Display transcript and toxic words
    if result.transcript and not result.transcript.startswith('[Error'):
        print(f"\n📝 TRANSCRIPTION:")
        print(f"   {result.transcript[:200]}{'...' if len(result.transcript) > 200 else ''}")
        
        toxic_words = result.transcript_analysis.get('toxic_words', [])
        if toxic_words:
            print(f"\n⚠️ DETECTED TOXIC WORDS: {', '.join(toxic_words)}")
        
        transcript_safety = result.transcript_analysis.get('is_safe', True)
        print(f"Transcript Safety: {'✅ SAFE' if transcript_safety else '⚠️ UNSAFE'}")
    
    # Visual alerts
    if result.unsafe_frames > 0:
        print("\n⚠️ VISUAL SAFETY ALERTS:")
        for analysis in result.frame_analyses:
            if not analysis.is_safe:
                print(f"  Frame {analysis.frame_number} ({analysis.timestamp}s):")
                for reason in analysis.reasons:
                    print(f"    - {reason}")
    
    # Transcript alerts
    if result.transcript and not result.transcript_analysis.get('is_safe', True):
        print("\n⚠️ TRANSCRIPT ALERTS:")
        for flag in result.transcript_analysis['flags']:
            print(f"  [{flag['category']}] {flag['reason']} (confidence: {flag['confidence']:.2f})")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Interactive demo
    print("\n" + "═" * 60)
    print("  MelodyWings Video Safety Analyzer")
    print("═" * 60)
    
    video_path = input("\nEnter video file path: ").strip()
    
    if video_path:
        test_video_analysis(video_path)
    else:
        print("❌ No video path provided")
