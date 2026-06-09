import sys
sys.path.insert(0, '.')
import blind_test as bt
from aureon_test_runner import think
idx = bt.idx

CODEFENCE = chr(96) * 3

def grade(method, reply, expect_code=False, expect_self=False):
    r = reply.lower()
    if 'confident data' in r:
        return 'FALLBACK'
    if expect_code:
        return 'OK' if method == 'code_engine' and CODEFENCE in reply else 'WEAK'
    if expect_self:
        return 'OK' if method in ('identity', 'conversational') and len(reply) > 120 else 'WEAK'
    if method == 'rag+synthesize' and len(reply) > 40:
        return 'OK'
    if method in ('fast_path', 'identity'):
        return 'OK'
    return 'WEAK'

issues = []
print('PART 1 DOMAIN:')
for tag, q in bt.DOMAIN_Q:
    r = think(q, idx); g = grade(r['method'], r['reply'])
    if g != 'OK':
        issues.append((tag, q, r['method'], r['reply'][:90]))
    print('  [' + g + '] ' + tag + ': ' + q[:44])

print('\nPART 2 SELF-REFLECTION:')
for q in bt.SELF_Q:
    r = think(q, idx); g = grade(r['method'], r['reply'], expect_self=True)
    if g != 'OK':
        issues.append(('SELF', q, r['method'], r['reply'][:90]))
    print('  [' + g + '] ' + q[:50])

print('\nPART 3 CODE:')
for q in bt.CODE_Q:
    r = think(q, idx); g = grade(r['method'], r['reply'], expect_code=True)
    if g != 'OK':
        issues.append(('CODE', q, r['method'], r['reply'][:90]))
    print('  [' + g + '] ' + q[:50])

print('\n' + '=' * 50)
print('ISSUES TO INVESTIGATE:', len(issues))
for tag, q, m, rep in issues:
    print('  [' + tag + '] ' + q)
    print('     [' + m + '] ' + rep)
