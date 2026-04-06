"""
Full Video Transcription Script
Transcribes ENTIRE audio track from video (not just samples)
Detects toxic words in the transcription
"""

import os
import sys
from app import extract_audio, transcribe_audio
from chat_analyser import ChatAnalyzer

def transcribe_full_video(video_path):
    """
    Transcribe complete audio from video file.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Full transcription text with toxicity analysis
    """
    print("="*60)
    print("FULL VIDEO TRANSCRIPTION")
    print("="*60)
    print(f"Video: {os.path.basename(video_path)}")
    
    # Step 1: Extract audio
    print("\n[STEP 1] Extracting audio from video...")
    audio_path = extract_audio(video_path)
    
    if not audio_path:
        print("❌ Audio extraction failed!")
        return None
    
    print(f"✅ Audio extracted: {os.path.basename(audio_path)}")
    
    # Step 2: Transcribe FULL audio
    print("\n[STEP 2] Transcribing complete audio track...")
    print("(This may take 1-3 minutes for a 4-minute video)")
    
    full_transcription = transcribe_audio(audio_path)
    
    if not full_transcription or full_transcription.startswith('['):
        print(f"❌ Transcription failed: {full_transcription}")
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return None
    
    print(f"\n✅ Transcription complete!")
    print(f"   Length: {len(full_transcription)} characters")
    print(f"   Words: {len(full_transcription.split())}")
    
    # Step 3: Analyze for toxic words
    print("\n[STEP 3] Analyzing transcription for toxic words...")
    analyzer = ChatAnalyzer()
    result = analyzer.analyze(full_transcription)
    
    # Display results
    print("\n" + "="*60)
    print("TRANSCRIPTION RESULTS")
    print("="*60)
    
    print("\n📝 FULL TRANSCRIPT:")
    print("-"*60)
    print(full_transcription)
    print("-"*60)
    
    # Toxic word detection
    toxic_words = result.toxic_words if hasattr(result, 'toxic_words') else []
    
    print(f"\n📊 ANALYSIS SUMMARY:")
    print(f"   Total characters: {len(full_transcription)}")
    print(f"   Total words: {len(full_transcription.split())}")
    print(f"   Safety status: {'✅ SAFE' if result.is_safe else '⚠️ UNSAFE'}")
    
    if toxic_words:
        print(f"\n🚨 TOXIC WORDS DETECTED ({len(toxic_words)}):")
        for word in toxic_words:
            print(f"   - {word}")
    else:
        print(f"\n✅ No toxic words detected")
    
    # Show detailed flags
    if result.flags:
        print(f"\n🚩 DETAILED FLAGS ({len(result.flags)}):")
        for i, flag in enumerate(result.flags, 1):
            print(f"   {i}. [{flag.category}] {flag.reason}")
            print(f"      Matched: \"{flag.matched}\"")
            print(f"      Confidence: {flag.confidence:.0%}")
    
    # Clean up audio file
    print("\n[CLEANUP] Removing temporary audio file...")
    try:
        os.remove(audio_path)
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️ Could not remove audio file: {e}")
    
    print("\n" + "="*60)
    print("TRANSCRIPTION COMPLETE")
    print("="*60)
    
    return {
        "transcription": full_transcription,
        "is_safe": result.is_safe,
        "toxic_words": toxic_words,
        "flags": result.flags,
        "word_count": len(full_transcription.split())
    }


if __name__ == "__main__":
    print("\n" + "═"*60)
    print("  MelodyWings Full Video Transcriber")
    print("  Complete Audio Transcription + Toxicity Check")
    print("═"*60 + "\n")
    
    # Get video path
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = input("Enter video file path: ").strip()
    
    # Remove quotes if present
    video_path = video_path.strip('"').strip("'")
    
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"\n❌ Video file not found: {video_path}")
        print("\nCommon locations:")
        print("  - uploads/your_video.mp4")
        print("  - ./test_video.mp4")
        sys.exit(1)
    
    # Run transcription
    result = transcribe_full_video(video_path)
    
    if result:
        # Save transcript to file
        output_file = "transcript_output.txt"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("="*60 + "\n")
                f.write("VIDEO TRANSCRIPTION\n")
                f.write("="*60 + "\n\n")
                f.write(f"Video: {os.path.basename(video_path)}\n")
                f.write(f"Word count: {result['word_count']}\n")
                f.write(f"Safety: {'SAFE' if result['is_safe'] else 'UNSAFE'}\n\n")
                f.write("-"*60 + "\n")
                f.write("FULL TRANSCRIPT:\n")
                f.write("-"*60 + "\n")
                f.write(result['transcription'])
                f.write("\n\n")
                
                if result['toxic_words']:
                    f.write("-"*60 + "\n")
                    f.write("TOXIC WORDS DETECTED:\n")
                    f.write("-"*60 + "\n")
                    for word in result['toxic_words']:
                        f.write(f"  - {word}\n")
                
            print(f"\n💾 Transcript saved to: {output_file}")
        except Exception as e:
            print(f"\n⚠️ Could not save transcript: {e}")
        
        print("\n✅ Success! Full transcription complete.")
    else:
        print("\n❌ Transcription failed.")
        sys.exit(1)
