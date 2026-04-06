# AI Safety Guardian for Child Interaction Platforms

## 🚀 Overview
AI Safety Guardian is a real-time multimodal safety system designed to protect children on online learning platforms. It analyzes chat messages, video frames, and audio streams to detect unsafe behavior and intervene proactively.

---

## 🔥 Features
- Real-time chat analysis (profanity, toxicity, personal info detection)
- Context-aware conversation monitoring
- Video frame analysis for unsafe content detection
- Speech-to-text analysis using Whisper
- Unified risk scoring system
- Real-time alerts and intervention
- Behavioral pattern detection (anti-grooming)

---

## 🧠 Tech Stack
Python, OpenCV, spaCy, NLTK, Hugging Face Transformers, Whisper, Flask

---

## ⚙️ How It Works
1. Chat messages are analyzed using NLP models
2. Video frames are processed using OpenCV + NSFW models
3. Audio is converted to text and analyzed
4. All signals are combined into a risk score
5. Alerts are generated in real-time

---

## ▶️ Installation

```bash
git clone https://github.com/your-username/ai-safety-guardian.git
cd ai-safety-guardian
pip install -r requirements.txt