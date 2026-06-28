# -*- coding: utf-8 -*-
import json, glob, os
from PIL import Image

SC = r'C:\Users\emacser\AppData\Local\Temp\claude\C--Users-emacser-Desktop-playground-embeded\aa9f1027-c09c-4b01-9573-d24bf6945175\scratchpad'
IMGDIR = r'C:\Users\emacser\Desktop\playground\embeded\docs\gconsafety\img'
DATA = r'C:\Users\emacser\Desktop\playground\embeded\docs\gconsafety\data.json'

new = json.load(open(os.path.join(SC, 'cons_new_questions.json'), encoding='utf-8'))
tx = {}
bad = []
for f in glob.glob(os.path.join(SC, 'constx2', 'out_*.json')):
    try:
        for r in json.load(open(f, encoding='utf-8')):
            if isinstance(r, dict) and 'id' in r:
                tx[int(r['id'])] = r
    except Exception as ex:
        bad.append((os.path.basename(f), str(ex)[:50]))

def crop_fig(fn, box):
    src = os.path.join(IMGDIR, fn)
    if not os.path.exists(src):
        return None
    try:
        im = Image.open(src).convert('RGB'); W, H = im.size
        x0, y0, x1, y1 = box; pad = 0.02
        x0 = max(0, x0-pad); y0 = max(0, y0-pad); x1 = min(1, x1+pad); y1 = min(1, y1+pad)
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1) or x1-x0 < 0.05 or y1-y0 < 0.03:
            x0, y0, x1, y1 = 0, 0, 1, 1
        out = 'fig_' + fn
        im.crop((int(x0*W), int(y0*H), int(x1*W), int(y1*H))).save(os.path.join(IMGDIR, out))
        return out
    except Exception:
        return None

text_n = mix_n = img_n = 0
new_q = []
for q in new:
    i = q['id']
    b = {'id': i, 'setKey': q['setKey'], 'setLabel': q['setLabel'], 'year': q['year'],
         'subjectNorm': q['subjectNorm'], 'num': q['num'], 'ans': q['ans'], 'exp': '', 'tag': ''}
    t = tx.get(i)
    if t and (t.get('q') or '').strip():
        stem = t['q'].strip()
        opts = [str(o).strip() for o in (t.get('opts') or []) if str(o).strip()]
        while len(opts) < 4:
            opts.append('')
        if t.get('figure'):
            fb = t.get('figbox')
            ff = crop_fig(q['img'], fb) if (fb and isinstance(fb, list) and len(fb) == 4) else None
            if not ff:
                ff = q['img']
            b['q'] = stem + '\n\n![](gconsafety/img/' + ff + ')'; b['opts'] = opts[:4]; mix_n += 1
        else:
            b['q'] = stem; b['opts'] = opts[:4]; text_n += 1
    else:
        b['q'] = '![](gconsafety/img/' + q['img'] + ')'; b['opts'] = ['', '', '', '']; img_n += 1
    new_q.append(b)

# merge with existing (20220424, 120 questions)
existing = json.load(open(DATA, encoding='utf-8'))['questions']
all_q = existing + new_q
all_q.sort(key=lambda q: (q['setKey'], q['num']))

from collections import OrderedDict
sm = OrderedDict()
for q in all_q:
    sm.setdefault(q['setKey'], q['setLabel'])
sets = [{'key': k, 'label': v, 'count': sum(1 for q in all_q if q['setKey'] == k),
         'gradable': sum(1 for q in all_q if q['setKey'] == k and q['ans'])} for k, v in sm.items()]
json.dump({'questions': all_q, 'sets': sets}, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False)

# prune unused images
used = set()
for q in all_q:
    for p in q['q'].split('!['):
        if '](gconsafety/img/' in p:
            used.add(p.split('](gconsafety/img/')[1].split(')')[0])
rm = 0
for f in os.listdir(IMGDIR):
    if f not in used:
        os.remove(os.path.join(IMGDIR, f)); rm += 1
print('bad tx files:', len(bad))
print('new: text', text_n, 'mixed', mix_n, 'img-only', img_n)
print('total questions:', len(all_q), '| sets:', len(sets))
print('images pruned:', rm, '| kept:', len(os.listdir(IMGDIR)))
