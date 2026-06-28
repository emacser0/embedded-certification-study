# -*- coding: utf-8 -*-
import json, re, os
ROOT = r'C:\Users\emacser\Desktop\playground\embeded'

ENV = re.compile(r'(\\begin\{[a-zA-Z]*matrix\})(.*?)(\\end\{[a-zA-Z]*matrix\})')
# row separator: a single backslash followed by digit, minus, or an uppercase letter
# that is NOT the start of a normal command like \Omega (uppercase + lowercase).
ROWSEP = re.compile(r'\\(?=[0-9\-]|[A-Z](?![a-z]))')

def fix_matrices(s):
    if '\\begin{' not in s:
        return s
    def repl(m):
        body = ROWSEP.sub(r'\\\\', m.group(2))
        return m.group(1) + body + m.group(3)
    return ENV.sub(repl, s)

def fix_text(s):
    if not s or '\\begin{' not in s:
        return s
    return re.sub(r'\$([^$]*)\$', lambda m: '$' + fix_matrices(m.group(1)) + '$', s)

for rel, kind in [('docs/electric/data.json','data'), ('docs/electric/ai_exp.json','exp'),
                  ('docs/gconsafety/data.json','data'), ('docs/gconsafety/ai_exp.json','exp')]:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        continue
    obj = json.load(open(p, encoding='utf-8'))
    ch = 0
    if kind == 'data':
        for q in obj['questions']:
            nv = fix_text(q['q'])
            if nv != q['q']: q['q'] = nv; ch += 1
            q['opts'] = [fix_text(o) for o in q['opts']]
    else:
        for k in list(obj.keys()):
            nv = fix_text(obj[k])
            if nv != obj[k]: obj[k] = nv; ch += 1
    json.dump(obj, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    print(rel, 'matrix-fixed:', ch)
