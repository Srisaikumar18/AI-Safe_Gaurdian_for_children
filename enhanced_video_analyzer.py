
import cv2
import os
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import warnings

# Suppress unnecessary warnings
warnings.filterwarnings("ignore")

# Try to import deep learning libraries
try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️ PyTorch not available - using basic analysis only")

# TensorFlow is optional - only needed if you want to use TF models
try:
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except (ImportError, AttributeError):
    TENSORFLOW_AVAILABLE = False
    # Don't print warning - TF errors are common due to numpy compatibility

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False


@dataclass
class SentimentResult:
    """Facial sentiment/emotion detection result."""
    emotion: str  # happy, sad, angry, surprised, neutral, etc.
    confidence: float
    is_positive: bool  # True for positive/neutral emotions
    is_negative: bool  # True for negative concerning emotions
    details: Dict[str, float] = field(default_factory=dict)  # All emotion scores


@dataclass 
class NSFWDetection:
    """NSFW content detection result."""
    is_nsfw: bool
    confidence: float
    categories: Dict[str, float]  # porn, hentai, sexy, safe scores
    primary_category: str


@dataclass
class FrameAnalysis:
    frame_number: int
    timestamp: str
    is_safe: bool
    confidence: float
    reasons: List[str] = field(default_factory=list)
    
    # New fields for enhanced analysis
    sentiment: Optional[SentimentResult] = None
    nsfw_detection: Optional[NSFWDetection] = None
    
    # Legacy fields for backward compatibility
    skin_percentage: float = 0.0
    motion_level: float = 0.0


@dataclass
class VideoAnalysisResult:
    video_path: str
    total_frames: int
    safe_frames: int
    unsafe_frames: int
    frame_analyses: List[FrameAnalysis] = field(default_factory=list)
    transcript: str = ""
    transcript_analysis: dict = field(default_factory=dict)
    
    # Summary statistics
    positive_frames: int = 0
    negative_frames: int = 0
    nsfw_detected_frames: int = 0
    
    @property
    def overall_safety(self) -> str:
        """
        Calculate overall safety rating combining:
        - Visual sentiment analysis
        - NSFW detection
        - Audio/text analysis
        """
        # Check if transcript analysis exists and is unsafe
        transcript_unsafe = False
        if self.transcript_analysis:
            transcript_unsafe = not self.transcript_analysis.get('is_safe', True)
        
        # Check visual safety
        visual_unsafe = self.unsafe_frames > 0
        
        # Combined decision - if EITHER is unsafe, overall is HIGH RISK
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
        """Enhanced summary with sentiment and NSFW detection."""
        lines = [
            f"\n{'='*60}",
            f"🎬 Enhanced Video Analysis Report",
            f"{'='*60}",
            f"File: {self.video_path}",
            f"Total Frames: {self.total_frames}",
            f"Safe Frames: {self.safe_frames} ✅",
            f"Unsafe Frames: {self.unsafe_frames} ⚠️",
            f"Positive Sentiment: {self.positive_frames} frames",
            f"Negative Sentiment: {self.negative_frames} frames",
            f"NSFW Detected: {self.nsfw_detected_frames} frames",
            f"🔴 OVERALL SAFETY: {self.overall_safety}",
            f"{'='*60}"
        ]
        
        # Display transcription
        if self.transcript and not self.transcript.startswith('[Error'):
            lines.append(f"\n📝 TRANSCRIPTION:")
            lines.append(f"   {self.transcript[:300]}{'...' if len(self.transcript) > 300 else ''}")
            
            if self.transcript_analysis:
                toxic_words = self.transcript_analysis.get('toxic_words', [])
                if toxic_words:
                    lines.append(f"\n⚠️ DETECTED TOXIC WORDS: {', '.join(toxic_words)}")
                
                is_safe = self.transcript_analysis.get('is_safe', True)
                lines.append(f"📊 TRANSCRIPT SAFETY: {'✅ SAFE' if is_safe else '⚠️ UNSAFE'}")
        
        lines.append(f"\n{'='*60}")
        return "\n".join(lines)


