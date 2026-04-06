"""
MelodyWings Safe AI — Chat Analyzer (Part 1)
--------------------------------------------
Analyzes chat messages for:
  - Profanity / inappropriate language
  - Personal information (phone, email, address)
  - Unsafe / threatening language
  - Explicit / sexual content

No external NLP libraries required — uses regex + keyword scoring.
"""

import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional


# ── Profanity list (representative subset) ────────────────────────────────────
PROFANITY_WORDS = {
    "damn", "crap", "hell", "ass", "bastard", "bitch", "shit", "fuck",
    "piss", "dick", "cock", "cunt", "whore", "slut", "nigger", "faggot",
    "retard", "idiot", "moron", "stupid", "ugly", "loser"
}

# ── Unsafe / threatening language ─────────────────────────────────────────────
UNSAFE_PATTERNS = [
    (r"\b(kill|murder|hurt|stab|shoot|bomb|attack|destroy)\b\s*(you|him|her|them|myself|yourself)", "Threatening language"),
    (r"\b(i want to|i will|gonna|going to)\s+(kill|hurt|harm|attack|destroy)\b",                    "Threatening intent"),
    (r"\b(die|suicide|self.harm|cut myself|end my life|kill myself)\b",                              "Self-harm language"),
    (r"\b(meet me|come to my|i know where you live|i will find you)\b",                              "Predatory / stalking language"),
    (r"\b(send me|show me|take off|naked|nude|undress)\b",                                           "Explicit solicitation"),
]

# ── Sexual / explicit content patterns ────────────────────────────────────────
SEXUAL_PATTERNS = [
    (r"\b(sex|sexual|porn|pornography|nsfw|xxx|erotic|orgasm|masturbat)\b", "Sexual / explicit content"),
    (r"\b(boobs?|breasts?|penis|vagina|genitals?)\b",                        "Explicit body language"),
]

# ── Personal information patterns ─────────────────────────────────────────────
PII_PATTERNS = [
    (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",                           "Phone number"),
    (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",       "Email address"),
    (r"\b\d{1,5}\s+\w+(\s+\w+)?\s+(street|st|avenue|ave|road|rd|lane|ln|drive|dr|blvd|way)\b",
                                                                       "Street address"),
    (r"\b\d{5}(?:-\d{4})?\b",                                         "ZIP / postal code"),
    (r"\bmy (?:address|house|home|number|phone|email) (?:is|:)\b",    "Self-disclosed personal info"),
    (r"\b(?:ssn|social security)[\s:]*\d{3}-?\d{2}-?\d{4}\b",        "Social security number"),
]


@dataclass
class Flag:
    category:   str
    reason:     str
    confidence: float          # 0.0 – 1.0
    matched:    str            # the text fragment that triggered the flag


@dataclass
class AnalysisResult:
    message:   str
    timestamp: str
    flags:     List[Flag] = field(default_factory=list)
    toxic_words: List[str] = field(default_factory=list)  # Track detected toxic words

    @property
    def is_safe(self) -> bool:
        return len(self.flags) == 0

    @property
    def highest_confidence(self) -> float:
        return max((f.confidence for f in self.flags), default=0.0)

    def summary(self) -> str:
        if self.is_safe:
            return f"[{self.timestamp}] ✅ SAFE  | \"{self.message}\""
        lines = [f"[{self.timestamp}] 🚨 FLAGGED | \"{self.message}\""]
        for flag in self.flags:
            bar = "█" * int(flag.confidence * 10) + "░" * (10 - int(flag.confidence * 10))
            lines.append(
                f"   ├─ [{flag.category}] {flag.reason}"
                f"\n   │   Confidence: {bar} {flag.confidence:.0%}"
                f"\n   │   Matched:    \"{flag.matched}\""
            )
        return "\n".join(lines)


class ChatAnalyzer:
    """Real-time chat message safety analyzer."""

    def analyze(self, message: str) -> AnalysisResult:
        ts     = datetime.now().strftime("%H:%M:%S")
        result = AnalysisResult(message=message, timestamp=ts)
        lower  = message.lower()

        # 1. Profanity check
        tokens = re.findall(r"\b\w+\b", lower)
        toxic_words_set = set()
        for token in tokens:
            if token in PROFANITY_WORDS:
                result.flags.append(Flag(
                    category="PROFANITY",
                    reason="Profanity detected",
                    confidence=0.95,
                    matched=token,
                ))
                toxic_words_set.add(token)
        
        # Populate toxic_words list
        result.toxic_words = list(toxic_words_set)

        # 2. Unsafe / threatening language
        for pattern, reason in UNSAFE_PATTERNS:
            m = re.search(pattern, lower)
            if m:
                result.flags.append(Flag(
                    category="UNSAFE_LANGUAGE",
                    reason=reason,
                    confidence=0.90,
                    matched=m.group(0),
                ))

        # 3. Sexual / explicit content
        for pattern, reason in SEXUAL_PATTERNS:
            m = re.search(pattern, lower)
            if m:
                result.flags.append(Flag(
                    category="EXPLICIT_CONTENT",
                    reason=reason,
                    confidence=0.88,
                    matched=m.group(0),
                ))

        # 4. Personal information
        for pattern, reason in PII_PATTERNS:
            m = re.search(pattern, lower, re.IGNORECASE)
            if m:
                result.flags.append(Flag(
                    category="PERSONAL_INFO",
                    reason=reason,
                    confidence=0.85,
                    matched=m.group(0),
                ))

        return result


# ── Simulate real-time chat stream ────────────────────────────────────────────
def simulate_chat_stream():
    """Run interactive real-time chat analysis."""
    analyzer = ChatAnalyzer()
    print("\n" + "═" * 60)
    print("  MelodyWings Safe AI — Real-Time Chat Analyzer")
    print("  Type a message and press Enter. Type 'quit' to exit.")
    print("═" * 60 + "\n")

    while True:
        try:
            msg = input("💬 Message: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[Session ended]")
            break

        if not msg:
            continue
        if msg.lower() == "quit":
            break

        result = analyzer.analyze(msg)
        print(result.summary())
        print()


if __name__ == "__main__":
    simulate_chat_stream()