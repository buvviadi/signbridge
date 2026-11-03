import re

# The signs we support. Later, each word maps to a video clip / landmark file.
VOCAB = {
    # pronouns / people
    "i", "you", "he", "she", "we", "they", "my", "your", "name", "friend",
    "mother", "father", "teacher", "doctor", "student",
    # verbs
    "go", "come", "want", "need", "help", "eat", "drink", "sleep", "know",
    "like", "have", "see", "give", "take", "understand", "sit", "stand",
    "learn", "work", "play",
    # places / things
    "hospital", "school", "home", "college", "water", "food", "medicine",
    "book", "class", "market", "toilet",
    # greetings / common
    "hello", "thanks", "please", "sorry", "yes", "no", "not", "good", "bad",
    "morning", "night", "today", "tomorrow", "yesterday", "now", "again",
    # question words
    "what", "where", "when", "who", "why", "how", "which",    # added after live testing
    "from", "hope", "fine", "life", "family", "brother", "sister", "money",
    "time", "day", "name", "age", "live", "open", "close", "wait", "stop",
    "happy", "sad", "hungry", "sick", "pain", "tea", "coffee", "phone",
}

WH_WORDS = {"what", "where", "when", "who", "why", "how", "which"}

# Words with no sign of their own
STOPWORDS = {"a", "an", "the", "is", "am", "are", "was", "were", "be", "been",
             "to", "of", "do", "does", "did", "very", "much",
             "and", "then", "can", "will", "would", "just", "so"}

CONTRACTIONS = {
    "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "can't": "can not", "won't": "will not", "i'm": "i am",
    "what's": "what is", "where's": "where is", "who's": "who is",
    "i'll": "i will", "i'd": "i would", "you're": "you are",
}

# Irregular forms and synonyms -> base word
LEMMA = {
    "went": "go", "gone": "go", "going": "go", "goes": "go",
    "ate": "eat", "eaten": "eat", "came": "come", "saw": "see",
    "gave": "give", "took": "take", "knew": "know", "slept": "sleep",
    "me": "i", "us": "we", "him": "he", "her": "she", "them": "they",
    "thank": "thanks", "hi": "hello", "hey": "hello",
    "doctors": "doctor", "students": "student", "teachers": "teacher",
    "medicines": "medicine", "books": "book", "friends": "friend",
}

def lemmatize(word):
    """Return the base word if we can find it in VOCAB, else the word itself."""
    if word in LEMMA:
        return LEMMA[word]
    if word in VOCAB:
        return word
    # try stripping common endings: wants, wanted, helping, played, watches...
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) > len(suffix) + 1:
            stem = word[: -len(suffix)]
            for candidate in (stem, stem + "e", stem[:-1]):  # help, like, stop
                if candidate in VOCAB:
                    return candidate
    return word

def text_to_gloss(text):
    """Sentence -> list of tokens: {'gloss': 'HOSPITAL', 'type': 'sign' | 'fingerspell'}"""
    text = text.lower().strip()
    for short, full in CONTRACTIONS.items():
        text = text.replace(short, full)
    words = re.findall(r"[a-z]+", text)

    words = [w for w in words if w not in STOPWORDS]
    words = [lemmatize(w) for w in words]

    # ISL/ASL put question words at the end of the sentence
    wh = [w for w in words if w in WH_WORDS]
    words = [w for w in words if w not in WH_WORDS] + wh

    tokens = []
    for w in words:
        if w in VOCAB:
            tokens.append({"gloss": w.upper(), "type": "sign"})
        else:
            tokens.append({"gloss": w.upper(), "type": "fingerspell",
                           "letters": list(w.upper())})
    return tokens

def gloss_string(text):
    return " ".join(
        t["gloss"] if t["type"] == "sign" else "#" + t["gloss"]
        for t in text_to_gloss(text)
    )