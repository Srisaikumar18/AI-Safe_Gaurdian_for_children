"""Count exact number of texts in app.py"""

# Copy from app.py
texts = [
    # NORMAL - Clear positive phrases WITHOUT overlap words (60 examples)
    "hello friend", "hi there", "hey buddy", "good morning", "good afternoon",
    "how are you doing", "hope you are well", "what is new", "pleased to meet you",
    "thanks", "thank you very much", "much appreciated", "very helpful of you",
    "you are welcome", "it is fine", "all good", "no worries",
    "excellent work", "perfect", "outstanding", "superb", "magnificent",
    "I enjoy this", "this is enjoyable", "I am content", "feeling wonderful",
    "I adore this", "super cool", "incredible", "marvelous", "exceptional",
    "shall we play", "join us", "together we can",
    "I comprehend", "I see", "that is logical", "yes certainly",
    "until next time", "look after yourself", "wonderful day ahead", "farewell friend",
    "you are thoughtful", "you assist well", "you are clever", "you make me laugh",
    "close companions", "we cooperate", "I have confidence in you", "rely on me",
    "study time", "learning rocks", "school is great",
    "congratulations", "bravo", "high five", "you nailed it",
    "keep going", "you can do it", "stay strong", "believe yourself",
    "delightful", "charming", "pleasant", "agreeable", "satisfactory",
    "good vibes", "positive energy", "feeling blessed", "life is good",
    
    # TOXIC - Clear harmful phrases with DISTINCT vocabulary (60 examples)
    "you are an idiot", "you are dumb", "complete moron", "such a jerk", "pathetic",
    "shut your mouth", "silence", "stop your nonsense", "quit yapping",
    "I loathe you", "despise you", "you irritate me", "leave me alone",
    "you are hideous", "completely worthless", "everyone hates you", "you have nobody",
    "gonna harm you", "will strike you", "better watch yourself", "furious at you",
    "end your life", "drop dead", "eliminate yourself", "cease existing",
    "total failure", "can not succeed", "useless person", "accomplish nothing",
    "stupid creature", "darn fool", "trash human", "complete villain", "child of devil",
    "hand over credentials", "disclose location", "reveal your dwelling",
    "transmit contact details", "provide electronic mail",
    "tracking you", "observing you", "coming for you",
    "you belong to me", "I control you", "obey me",
    "they mock you", "all ridicule you",
    "zero companions", "what makes you unusual",
    "disabled slur", "handicapped insult", "abnormal person", "strange one", "disturbing individual",
    "gonna battle you", "confront me", "gonna strike you",
    "smash your bones", "strike your face",
    "feel regret", "how could you", "you make me sick",
    "depart", "cease to exist", "fade away", "isolate yourself",
    "you are pathetic", "disappointing", "embarrassing", "disgrace",
    "hate your existence", "you should not be here", "unwanted",
    "annoying pest", "troublesome person", "irritating fool",
    
    # SAD - Emotional distress (clear indicators) (14 examples)
    "feeling sorrowful", "weeping", "isolated", "I feel abandoned",
    "deeply depressed", "existence is difficult", "constant pain", "terrified",
    "physically ill", "abdominal pain", "migraine",
    "longing for relatives", "wish to return home", "missing home",
    "awful experience", "horrible day", "everything fails",
    
    # HAPPY - Joy and excitement (14 examples)
    "feeling joyful", "extremely pleased", "fantastic day", "very enthusiastic",
    "hurrah", "excellent", "excited", "ecstatic",
    "rejoicing", "enjoyment", "pleasure",
    "fortunate", "appreciative", "full of gratitude", "good feelings"
]

print(f"Total texts: {len(texts)}")

# Count by section
normal = texts[:64]
toxic_start = 64
toxic_end = 124
sad_start = 124
sad_end = 140
happy_start = 140

print(f"NORMAL section (indices 0-63): {len(normal)} items")
print(f"TOXIC section should start at index {toxic_start}")
print(f"SAD section should start at index {sad_end}")
print(f"HAPPY section should start at index {sad_end}")
