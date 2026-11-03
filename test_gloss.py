from gloss import text_to_gloss, gloss_string

sentences = [
    "Hello, how are you today?",
    "I want to go to the hospital.",
    "What is your name?",
    "Thank you very much.",
    "Please help me.",
    "I don't understand.",
    "Where is the toilet?",
    "My friend Ravi went to school yesterday.",
    "The doctor gave me medicine.",
    "I am eating food.",
]

total = signed = 0
for s in sentences:
    print(f"{s:45} -> {gloss_string(s)}")
    for t in text_to_gloss(s):
        total += 1
        signed += t["type"] == "sign"

print(f"\nVocabulary coverage: {signed}/{total} = {100 * signed / total:.0f}%")