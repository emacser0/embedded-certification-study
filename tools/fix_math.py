# -*- coding: utf-8 -*-
import json, re, os

ROOT = r'C:\Users\emacser\Desktop\playground\embeded'

def fix_span(inner):
    prot = []
    def stash(m):
        prot.append(m.group(0)); return '\x00%d\x00' % (len(prot)-1)
    # protect existing \text{...} (and similar) so we don't double-wrap
    tmp = re.sub(r'\\(?:text|mathrm|operatorname|mbox|textbf|textit|textrm)\s*\{[^{}]*\}', stash, inner)
    # wrap bare Hangul runs (allow spaces, ·, 및, /, parentheses between hangul) in \text{}
    tmp = re.sub(r'[가-힣][가-힣()·및/\s]*[가-힣]|[가-힣]', lambda m: '\\text{' + m.group(0) + '}', tmp)
    tmp = re.sub(r'\x00(\d+)\x00', lambda m: prot[int(m.group(1))], tmp)
    return tmp

def fix_text(s):
    if not s:
        return s
    # 과도 이스케이프된 LaTeX 백슬래시 축소: \\dfrac -> \dfrac (KaTeX가 이탤릭으로 깨지는 주원인)
    if '\\\\' in s:
        s = s.replace('\\\\', '\\')
    if '$' not in s:
        return s
    return re.sub(r'\$([^$]*)\$', lambda m: '$' + fix_span(m.group(1)) + '$', s)

def has_bare_hangul_in_math(s):
    for m in re.finditer(r'\$([^$]*)\$', s or ''):
        cleaned = re.sub(r'\\(?:text|mathrm|operatorname|mbox)\s*\{[^{}]*\}', '', m.group(1))
        if re.search(r'[가-힣]', cleaned):
            return True
    return False

import sys
preview = len(sys.argv) > 1 and sys.argv[1] == 'preview'

targets = [
    ('docs/electric/data.json', 'data'),
    ('docs/electric/ai_exp.json', 'exp'),
    ('docs/gconsafety/data.json', 'data'),
    ('docs/gconsafety/ai_exp.json', 'exp'),
]
for rel, kind in targets:
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        continue
    obj = json.load(open(path, encoding='utf-8'))
    changed = 0
    if kind == 'data':
        for q in obj['questions']:
            nq = fix_text(q['q'])
            if nq != q['q']:
                changed += 1; q['q'] = nq
            q['opts'] = [fix_text(o) for o in q['opts']]
    else:
        for k in list(obj.keys()):
            nv = fix_text(obj[k])
            if nv != obj[k]:
                changed += 1; obj[k] = nv
    if not preview:
        json.dump(obj, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
    print(rel, '| changed:', changed)

# show a couple before/after
if preview:
    exp = json.load(open(os.path.join(ROOT, 'docs/electric/ai_exp.json'), encoding='utf-8'))
    for k in ['1562', '3162']:
        if k in exp:
            print('\nID', k, 'AFTER:', fix_text(exp[k])[:300])
