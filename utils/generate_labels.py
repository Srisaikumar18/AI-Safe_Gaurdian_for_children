"""Generate correct labels for app.py training data"""

# Count texts in each category
normal_count = 60
toxic_count = 60
sad_count = 14
happy_count = 14

print(f"Total: {normal_count + toxic_count + sad_count + happy_count}")

# Generate labels
labels = []

# NORMAL
labels.extend(["normal"] * normal_count)
print(f"# NORMAL ({normal_count})")

# TOXIC  
labels.extend(["toxic"] * toxic_count)
print(f"# TOXIC ({toxic_count})")

# SAD
labels.extend(["sad"] * sad_count)
print(f"# SAD ({sad_count})")

# HAPPY
labels.extend(["happy"] * happy_count)
print(f"# HAPPY ({happy_count})")

# Print as formatted string for copying
output = "    labels = [\n"

# Normal section
for i in range(0, normal_count, 5):
    count = min(5, normal_count - i)
    items = ', '.join(['"normal"'] * count)
    output += f'        {items},  # {i+count}\n'

output += '        \n'

# Toxic section
for i in range(0, toxic_count, 5):
    count = min(5, toxic_count - i)
    items = ', '.join(['"toxic"'] * count)
    output += f'        {items},  # {i+count}\n'

output += '        \n'

# Sad section
for i in range(0, sad_count, 4):
    count = min(4, sad_count - i)
    items = ', '.join(['"sad"'] * count)
    output += f'        {items},  # {i+count}\n'

output += '        \n'

# Happy section
for i in range(0, happy_count, 4):
    count = min(4, happy_count - i)
    items = ', '.join(['"happy"'] * count)
    output += f'        {items},  # {i+count}\n'

output += "    ]"

print("\n\nFormatted for app.py:")
print(output)
