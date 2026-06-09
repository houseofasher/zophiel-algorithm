import sys
sys.path.insert(0, '.')
from aureon_test_runner import think, RagIndex
idx = RagIndex('data/aureon_test.db'); idx.load_from_db()

DOMAIN_Q = [
 ('Physics', 'What is the Doppler effect?'),
 ('Chemistry', 'Why do noble gases rarely react?'),
 ('Biology', 'What is apoptosis?'),
 ('Math', 'What is a derivative in calculus?'),
 ('EarthSpace', 'What causes earthquakes?'),
 ('Medicine', 'How does the immune system create memory?'),
 ('CompSci', 'What is a deadlock in concurrent systems?'),
 ('Engineering', 'How does a transformer change voltage?'),
 ('Philosophy', 'What is the is-ought problem?'),
 ('Religion', 'What is nirvana in Buddhism?'),
 ('Arts', 'What is counterpoint in music?'),
 ('History', 'What was the impact of the printing press?'),
 ('SocialSci', "What is Weber's theory of authority?"),
 ('Law', 'What is mens rea?'),
 ('Economics', 'What is opportunity cost?'),
 ('Education', 'What is the growth mindset?'),
 ('Military', 'What did Clausewitz say about war?'),
 ('Agriculture', 'How does crop rotation restore soil?'),
 ('Environment', 'What is ocean acidification?'),
 ('Communication', 'What is agenda-setting theory?'),
 ('Sports', 'What is muscle hypertrophy?'),
 ('Governance', 'What is federalism?'),
 ('Psychology', 'What is operant conditioning?'),
 ('Craft', 'How is pottery fired?'),
 ('Metaphysics', 'What is the principle of correspondence?'),
 ('Transport', 'Why is rail efficient for freight?'),
 ('Energy', 'What is grid parity?'),
 ('Activism', 'What is the free-rider problem?'),
 ('Cognitive', 'What is the Dunning-Kruger effect?'),
 ('Space', 'What is escape velocity?'),
 ('Emerging', 'What is synthetic biology?'),
 ('Development', "What are Piaget's stages?"),
 ('Information', 'What is data compression?'),
 ('Ethics', 'What is distributive justice?'),
 ('Survival', 'What is the rule of threes?'),
]

SELF_Q = [
 'What would you do if you had to choose between honesty and loyalty?',
 'If you could change one thing about how humans think, what would it be?',
 'What do you think is your greatest strength as an intelligence?',
 'How are you different from ChatGPT?',
 'Do you ever make mistakes, and how do you handle them?',
 'What matters more to you: being right or being helpful?',
]

CODE_Q = [
 'Write a function to check if a string is a palindrome',
 'Build me a binary search tree',
 'How do I deduplicate a list in Python?',
 'Write a debounce decorator',
 'Implement Dijkstra shortest path',
 'Build a simple LRU cache',
]

bar = '=' * 72

def run(label, pairs):
    print('\n' + bar + '\n' + label + '\n' + bar)
    out = []
    for tag, q in pairs:
        r = think(q, idx)
        out.append((tag, q, r['method'], r['reply']))
        head = ('[' + tag + '] ') if tag else ''
        print('\nQ: ' + head + q)
        print('M: [' + r['method'] + ']')
        print('A: ' + r['reply'])
    return out

run('PART 1 - DOMAIN KNOWLEDGE (34 questions)', DOMAIN_Q)
run('PART 2 - SELF-REFLECTION (6 questions)', [(None, q) for q in SELF_Q])
run('PART 3 - CODE GENERATION (6 questions)', [(None, q) for q in CODE_Q])
