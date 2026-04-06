"""
Test script for video audio extraction and toxic speech detection.
This script tests the complete pipeline:
1. Extract audio from video
2. Transcribe audio to text
3. Analyze transcribed text for toxicity
4. Combine visual and audio analysis
"""

import os
from video_analyser import VideoAnalyzer, MOVIEPY_AVAILABLE, SPEECH_RECOGNITION_AVAILABLE


def test_dependencies():
    """Test if required dependencies are available."""
    print("=" * 60)
    print("DEPENDENCY CHECK")
    print("=" * 60)
    print(f"✅ moviepy available: {MOVIEPY_AVAILABLE}")
    print(f"✅ speech_recognition available: {SPEECH_RECOGNITION_AVAILABLE}")
    
    if not MOVIEPY_AVAILABLE:
        print("\n⚠️ ERROR: moviepy is not installed!")
        print("   Install with: pip install moviepy")
        return False
    
    if not SPEECH_RECOGNITION_AVAILABLE:
        print("\n⚠️ WARNING: speech_recognition is not available")
        print("   Audio transcription will not work")
    
    print()
    return True


def test_audio_extraction(video_path):
    """Test audio extraction from video."""
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return None
    
    analyzer = VideoAnalyzer()
    
    print("=" * 60)
    print("TEST 1: AUDIO EXTRACTION")
    print("=" * 60)
    print(f"Video: {os.path.basename(video_path)}")
    
    try:
        # Test audio extraction
        audio_path, transcript = analyzer.extract_audio_transcript(video_path)
        print(f"✅ Audio extracted to: {os.path.basename(audio_path)}")
        print(f"✅ Transcript: {transcript[:200]}...")
        
        # Clean up extracted audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"🧹 Cleaned up temporary audio file")
        
        return transcript
        
    except Exception as e:
        print(f"❌ Audio extraction failed: {str(e)}")
        return None


def test_full_analysis(video_path):
    """Test complete video analysis with audio transcription."""
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    analyzer = VideoAnalyzer()
    
    print("\n" + "=" * 60)
    print("TEST 2: FULL VIDEO ANALYSIS (Visual + Audio)")
    print("=" * 60)
    
    try:
        # Run complete analysis
        result = analyzer.analyze_video(video_path, max_frames=30, include_transcript=True)
        
        print("\n" + "=" * 60)
        print("FINAL RESULT")
        print("=" * 60)
        print(f"Overall Risk: {result.overall_safety}")
        print(f"Visual: {result.unsafe_frames}/{result.total_frames} unsafe frames")
        
        if result.transcript and not result.transcript.startswith('[Error'):
            print(f"\nTranscription:")
            print(f"   {result.transcript[:200]}...")
            
            toxic_words = result.transcript_analysis.get('toxic_words', [])
            if toxic_words:
                print(f"\n⚠️ TOXIC WORDS DETECTED: {', '.join(toxic_words)}")
            
            transcript_safe = result.transcript_analysis.get('is_safe', True)
            print(f"Transcript Safety: {'✅ SAFE' if transcript_safe else '⚠️ UNSAFE'}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main test function."""
    print("\n" + "═" * 60)
    print("  MelodyWings Video Audio & Toxicity Test")
    print("═" * 60 + "\n")
    
    # Check dependencies
    if not test_dependencies():
        print("\n❌ Cannot proceed - missing dependencies")
        return
    
    # Ask for video file
    video_path = input("\nEnter video file path (or press Enter for sample): ").strip()
    
    if not video_path:
        # Try to find a sample video in the uploads folder
        sample_paths = [
            "uploads/test.mp4",
            "uploads/sample.mp4",
            "test_video.mp4"
        ]
        for path in sample_paths:
            if os.path.exists(path):
                video_path = path
                break
    
    if not video_path or not os.path.exists(video_path):
        print("\n❌ No valid video file found")
        print("\nTo test, please:")
        print("1. Place a video file in the 'uploads' folder")
        print("2. Run this script again and provide the path")
        return
    
    # Test 1: Audio extraction only
    transcript = test_audio_extraction(video_path)
    
    if transcript:
        print("\n✅ Audio extraction test PASSED\n")
    else:
        print("\n❌ Audio extraction test FAILED\n")
        return
    
    # Test 2: Full analysis
    test_full_analysis(video_path)
    
    print("\n✅ All tests completed!\n")


if __name__ == "__main__":
    main()
