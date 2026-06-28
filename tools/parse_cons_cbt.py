# -*- coding: utf-8 -*-
"""한솔 CBT 복원 PDF(텍스트 정상) 파서: 문제+보기+과목 + 마지막 페이지 정답표."""
import fitz, re, io, os

CIRC = {'①':1,'②':2,'③':3,'④':4}
SUBJ_RE = re.compile(r'^제\s*([1-6])\s*과목\s*[:：]\s*(.+?)\s*$')
QSTART  = re.compile(r'^(\d{1,3})\.\s*(.*)$')
SKIP_RE = re.compile(r'한솔아카데미|www\.inup|TEL\.|온라인강의|학원강의|본\s*문제는|복원한|수험자의\s*기억|^\s*※')
CIRC_SPLIT = re.compile(r'([①②③④])')

def clean(s): return re.sub(r'\s+', ' ', s).strip()

def add_segment(cur, state, text):
    parts = CIRC_SPLIT.split(text)
    pre = parts[0].strip()
    if pre:
        if state['mode'] == 'opt' and cur['opts']:
            cur['opts'][-1] = clean(cur['opts'][-1] + ' ' + pre)
        else:
            cur['stem'] = clean(cur['stem'] + ' ' + pre)
    i = 1
    while i < len(parts):
        txt = parts[i+1].strip() if i+1 < len(parts) else ''
        cur['opts'].append(txt); state['mode'] = 'opt'
        i += 2

def parse_pdf(path):
    doc = fitz.open(path)
    pages = [doc[i].get_text() for i in range(doc.page_count)]
    doc.close()
    qmarks = [len(re.findall(r'(?m)^\s*\d{1,3}\.', p)) for p in pages]
    # 뒤쪽의 qmark 0 페이지들 = 정답표
    ans_start = len(pages)
    while ans_start-1 >= 0 and qmarks[ans_start-1] == 0:
        ans_start -= 1
    body = '\n'.join(pages[:ans_start])
    ansblock = '\n'.join(pages[ans_start:])
    answers = [CIRC[c] for c in ansblock if c in CIRC]

    questions = []; cur = None; cur_subject = ''; expecting = 1
    state = {'mode': 'stem'}
    def flush():
        if cur and cur['opts']: questions.append(cur)
    for raw in body.split('\n'):
        s = raw.strip()
        if not s: continue
        m = SUBJ_RE.match(s)
        if m: cur_subject = clean(m.group(2)); continue
        if SKIP_RE.search(s): continue
        if re.match(r'^\d{1,3}$', s): continue          # 페이지번호
        qm = QSTART.match(s)
        if qm and int(qm.group(1)) == expecting:
            flush()
            cur = {'num': expecting, 'subject': cur_subject, 'stem': clean(qm.group(2)), 'opts': []}
            expecting += 1; state = {'mode': 'stem'}
            continue
        if cur is None: continue
        if s[0] in CIRC:
            add_segment(cur, state, s)          # 보기 시작 줄(한 줄에 여러 보기 가능)
        elif state['mode'] == 'opt' and cur['opts']:
            cur['opts'][-1] = clean(cur['opts'][-1] + ' ' + s)   # 보기 연속줄(중간 ①~⑤는 그대로)
        else:
            cur['stem'] = clean(cur['stem'] + ' ' + s)           # 문제 연속줄
    flush()
    return questions, answers

def build(path, year, rnd, setkey, setlabel, start_id):
    qs, answers = parse_pdf(path)
    recs = []; bad = []
    for i, q in enumerate(qs):
        num = q['num']
        ans = answers[num-1] if num-1 < len(answers) else None
        opts = [clean(o) for o in q['opts']][:4]
        if len(q['opts']) != 4: bad.append(('opts=%d' % len(q['opts']), num))
        if ans is None: bad.append(('noans', num))
        recs.append({'id': start_id + i, 'setKey': setkey, 'setLabel': setlabel,
                     'year': year, 'subjectNorm': q['subject'], 'num': num,
                     'ans': ans, 'exp': '', 'tag': '', 'q': clean(q['stem']), 'opts': opts})
    return recs, answers, bad

if __name__ == '__main__':
    ROOT = r'C:\Users\emacser\Desktop\playground\embeded'
    recs, answers, bad = build(os.path.join(ROOT,'construction-safety','2023년 건설안전기사 제1회 CBT 복원문제.pdf'),
                               2023, 1, '20230101', '2023년 1회', 11514)
    from collections import Counter
    print('questions:', len(recs), '| answers:', len(answers), '| ans distrib:', dict(Counter(answers)))
    print('subjects:', dict(Counter(r['subjectNorm'] for r in recs)))
    print('bad:', bad)
    o = io.open(r'C:\Users\emacser\AppData\Local\Temp\claude\C--Users-emacser-Desktop-playground-embeded\aa9f1027-c09c-4b01-9573-d24bf6945175\scratchpad\sample_2023_1.txt','w',encoding='utf-8')
    for r in recs[:2] + recs[19:22] + recs[118:120]:
        o.write('Q%d [%s] ans=%s\n %s\n'%(r['num'], r['subjectNorm'], r['ans'], r['q']))
        for j,op in enumerate(r['opts']): o.write('   %s %s\n'%('①②③④'[j] if j<4 else '?', op))
        o.write('\n')
    o.close(); print('sample written')
