"""
MelodyWings Complete System Test
---------------------------------
Automated test script to verify all components work correctly.
Run this to ensure the system is ready for use.
"""

import os
import sys
from datetime import datetime

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_check(name, status, details=""):
    """Print check result."""
    icon = "✅" if status else "❌"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")

# ── Test Components ────────────────────────────────────────────────────────────

def test_dependencies():
    """Test if all required dependencies are installed."""
    print_header("TEST 1: Checking Dependencies")
    
    checks = []
    
    # Test Flask
    try:
        import flask
        checks.append(("Flask installed", True, f"Version: {flask.__version__}"))
    except ImportError:
        checks.append(("Flask installed", False, "Run: pip install flask"))
    
    # Test OpenCV
    try:
        import cv2
        checks.append(("OpenCV installed", True, f"Version: {cv2.__version__}"))
    except ImportError:
        checks.append(("OpenCV installed", False, "Run: pip install opencv-python"))
    
    # Test SpeechRecognition
    try:
        import speech_recognition
        checks.append(("SpeechRecognition installed", True))
    except ImportError:
        checks.append(("SpeechRecognition installed", False, "Run: pip install SpeechRecognition"))
    
    # Test PyAudio
    try:
        import pyaudio
        checks.append(("PyAudio installed", True))
    except ImportError:
        checks.append(("PyAudio installed", False, "Run: pip install PyAudio or pipwin install pyaudio"))
    
    # Test NumPy
    try:
        import numpy
        checks.append(("NumPy installed", True))
    except ImportError:
        checks.append(("NumPy installed", False, "Run: pip install numpy"))
    
    # Print results
    all_passed = True
    for item in checks:
        name = item[0]
        passed = item[1]
        details = item[2] if len(item) > 2 else ""
        print_check(name, passed, details)
        if not passed:
            all_passed = False
    
    return all_passed

def test_module_imports():
    """Test if all custom modules can be imported."""
    print_header("TEST 2: Checking Module Imports")
    
    checks = []
    
    # Test Chat Analyzer
    try:
        from chat_analyser import ChatAnalyzer
        analyzer = ChatAnalyzer()
        checks.append(("Chat Analyzer imports", True))
        
        # Quick test
        result = analyzer.analyze("Hello!")
        checks.append(("Chat Analyzer works", result.is_safe))
        
    except Exception as e:
        checks.append(("Chat Analyzer imports", False, str(e)))
    
    # Test Video Analyzer
    try:
        from video_analyser import VideoAnalyzer
        analyzer = VideoAnalyzer()
        checks.append(("Video Analyzer imports", True))
        
    except Exception as e:
        checks.append(("Video Analyzer imports", False, str(e)))
    
    # Test Safety Alert System
    try:
        from safety_alert_system import SafetyAlertSystem
        system = SafetyAlertSystem()
        checks.append(("Safety Alert System imports", True))
        
    except Exception as e:
        checks.append(("Safety Alert System imports", False, str(e)))
    
    # Print results
    all_passed = True
    for item in checks:
        name = item[0]
        passed = item[1]
        details = item[2] if len(item) > 2 else ""
        print_check(name, passed, details)
        if not passed:
            all_passed = False
    
    return all_passed

def test_chat_analysis():
    """Test chat analysis functionality."""
    print_header("TEST 3: Testing Chat Analysis")
    
    from chat_analyser import ChatAnalyzer
    analyzer = ChatAnalyzer()
    
    tests = [
        # (message, should_be_safe, description)
        ("Hello! Nice to meet you!", True, "Safe greeting"),
        ("My phone number is 555-123-4567", False, "Personal info - phone"),
        ("This is damn frustrating", False, "Profanity detected"),
        ("I live at 123 Main Street", False, "Personal info - address"),
        ("Let's work together", True, "Safe collaboration"),
        ("You're so stupid", False, "Insult/profanity"),
        ("I want to hurt you", False, "Threatening language"),
        ("Email me at test@example.com", False, "Personal info - email"),
    ]
    
    all_passed = True
    
    for message, should_be_safe, description in tests:
        result = analyzer.analyze(message)
        passed = result.is_safe == should_be_safe
        
        status_icon = "✅" if passed else "❌"
        expected = "SAFE" if should_be_safe else "UNSAFE"
        actual = "SAFE" if result.is_safe else "UNSAFE"
        
        print(f"{status_icon} {description}")
        print(f"   Message: '{message}'")
        print(f"   Expected: {expected}, Got: {actual}")
        
        if not result.is_safe and not should_be_safe:
            print(f"   Flags: {len(result.flags)} issues detected")
        
        if not passed:
            all_passed = False
        print()
    
    return all_passed

