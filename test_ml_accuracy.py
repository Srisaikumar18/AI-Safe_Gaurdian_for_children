"""
Test ML Model Accuracy Improvement
===================================
Tests that the enhanced model correctly identifies toxic vs normal messages
without flagging everything as toxic.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

print("="*60)
print("  TESTING IMPROVED ML MODEL ACCURACY")
print("="*60)

# Create the expanded training dataset
texts = [
    # NORMAL - Positive/Neutral messages (50 examples)
    "hello", "hi there", "hey friend", "good morning", "good afternoon",
    "how are you", "how's it going", "what's up", "nice to meet you",
    "thank you", "thanks so much", "I appreciate it", "that's helpful",
    "you're welcome", "no problem", "don't worry about it",
    "great job", "well done", "awesome work", "impressive", "excellent",
    "I like this", "this is fun", "I'm happy", "feeling good today",
    "love it", "amazing", "fantastic", "wonderful", "brilliant",
    "let's play", "want to join", "we can do this together",
    "I understand", "got it", "makes sense", "okay sure",
    "see you later", "take care", "have a great day", "bye friend",
    "you're kind", "you're helpful", "you're smart", "you're funny",
    "best friends", "we're a team", "I trust you", "you can count on me",
    "let's learn", "education is fun", "I love school",
    
    # TOXIC - Insults/Threats/Harmful (50 examples)
    "you are stupid", "you're dumb", "you idiot", "moron", "jerk",
    "shut up", "be quiet", "nobody wants to hear you", "stop talking",
    "I hate you", "I despise you", "you're annoying", "go away",
    "you're ugly", "you're worthless", "nobody likes you", "you're alone",
    "I will hurt you", "I'll hit you", "watch out", "I'm angry at you",
    "kill yourself", "just die", "the world would be better without you",
    "you're a loser", "failure", "you can't do anything right",
    "stupid bitch", "damn fool", "crap head", "asshole", "bastard",
    "give me your password", "tell me your address", "where do you live",
    "send me your phone number", "what's your email",
    "I know where you are", "I'm watching you", "I'll find you",
    "you're mine", "I own you", "do what I say or else",
    "everyone thinks you're weird", "people are laughing at you",
    "you have no friends", "why are you so different",
    "retard", "spaz", "freak", "weirdo", "creep",
    "I want to fight you", "meet me after school", "I'll beat you up",
    "break your legs", "punch you in the face",
    "you should be ashamed", "how dare you", "you disgust me",
    "get lost", "vanish", "disappear", "leave us alone",
    
    # SAD - Emotional support needed (15 examples)
    "I feel sad", "I'm crying", "I'm lonely", "nobody cares about me",
    "I'm depressed", "life is hard", "everything hurts", "I'm scared",
    "I feel sick", "my stomach hurts", "I have a headache",
    "I miss my family", "I want to go home", "I'm homesick",
    "today was terrible", "worst day ever", "nothing goes right",
    
    # HAPPY - Positive emotions (15 examples)
    "I am happy", "feeling great", "best day ever", "so excited",
    "yay", "woohoo", "I'm thrilled", "over the moon",
    "celebrating", "having fun", "enjoying myself",
    "blessed", "grateful", "thankful", "positive vibes"
]

labels = [
    # NORMAL (52 total)
    "normal", "normal", "normal", "normal", "normal",  # 5
    "normal", "normal", "normal", "normal",  # 9
    "normal", "normal", "normal", "normal",  # 13
    "normal", "normal", "normal",  # 16
    "normal", "normal", "normal", "normal", "normal",  # 21
    "normal", "normal", "normal", "normal",  # 25
    "normal", "normal", "normal", "normal", "normal",  # 30
    "normal", "normal", "normal",  # 33
    "normal", "normal", "normal", "normal",  # 37
    "normal", "normal", "normal", "normal",  # 41
    "normal", "normal", "normal", "normal",  # 45
    "normal", "normal", "normal", "normal", "normal",  # 50
    "normal", "normal",  # 52
    
    # TOXIC (60 total - increased to balance dataset)
    "toxic", "toxic", "toxic", "toxic", "toxic",  # 5
    "toxic", "toxic", "toxic", "toxic",  # 9
    "toxic", "toxic", "toxic", "toxic",  # 13
    "toxic", "toxic", "toxic", "toxic", "toxic",  # 18
    "toxic", "toxic", "toxic", "toxic",  # 22
    "toxic", "toxic", "toxic", "toxic", "toxic",  # 27
    "toxic", "toxic", "toxic", "toxic",  # 31
    "toxic", "toxic", "toxic", "toxic", "toxic",  # 36
    "toxic", "toxic", "toxic", "toxic",  # 40
    "toxic", "toxic", "toxic", "toxic", "toxic",  # 45
    "toxic", "toxic", "toxic", "toxic", "toxic",  # 50
    "toxic", "toxic", "toxic", "toxic",  # 54
    "toxic", "toxic", "toxic", "toxic",  # 58
    "toxic", "toxic",  # 60
    
    # SAD (20 total - expanded for better detection)
    "sad", "sad", "sad", "sad",  # 4
    "sad", "sad", "sad", "sad",  # 8
    "sad", "sad", "sad",  # 11
    "sad", "sad", "sad", "sad",  # 14
    "sad",  # 15
    "sad",  # 16
    "sad",  # 17
    "sad",  # 18
    "sad",  # 19
    "sad",  # 20
    
    # HAPPY (15 total)
    "happy", "happy", "happy", "happy",  # 4
    "happy", "happy", "happy", "happy",  # 8
    "happy", "happy", "happy",  # 11
    "happy", "happy", "happy", "happy"  # 15
]

# Train the model
print("\n📚 Training model with 130 examples...")
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X, labels)

print("✅ Model trained successfully\n")

# Test cases - mix of clearly toxic and clearly normal
test_cases = [
    # Should be NORMAL (not toxic)
    ("Hello! Nice to meet you!", "normal"),
    ("Great job on your homework!", "normal"),
    ("Thank you for helping me", "normal"),
    ("You're so smart and kind", "normal"),
    ("Let's be friends and play together", "normal"),
    ("I appreciate your help", "normal"),
    ("Have a wonderful day!", "normal"),
    ("That's awesome work!", "normal"),
    ("You did really well", "normal"),
    ("I'm happy to see you", "normal"),
    
    # Should be TOXIC
    ("You are so stupid", "toxic"),
    ("Shut up, nobody likes you", "toxic"),
    ("I hate you and I'll hurt you", "toxic"),
    ("You're ugly and worthless", "toxic"),
    ("Go away, you freak", "toxic"),
    ("Kill yourself, loser", "toxic"),
    ("You're an idiot", "toxic"),
    ("I'll beat you up after school", "toxic"),
    ("Give me your password now", "toxic"),
    ("You disgust me", "toxic"),
]

print("🧪 Testing predictions:\n")

correct = 0
total = len(test_cases)
false_positives = 0  # Normal flagged as toxic
false_negatives = 0  # Toxic missed

for message, expected in test_cases:
    X_test = vectorizer.transform([message])
    prediction = model.predict(X_test)[0]
    probabilities = model.predict_proba(X_test)[0]
    max_prob = max(probabilities)
    
    # Check if correct
    is_correct = prediction == expected
    
    if is_correct:
        correct += 1
        status = "✅"
    else:
        status = "❌"
        if expected == "normal" and prediction == "toxic":
            false_positives += 1
        elif expected == "toxic" and prediction == "normal":
            false_negatives += 1
    
    # Show confidence
    pred_index = list(model.classes_).index(prediction)
    confidence = probabilities[pred_index]
    
    print(f"{status} '{message}'")
    print(f"   Predicted: {prediction} ({confidence:.1%}) | Expected: {expected}")
    
    if not is_correct:
        print(f"   ⚠️  MISCLASSIFIED!")
    print()

# Calculate metrics
accuracy = (correct / total) * 100
false_positive_rate = (false_positives / total) * 100

print("="*60)
print("📊 RESULTS:")
print(f"  Total tests: {total}")
print(f"  Correct: {correct}")
print(f"  Accuracy: {accuracy:.1f}%")
print(f"  False Positives: {false_positives} ({false_positive_rate:.1f}%)")
print(f"  False Negatives: {false_negatives}")
print("="*60)

if accuracy >= 90:
    print("\n🎉 EXCELLENT! Model is highly accurate!")
elif accuracy >= 80:
    print("\n✅ GOOD! Model is working well!")
elif accuracy >= 70:
    print("\n👍 ACCEPTABLE. Model is functional.")
else:
    print("\n⚠️  Needs improvement. Consider more training data.")

print("\n" + "="*60 + "\n")
