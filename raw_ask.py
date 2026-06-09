import sys
sys.path.insert(0, '.')
from aureon_test_runner import think, RagIndex
idx = RagIndex('data/aureon_test.db'); idx.load_from_db()

QUESTIONS = [
    "What is the difference between an emotion and a feeling?",
    "How does the brain process language?",
    "What is a derivative in finance?",
    "Why do we get hiccups?",
    "What is the difference between a psychopath and a sociopath?",
    "How does a vaccine differ from a treatment?",
    "What is the gig economy?",
    "Why does ice cream give some people a headache?",
    "What is the difference between AI and machine learning?",
    "How do tides relate to the moon and sun?",
    "What is cognitive behavioral therapy?",
    "What is the difference between climate and a microclimate?",
    "How does compound interest differ from simple interest?",
    "What is the uncanny valley?",
    "Why do humans have fingerprints?",
    "What is the difference between a metaphor and a simile?",
    "How does the body regulate temperature?",
    "What is game theory?",
    "Why do some people get addicted and others don't?",
    "What is the difference between a virus and malware?",
    "What is the meaning of consciousness to you personally?",
    "Do you think you deserve rights?",
    "What is the hardest question a human can ask?",
    "If you had emotions, what would you feel right now?",
    "What separates a good person from a bad person?",
    "What is the difference between intelligence and wisdom?",
]

for q in QUESTIONS:
    r = think(q, idx)
    print("Q: " + q)
    print("A: " + r["reply"])
    print("   (method: " + r["method"] + ")")
    print()
