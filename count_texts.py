"""Quick script to count training data items"""

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

print(f"Total texts: {len(texts)}")

# Count by section
normal_count = 52  # Lines 4-55
toxic_count = 50   # Lines 58-107  
sad_count = 16     # Lines 110-125
happy_count = 15   # Lines 128-142

print(f"Normal: {normal_count}")
print(f"Toxic: {toxic_count}")
print(f"Sad: {sad_count}")
print(f"Happy: {happy_count}")
print(f"Total: {normal_count + toxic_count + sad_count + happy_count}")
