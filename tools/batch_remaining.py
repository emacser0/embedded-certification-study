# -*- coding: utf-8 -*-
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from extract_v2 import process_v2

ROOT = r'C:\Users\emacser\Desktop\playground\embeded\electric'
IMGOUT = r'C:\Users\emacser\Desktop\playground\embeded\docs\electric\img'
STAGE = os.path.join(os.path.dirname(__file__), 'new_questions.json')

DONE = {'20220424', '20210515', '20200822', '20190804'}
folders = sorted(d for d in os.listdir(ROOT)
                 if os.path.isdir(os.path.join(ROOT, d)) and d.isdigit() and d not in DONE)

def find_pdf(folder, kind):
    for f in os.listdir(folder):
        if kind in f and f.endswith('.pdf'):
            return os.path.join(folder, f)

def label_of(d):
    return f'{d[:4]}-{d[4:6]}-{d[6:8]}'

all_new = []
qid = 1000  # new ids start at 1000 (existing are 1..399)
summary = []
for date in folders:
    folder = os.path.join(ROOT, date)
    try:
        t_out = process_v2(find_pdf(folder, '교사용'), '', 'e'+date, want_images=False)
        ans_by_num = {r['num']: r['ans'] for r in t_out}
        s_out = process_v2(find_pdf(folder, '학생용'), IMGOUT, 'e'+date, want_images=True)
    except Exception as ex:
        summary.append((date, 'ERROR ' + str(ex)[:60], 0)); continue
    kept = 0
    for r in s_out:
        a = ans_by_num.get(r['num'])
        if not a or 'img' not in r:
            if 'img' in r and os.path.exists(os.path.join(IMGOUT, r['img'])):
                os.remove(os.path.join(IMGOUT, r['img']))
            continue
        all_new.append({'id': qid, 'setKey': date, 'setLabel': label_of(date),
                        'year': int(date[:4]), 'subjectNorm': r['subject'] or '기타',
                        'num': r['num'], 'ans': a, 'img': r['img']})
        qid += 1; kept += 1
    summary.append((date, len(s_out), kept))

json.dump(all_new, open(STAGE, 'w', encoding='utf-8'), ensure_ascii=False)
for s in summary:
    print(' ', s[0], 'total', s[1], 'kept', s[2])
print('NEW questions:', len(all_new))
