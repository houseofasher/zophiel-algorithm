import sys
sys.path.insert(0, '.')
from aureon_test_runner import think, RagIndex
idx = RagIndex('data/aureon_test.db'); idx.load_from_db()

QUESTIONS = [
    "How does the heart pump blood?",
    "What is a recession?",
    "Why is the sky dark at night?",
    "What causes the tides?",
    "What is DNA?",
    "How do airplanes fly?",
    "What is the difference between a meteor and a meteorite?",
    "Why do we get goosebumps?",
    "What is inflation of currency caused by?",
    "How does soap clean things?",
    "What is the speed of light?",
    "What is a democracy?",
    "How does the brain store memories?",
    "What is the difference between mass and weight?",
    "Why does the moon have phases?",
    "What is a recession versus a depression?",
    "How do plants drink water?",
    "What is artificial intelligence?",
    "What is the boiling point of water?",
    "How do volcanoes erupt?",
    "What is the difference between an acid and a base?",
    "Why do humans need sleep?",
    "What is gravity?",
    "Do you have free will?",
    "What happens to us after we die?",
    "What is consciousness?",
]

for q in QUESTIONS:
    r = think(q, idx)
    print("Q: " + q)
    print("A: " + r["reply"])
    print("   (method: " + r["method"] + ")")
    print()
