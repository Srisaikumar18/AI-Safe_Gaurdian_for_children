"""Test that ML model trains correctly with new data"""

from app import ml_model, vectorizer

print("✅ ML Model loaded successfully!")
print(f"Model classes: {ml_model.classes_}")
print(f"Classes learned: {len(ml_model.classes_)}")

# Test a few predictions
test_messages = [
    "Hello friend!",
    "You are stupid",
    "Thank you for helping",
    "Great job!"
]

print("\n🧪 Quick predictions:")
for msg in test_messages:
    X = vectorizer.transform([msg])
    pred = ml_model.predict(X)[0]
    proba = max(ml_model.predict_proba(X)[0])
    print(f"  '{msg}' → {pred} ({proba:.1%})")