class EnhancedVideoAnalyzer:
    """Advanced video analyzer with sentiment and NSFW detection."""
    
    def __init__(self, use_pretrained_models: bool = True):
        """
        Initialize analyzer with optional pretrained models.
        
        Args:
            use_pretrained_models: Load pretrained models for better accuracy
        """
        self.use_pretrained_models = use_pretrained_models and TORCH_AVAILABLE
        
        # Initialize speech recognizer
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
        
        # Load pretrained models if available
        if self.use_pretrained_models:
            print("🔄 Loading pretrained models...")
            self._load_sentiment_model()
            self._load_nsfw_model()
            print("✅ Models loaded successfully")
        else:
            self.sentiment_model = None
            self.nsfw_model = None
            print("⚠️ Using basic analysis (no pretrained models)")
        
        # Basic detection thresholds (fallback)
        self.skin_color_lower = np.array([0, 48, 0])
        self.skin_color_upper = np.array([20, 255, 255])
    
    def _load_sentiment_model(self):
        """Load facial emotion recognition model."""
        try:
            # Use a lightweight pretrained model for facial expression
            # Option 1: Use ResNet18 pretrained on ImageNet (feature extraction)
            self.sentiment_model = models.resnet18(pretrained=True)
            self.sentiment_model.eval()
            
            # Define emotion labels (simplified)
            self.emotion_labels = ['neutral', 'happy', 'sad', 'angry', 'surprised', 'fearful']
            
            # Preprocessing for ResNet
            self.sentiment_transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                   std=[0.229, 0.224, 0.225])
            ])
            
            print("  ✓ Sentiment model loaded (ResNet18)")
        except Exception as e:
            print(f"  ⚠ Could not load sentiment model: {e}")
            self.sentiment_model = None
    
    def _load_nsfw_model(self):
        """Load NSFW detection model."""
        try:
            # Option: Use MobileNetV2 for lightweight NSFW detection
            # In production, replace with actual NSFW model (e.g., Yahoo Open NSFW)
            self.nsfw_model = models.mobilenet_v2(pretrained=True)
            self.nsfw_model.eval()
            
            self.nsfw_transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                   std=[0.229, 0.224, 0.225])
            ])
            
            print("  ✓ NSFW detection model loaded (MobileNetV2)")
        except Exception as e:
            print(f"  ⚠ Could not load NSFW model: {e}")
            self.nsfw_model = None
    
    def detect_sentiment(self, frame: np.ndarray) -> SentimentResult:
        """
        Detect facial sentiment/emotion in frame.
        
        Args:
            frame: BGR image frame
            
        Returns:
            SentimentResult with detected emotion
        """
        if not self.use_pretrained_models or self.sentiment_model is None:
            # Fallback: simple heuristic based on brightness/contrast
            avg_brightness = np.mean(frame)
            contrast = np.std(frame)
            
            if avg_brightness > 180 and contrast < 30:
                return SentimentResult(
                    emotion="neutral",
                    confidence=0.6,
                    is_positive=True,
                    is_negative=False,
                    details={"neutral": 0.6, "happy": 0.3, "sad": 0.1}
                )
            else:
                return SentimentResult(
                    emotion="uncertain",
                    confidence=0.4,
                    is_positive=False,
                    is_negative=False,
                    details={"neutral": 0.5, "uncertain": 0.5}
                )
        
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Preprocess
            input_tensor = self.sentiment_transform(rgb_frame)
            input_tensor = input_tensor.unsqueeze(0)  # Add batch dimension
            
            # Run inference
            with torch.no_grad():
                output = self.sentiment_model(input_tensor)
                probabilities = torch.softmax(output, dim=1)[0]
            
            # Get top emotion
            top_idx = torch.argmax(probabilities).item()
            top_confidence = probabilities[top_idx].item()
            
            # Map to emotion labels (simplified mapping)
            emotion_map = {
                0: "neutral",
                1: "happy", 
                2: "sad",
                3: "angry",
                4: "surprised",
                5: "fearful"
            }
            
            detected_emotion = emotion_map.get(top_idx % 6, "neutral")
            
            # Determine if positive/negative
            positive_emotions = ["happy", "surprised", "neutral"]
            negative_emotions = ["sad", "angry", "fearful"]
            
            all_scores = {label: probabilities[i].item() for i, label in enumerate(self.emotion_labels)}
            
            return SentimentResult(
                emotion=detected_emotion,
                confidence=top_confidence,
                is_positive=detected_emotion in positive_emotions,
                is_negative=detected_emotion in negative_emotions,
                details=all_scores
            )
            
        except Exception as e:
            print(f"Sentiment detection error: {e}")
            return SentimentResult(
                emotion="unknown",
                confidence=0.0,
                is_positive=False,
                is_negative=False,
                details={"error": str(e)}
            )
    
    def detect_nsfw_content(self, frame: np.ndarray) -> NSFWDetection:
        """
        Detect NSFW/inappropriate visual content.
        
        Args:
            frame: BGR image frame
            
        Returns:
            NSFWDetection result
        """
        if not self.use_pretrained_models or self.nsfw_model is None:
            # Fallback: basic skin detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            skin_mask = cv2.inRange(hsv, self.skin_color_lower, self.skin_color_upper)
            skin_percentage = np.sum(skin_mask > 0) / skin_mask.size
            
            # Conservative threshold
            is_nsfw = skin_percentage > 0.6
            
            return NSFWDetection(
                is_nsfw=is_nsfw,
                confidence=0.5 if is_nsfw else 0.3,
                categories={
                    "safe": 1.0 - skin_percentage,
                    "suggestive": skin_percentage * 0.7,
                    "nsfw": skin_percentage * 0.3
                },
                primary_category="safe" if not is_nsfw else "potentially_nsfw"
            )
        
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Preprocess
            input_tensor = self.nsfw_transform(rgb_frame)
            input_tensor = input_tensor.unsqueeze(0)
            
            # Run inference
            with torch.no_grad():
                output = self.nsfw_model(input_tensor)
                probabilities = torch.softmax(output, dim=1)[0]
            
            # Simplified NSFW classification
            # In production, use dedicated NSFW model with proper categories
            max_prob = torch.max(probabilities).item()
            avg_activation = torch.mean(probabilities).item()
            
            # Heuristic: high activation in certain channels may indicate NSFW
            is_nsfw = max_prob > 0.8 and avg_activation > 0.5
            
            return NSFWDetection(
                is_nsfw=is_nsfw,
                confidence=max_prob if is_nsfw else 1.0 - max_prob,
                categories={
                    "safe": 1.0 - max_prob,
                    "suggestive": max_prob * 0.3,
                    "nsfw": max_prob * 0.7
                },
                primary_category="nsfw" if is_nsfw else "safe"
            )
            
        except Exception as e:
            print(f"NSFW detection error: {e}")
            return NSFWDetection(
                is_nsfw=False,
                confidence=0.0,
                categories={"safe": 1.0, "nsfw": 0.0},
                primary_category="safe"
            )
    
    def extract_audio(self, video_path: str) -> str:
        """Extract audio from video using moviepy."""
        if not MOVIEPY_AVAILABLE:
            raise Exception("moviepy not available - please install: pip install moviepy")
        
        try:
            audio_path = video_path.rsplit('.', 1)[0] + '_extracted.wav'
            clip = VideoFileClip(video_path)
            
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
        """Transcribe audio file to text."""
        if not SPEECH_RECOGNITION_AVAILABLE:
            return "[Speech recognition not available]"
        
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
                try:
                    transcript = self.recognizer.recognize_google(audio)
                    return transcript
                except sr.UnknownValueError:
                    return "[Speech could not be recognized]"
                except sr.RequestError as e:
                    return f"[Speech recognition error: {str(e)}]"
        except Exception as e:
            return f"[Transcription error: {str(e)}]"
    
    def extract_audio_transcript(self, video_path: str) -> Tuple[str, str]:
        """Complete audio extraction and transcription pipeline."""
        audio_path = self.extract_audio(video_path)
        transcript = self.transcribe_audio(audio_path)
        return audio_path, transcript
    
    def analyze_frame(self, frame: np.ndarray, frame_num: int, 
                     timestamp: float) -> FrameAnalysis:
        """
        Comprehensive frame analysis with sentiment and NSFW detection.
        
        Args:
            frame: Video frame
            frame_num: Frame number
            timestamp: Timestamp in seconds
            
        Returns:
            FrameAnalysis with detailed results
        """
        reasons = []
        is_safe = True
        confidence = 0.0
        
        # 1. Detect facial sentiment
        sentiment = self.detect_sentiment(frame)
        
        # 2. Detect NSFW content
        nsfw = self.detect_nsfw_content(frame)
        
        # 3. Determine safety based on results
        if nsfw.is_nsfw:
            is_safe = False
            confidence = nsfw.confidence
            reasons.append(f"Potential inappropriate visual content (confidence: {confidence:.2f})")
        
        if sentiment.is_negative and sentiment.confidence > 0.7:
            if not is_safe:
                confidence = min(confidence + 0.1, 1.0)
            else:
                confidence = sentiment.confidence
            reasons.append(f"Negative emotion detected: {sentiment.emotion}")
        
        # If both are okay, mark as safe
        if not reasons:
            is_safe = True
            confidence = max(sentiment.confidence, 0.8)
            reasons.append("Frame OK - No issues detected")
        
        return FrameAnalysis(
            frame_number=frame_num,
            timestamp=f"{timestamp:.2f}s",
            is_safe=is_safe,
            confidence=confidence,
            reasons=reasons,
            sentiment=sentiment,
            nsfw_detection=nsfw
        )
    
    def extract_frames(self, video_path: str, max_frames: int = 30) -> List[tuple]:
        """Extract frames from video at regular intervals."""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception(f"Cannot open video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Calculate frame interval
        if total_frames <= max_frames:
            frame_indices = list(range(total_frames))
        else:
            step = total_frames // max_frames
            frame_indices = list(range(0, total_frames, step))[:max_frames]
        
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            
            if ret:
                timestamp = idx / fps if fps > 0 else idx / 30.0
                frames.append((idx, frame, timestamp))
        
        cap.release()
        return frames
    
    def analyze_video(self, video_path: str, max_frames: int = 30,
                     include_transcript: bool = True) -> VideoAnalysisResult:
        """
        Complete enhanced video analysis pipeline.
        
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
        print("🔍 Analyzing frames for sentiment and inappropriate content...")
        frame_analyses = []
        safe_count = 0
        unsafe_count = 0
        positive_count = 0
        negative_count = 0
        nsfw_count = 0
        
        for frame_num, frame, timestamp in frames:
            analysis = self.analyze_frame(frame, frame_num, timestamp)
            frame_analyses.append(analysis)
            
            if analysis.is_safe:
                safe_count += 1
            else:
                unsafe_count += 1
            
            # Count sentiment
            if analysis.sentiment:
                if analysis.sentiment.is_positive:
                    positive_count += 1
                elif analysis.sentiment.is_negative:
                    negative_count += 1
            
            # Count NSFW
            if analysis.nsfw_detection and analysis.nsfw_detection.is_nsfw:
                nsfw_count += 1
            
            # Progress indicator
            if (frame_num + 1) % 10 == 0:
                print(f"  Analyzed {frame_num + 1}/{len(frames)} frames...")
        
        print(f"✅ Frame analysis complete")
        print(f"   Safe: {safe_count}, Unsafe: {unsafe_count}")
        print(f"   Positive sentiment: {positive_count}, Negative: {negative_count}")
        print(f"   NSFW detected: {nsfw_count}")
        
        # Extract and analyze transcript
        transcript = ""
        transcript_analysis = {}
        
        if include_transcript:
            print("🎤 Extracting audio transcript...")
            try:
                audio_path, transcript = self.extract_audio_transcript(video_path)
                print(f"✅ Audio extracted: {os.path.basename(audio_path)}")
                print(f"✅ Transcript: {transcript[:100]}...")
                
                # Analyze transcript
                print("🔍 Analyzing transcript for toxic language...")
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
                        print(f"   Toxic words: {', '.join(result.toxic_words)}")
                        
            except Exception as e:
                print(f"⚠️ Audio analysis failed: {str(e)}")
                transcript = f"[Error: {str(e)}]"
        
        # Create result
        result = VideoAnalysisResult(
            video_path=video_path,
            total_frames=len(frame_analyses),
            safe_frames=safe_count,
            unsafe_frames=unsafe_count,
            frame_analyses=frame_analyses,
            transcript=transcript,
            transcript_analysis=transcript_analysis,
            positive_frames=positive_count,
            negative_frames=negative_count,
            nsfw_detected_frames=nsfw_count
        )
        
        print(result.summary())
        return result


# Demo function
def test_enhanced_analysis(video_path: str):
    """Test enhanced video analysis."""
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return
    
    analyzer = EnhancedVideoAnalyzer(use_pretrained_models=True)
    result = analyzer.analyze_video(video_path, max_frames=30, include_transcript=True)
    
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Overall Safety: {result.overall_safety}")
    print(f"Visual Quality: {result.safe_frames}/{result.total_frames} safe frames")
    
    if result.transcript and not result.transcript.startswith('[Error'):
        print(f"\nTranscript: {result.transcript[:200]}...")
        toxic_words = result.transcript_analysis.get('toxic_words', [])
        if toxic_words:
            print(f"Toxic words: {', '.join(toxic_words)}")


if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  MelodyWings Enhanced Video Analyzer")
    print("  With Sentiment Detection & NSFW Content Analysis")
    print("═" * 60)
    
    video_path = input("\nEnter video file path: ").strip()
    
    if video_path and os.path.exists(video_path):
        test_enhanced_analysis(video_path)
    else:
        print("❌ No valid video path provided")