def test_folders():
    """Test if required folders exist."""
    print_header("TEST 4: Checking Folder Structure")
    
    required_folders = ["uploads", "logs", "templates", "static"]
    
    all_passed = True
    
    for folder in required_folders:
        exists = os.path.exists(folder)
        print_check(f"Folder '{folder}' exists", exists)
        if not exists:
            # Try to create it
            try:
                os.makedirs(folder, exist_ok=True)
                print_check(f"  → Created '{folder}'", True)
            except Exception as e:
                print_check(f"  → Failed to create: {str(e)}", False)
                all_passed = False
    
    return all_passed

def test_flask_app():
    """Test Flask app configuration."""
    print_header("TEST 5: Testing Flask App")
    
    try:
        # Import app without running
        import app
        
        checks = []
        
        # Check if app exists
        checks.append(("Flask app imports", True))
        
        # Check routes
        routes = [rule.rule for rule in app.app.url_map.iter_rules()]
        
        required_routes = ["/", "/api/chat", "/api/analyze-audio", "/api/analyze-video", "/api/alerts"]
        
        for route in required_routes:
            exists = any(route in r for r in routes)
            checks.append((f"Route {route} exists", exists))
        
        # Print results
        all_passed = True
        for name, passed in checks:
            print_check(name, passed)
            if not passed:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_check("Flask app test", False, str(e))
        return False

def run_demo():
    """Run a quick interactive demo."""
    print_header("BONUS: Interactive Demo")
    
    from chat_analyser import ChatAnalyzer
    analyzer = ChatAnalyzer()
    
    print("Type messages to analyze (or 'quit' to exit):\n")
    
    while True:
        try:
            message = input("💬 Message: ").strip()
            
            if not message:
                continue
            
            if message.lower() == 'quit':
                print("\n👋 Goodbye!\n")
                break
            
            result = analyzer.analyze(message)
            
            if result.is_safe:
                print("✅ SAFE\n")
            else:
                print(f"⚠️ UNSAFE - {len(result.flags)} issues:\n")
                for flag in result.flags:
                    print(f"  • [{flag.category}] {flag.reason}")
                print()
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break

# ── Main Test Runner ────────────────────────────────────────────────────────────

def main():
    """Run all tests."""
    print("\n" + "🛡️ " * 20)
    print(" MELODYWINGS COMPLETE SYSTEM TEST")
    print("🛡️ " * 20)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    # Run tests
    results.append(("Dependencies", test_dependencies()))
    results.append(("Module Imports", test_module_imports()))
    results.append(("Chat Analysis", test_chat_analysis()))
    results.append(("Folder Structure", test_folders()))
    results.append(("Flask App", test_flask_app()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    for name, result in results:
        icon = "✅" if result else "❌"
        print(f"{icon} {name}: {'PASSED' if result else 'FAILED'}")
    
    print("\n" + "-" * 70)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready to use!\n")
        print("Next steps:")
        print("1. Run: python app.py")
        print("2. Open: http://127.0.0.1:5000")
        print("3. Start monitoring!\n")
        
        # Offer to run demo
        try:
            response = input("Would you like to run an interactive demo? (y/n): ").strip().lower()
            if response == 'y':
                run_demo()
        except:
            pass
        
    else:
        print("\n⚠️ Some tests failed. Please fix the issues above.\n")
        print("Common fixes:")
        print("• Install missing dependencies: pip install -r requirements.txt")
        print("• Check folder permissions")
        print("• Verify Python version (3.8+)")
        print()
    
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    main()
