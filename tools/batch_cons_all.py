# -*- coding: utf-8 -*-
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))
import fitz
from extract_v2 import process_v2

CROOT = r'C:\Users\emacser\Desktop\playground\embeded\construction-safety'
IMGOUT = r'C:\Users\emacser\Desktop\playground\embeded\docs\gconsafety\img'
STAGE = os.path.join(os.path.dirname(__file__), 'cons_new_questions.json')
DONE = {'20220424'}

SUBJ_HDR = re.compile(r'【?\s*([1-9])\s*과목')

def parse_answers(pdf):
    """page1 정답표 파싱: qnum -> ans"""
    doc = fitz.open(pdf)
    p = doc[0]
    toks = []
    for w in p.get_text("words"):
        t = w[4].strip()
        if re.fullmatch(r'\d{1,3}', t):
            toks.append((round(w[1], 1), round((w[0]+w[2])/2, 1), int(t)))
    toks.sort()
    rows = []; cur = []; last = None
    for y, x, v in toks:
        if last is None or abs(y-last) <= 6:
            cur.append((x, v))
        else:
            rows.append((last, sorted(cur))); cur = [(x, v)]
        last = y
    if cur:
        rows.append((last, sorted(cur)))
    ans = {}
    for i, (y, row) in enumerate(rows):
        vals = [v for x, v in row]
        if len(row) >= 8 and (max(vals)-min(vals)) == len(set(vals))-1 and (max(vals)-min(vals)) >= 7 and min(vals) >= 1:
            if i+1 < len(rows):
                ar = rows[i+1][1]
                for hx, hv in row:
                    best = min(ar, key=lambda a: abs(a[0]-hx))
                    if abs(best[0]-hx) < 14 and 1 <= best[1] <= 4:
                        ans[hv] = best[1]
    return ans

def parse_subjects(pdf):
    """page1 좌측에서 과목명 6개를 순서대로 (range 매핑은 호출측에서)"""
    doc = fitz.open(pdf)
    p = doc[0]
    names = []
    lines = []
    for b in p.get_text("dict")['blocks']:
        for l in b.get('lines', []):
            t = ''.join(s['text'] for s in l['spans']).strip()
            x0 = l['bbox'][0]; y0 = l['bbox'][1]
            lines.append((y0, x0, t))
    lines.sort()
    # 과목 헤더 위치를 찾고, 그 근처 좌측 텍스트(숫자/과목/문제 제외)를 과목명으로
    for i, (y, x, t) in enumerate(lines):
        if SUBJ_HDR.search(t) and x < 240:
            # 같은/다음 줄에서 과목명 후보
            cand = SUBJ_HDR.sub('', t)
            cand = re.sub(r'[【】:：()0-9문제\s]', '', cand)
            nm = ''
            # 다음 몇 줄에서 한글 이름
            for j in range(i, min(i+3, len(lines))):
                tt = lines[j][2]
                m = re.search(r'([가-힣][가-힣\s·및]+[가-힣])', re.sub(r'【[^】]*】', '', tt))
                if m and '과목' not in m.group(1) and '문제' not in m.group(1):
                    nm = m.group(1).strip(); break
            names.append(nm)
    return names

def label_of(d):
    return f'{d[:4]}-{d[4:6]}-{d[6:8]}'

if __name__ == '__main__':
    test = len(sys.argv) > 1 and sys.argv[1] == 'test'
    pdfs = sorted(f for f in os.listdir(CROOT) if f.endswith('.pdf'))
    pdfs = [f for f in pdfs if f[len('gconsafety_'):-4] not in DONE]
    if test:
        for f in pdfs[:1] + pdfs[len(pdfs)//2:len(pdfs)//2+1] + pdfs[-1:]:
            pdf = os.path.join(CROOT, f)
            ans = parse_answers(pdf)
            subs = parse_subjects(pdf)
            doc = fitz.open(pdf)
            qmarks = process_v2(pdf, '', 'x', want_images=False)
            print(f, '| pages', doc.page_count, '| qmarks', len(qmarks), '| answers', len(ans),
                  '| maxq', max(ans) if ans else 0, '| subjects', subs)
        sys.exit(0)
    # full run
    os.makedirs(IMGOUT, exist_ok=True)
    all_new = []; qid = 6000; summary = []
    STD = ['산업안전관리론', '산업심리 및 교육', '인간공학 및 시스템안전공학', '건설시공학', '건설재료학', '건설안전기술']
    for f in pdfs:
        date = f[len('gconsafety_'):-4]
        pdf = os.path.join(CROOT, f)
        try:
            ans = parse_answers(pdf)
            subs = parse_subjects(pdf)
            out = process_v2(pdf, IMGOUT, 'gc'+date, want_images=True)
        except Exception as ex:
            summary.append((date, 'ERR '+str(ex)[:50], 0)); continue
        maxq = max(ans) if ans else 120
        per = max(1, round(maxq/6))
        def subj_of(n):
            idx = min((n-1)//per, 5)
            if len(subs) == 6 and subs[idx]:
                return subs[idx]
            return STD[idx]
        kept = 0; seen = set()
        for r in out:
            if 'img' not in r:
                continue
            n = r['num']
            if n not in ans or n in seen:   # 가짜/중복 마커 제거
                if os.path.exists(os.path.join(IMGOUT, r['img'])):
                    os.remove(os.path.join(IMGOUT, r['img']))
                continue
            seen.add(n)
            all_new.append({'id': qid, 'setKey': date, 'setLabel': label_of(date), 'year': int(date[:4]),
                            'subjectNorm': subj_of(n), 'num': n, 'ans': ans[n], 'img': r['img']})
            qid += 1; kept += 1
        summary.append((date, len(out), kept, len(ans)))
    json.dump(all_new, open(STAGE, 'w', encoding='utf-8'), ensure_ascii=False)
    for s in summary:
        print(' ', s)
    print('NEW construction questions:', len(all_new))
