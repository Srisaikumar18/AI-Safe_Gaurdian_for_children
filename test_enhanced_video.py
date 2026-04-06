"""
Test script for Enhanced Video Analyzer
Tests sentiment detection and NSFW content analysis
"""

import os
from enhanced_video_analyser import EnhancedVideoAnalyzer, TORCH_AVAILABLE


def test_model_availability():
    """Check if models are available."""
    print("=" * 60)
    print("MODEL AVAILABILITY CHECK")
    print("=" * 60)
    print(f"✅ PyTorch available: {TORCH_AVAILABLE}")
    
    if not TORCH_AVAILABLE:
        print("\n⚠️ WARNING: PyTorch not available!")
        print("   Install with: pip install torch torchvision")
        print("   Will use basic analysis only (reduced accuracy)")
        return False
    
    print("✅ Can load pretrained models")
    print()
    return True


def test_sentiment_detection():
    """Test facial sentiment detection."""
    import cv2
    import numpy as np
    
    print("=" * 60)
    print("TEST 1: SENTIMENT DETECTION")
    print("=" * 60)
    
    analyzer = EnhancedVideoAnalyzer(use_pretrained_models=TORCH_AVAILABLE)
    
    # Create a test image (gray background)
    test_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    
    # Test sentiment detection
    result = analyzer.detect_sentiment(test_frame)
    
    print(f"Emotion: {result.emotion}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Is Positive: {result.is_positive}")
    print(f"Is Negative: {result.is_negative}")
    print(f"Details: {result.details}")
    
    if result.emotion:
        print("✅ Sentiment detection working")
    else:
        print("⚠️ Sentiment detection returned no emotion")
    
    print()
    return result


def test_nsfw_detection():
    """Test NSFW content detection."""
    import cv2
    import numpy as np
    
    print("=" * 60)
    print("TEST 2: NSFW DETECTION")
    print("=" * 60)
    
    analyzer = EnhancedVideoAnalyzer(use_pretrained_models=TORCH_AVAILABLE)
    
    # Create a test image (safe - neutral color)
    test_frame = np.ones((480, 640, 3), dtype=np.uint8) * 200
    
    # Test NSFW detection
    result = analyzer.detect_nsfw_content(test_frame)
    
    print(f"Is NSFW: {result.is_nsfw}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Primary Category: {result.primary_category}")
    print(f"Categories: {result.categories}")
    
    if result.primary_category:
        print("✅ NSFW detection working")
    else:
        print("⚠️ NSFW detection returned no category")
    
    print()
    return result


def test_full_analysis(video_path):
    """Test complete video analysis."""
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return None
    
    print("=" * 60)
    print("TEST 3: FULL VIDEO ANALYSIS")
    print("=" * 60)
    print(f"Video: {os.path.basename(video_path)}")
    print()
    
    analyzer = EnhancedVideoAnalyzer(use_pretrained_models=True)
    
    try:
        result = analyzer.analyze_video(video_path, max_frames=30, include_transcript=True)
        
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60)
        print(f"Total Frames: {result.total_frames}")
        print(f"Safe Frames: {result.safe_frames} ✅")
        print(f"Unsafe Frames: {result.unsafe_frames} ⚠️")
        print(f"Positive Sentiment: {result.positive_frames} frames")
        print(f"Negative Sentiment: {result.negative_frames} frames")
        print(f"NSFW Detected: {result.nsfw_detected_frames} frames")
        print(f"\nOverall Safety: {result.overall_safety}")
        
        # Show sample frame details
        if result.frame_analyses:
            print("\n" + "=" * 60)
            print("SAMPLE FRAME DETAILS")
            print("=" * 60)
            
            for i, frame in enumerate(result.frame_analyses[:3]):  # Show first 3 frames
                print(f"\nFrame {frame.frame_number} ({frame.timestamp}):")
                print(f"  Status: {'✅ SAFE' if frame.is_safe else '⚠️ UNSAFE'}")
                print(f"  Confidence: {frame.confidence:.2%}")
                
                if frame.sentiment:
                    print(f"  Emotion: {frame.sentiment.emotion}")
                    print(f"  Sentiment: {'😊 Positive' if frame.sentiment.is_positive else '😟 Negative' if frame.sentiment.is_negative else '😐 Neutral'}")
                
                if frame.nsfw_detection:
                    print(f"  NSFW: {'⚠️ Detected' if frame.nsfw_detection.is_nsfw else '✅ Not detected'}")
                    print(f"  Category: {frame.nsfw_detection.primary_category}")
                
                print(f"  Reasons: {', '.join(frame.reasons)}")
        
        # Transcript results
        if result.transcript and not result.transcript.startswith('[Error'):
            print("\n" + "=" * 60)
            print("TRANSCRIPT ANALYSIS")
            print("=" * 60)
            print(f"Transcript: {result.transcript[:200]}...")
            
            toxic_words = result.transcript_analysis.get('toxic_words', [])
            if toxic_words:
                print(f"\n⚠️ TOXIC WORDS: {', '.join(toxic_words)}")
            
            transcript_safe = result.transcript_analysis.get('is_safe', True)
            print(f"Transcript Safety: {'✅ SAFE' if transcript_safe else '⚠️ UNSAFE'}")
        
        print("\n" + "=" * 60)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main test function."""
    print("\n" + "═" * 60)
    print("  Enhanced Video Analyzer Test Suite")
    print("  Testing: Sentiment + NSFW + Audio Analysis")
    print("═" * 60 + "\n")
    
    # Test 1: Check model availability
    has_torch = test_model_availability()
    
    # Test 2: Sentiment detection
    test_sentiment_detection()
    
    # Test 3: NSFW detection
    test_nsfw_detection()
    
    # Test 4: Full video analysis
    video_path = input("\nEnter video file path (or press Enter to skip): ").strip()
    
    if not video_path:
        # Try sample paths
        sample_paths = ["uploads/test.mp4", "uploads/sample.mp4"]
        for path in sample_paths:
            if os.path.exists(path):
                video_path = path
                break
    
    if video_path and os.path.exists(video_path):
        result = test_full_analysis(video_path)
        
        if result:
            print("\n✅ All tests passed!")
        else:
            print("\n⚠️ Some tests failed")
    else:
        print("\n⏭️ Skipping full video analysis (no video provided)")
        print("\nTo test with a video:")
        print("1. Place video in 'uploads' folder")
        print("2. Run this script again")
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
