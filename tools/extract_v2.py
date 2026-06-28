# -*- coding: utf-8 -*-
import fitz, re, os, io
from PIL import Image

ANS_MARKS = {'❶':1,'❷':2,'❸':3,'❹':4}
SUBJ_RE = re.compile(r'([1-9])\s*과목\s*[:：]\s*([가-힣A-Za-z·\s]+)')
QNUM_RE = re.compile(r'^(\d{1,3})\.$')
PAGE_TOP = 46
DPI = 150

def col_x(W, col):
    cm = W/2
    return (8, cm-2) if col == 0 else (cm+2, W-8)

def analyze(pdf_path):
    doc = fitz.open(pdf_path)
    qmarks = []; headers = []; ansmarks = []
    dims = []
    for pno in range(doc.page_count):
        p = doc[pno]; W, H = p.rect.width, p.rect.height; cm = W/2
        dims.append((W, H))
        for b in p.get_text("dict")['blocks']:
            for l in b.get('lines', []):
                t = ''.join(s['text'] for s in l['spans'])
                m = SUBJ_RE.search(t)
                if m:
                    x = l['bbox'][0]
                    headers.append(((pno, 0 if x < cm else 1, l['bbox'][1]),
                                    re.sub(r'\s+', ' ', m.group(2).strip())))
        for w in p.get_text("words"):
            if QNUM_RE.match(w[4]) and (w[0] < 60 or (cm-20 < w[0] < cm+60)):
                qmarks.append({'num': int(QNUM_RE.match(w[4]).group(1)), 'page': pno,
                               'col': 0 if w[0] < cm else 1, 'y': w[1]})
            for ch, v in ANS_MARKS.items():
                if ch in w[4]:
                    ansmarks.append({'page': pno, 'col': 0 if w[0] < cm else 1,
                                     'y': (w[1]+w[3])/2, 'v': v})
    qmarks.sort(key=lambda q: (q['page'], q['col'], q['y']))
    headers.sort(key=lambda h: h[0])
    return doc, qmarks, headers, ansmarks, dims

def slots_between(a, b, dims):
    (pa, ca, ya), (pb, cb, yb) = a, b
    res = []; cur = (pa, ca); guard = 0
    while guard < 12:
        guard += 1
        p, c = cur
        ytop = ya if (p, c) == (pa, ca) else PAGE_TOP
        if (p, c) == (pb, cb):
            res.append((p, c, ytop, yb)); break
        res.append((p, c, ytop, dims[p][1]-30))
        cur = (p, 1) if c == 0 else (p+1, 0)
        if cur[0] >= len(dims): break
    return res

def render_question(doc, slots, dims):
    imgs = []
    for (p, c, ytop, ybot) in slots:
        if ybot - ytop < 6:
            continue
        W, H = dims[p]; x0, x1 = col_x(W, c)
        rect = fitz.Rect(x0, ytop-3, x1, ybot)
        pix = doc[p].get_pixmap(clip=rect, dpi=DPI)
        imgs.append(Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB"))
    if not imgs:
        return None
    w = max(im.width for im in imgs)
    h = sum(im.height for im in imgs) + (len(imgs)-1)*6
    canvas = Image.new("RGB", (w, h), "white")
    y = 0
    for im in imgs:
        canvas.paste(im, (0, y)); y += im.height + 6
    return canvas

def detect_ans(slots, ansmarks):
    for (p, c, ytop, ybot) in slots:
        for a in ansmarks:
            if a['page'] == p and a['col'] == c and ytop-3 <= a['y'] <= ybot+3:
                return a['v']
    return None

def process_v2(pdf_path, out_dir, prefix, want_images=True):
    doc, qmarks, headers, ansmarks, dims = analyze(pdf_path)
    if want_images:
        os.makedirs(out_dir, exist_ok=True)
    def subj_for(q):
        s = ''; k = (q['page'], q['col'], q['y'])
        for hk, name in headers:
            if hk <= k: s = name
            else: break
        return s
    out = []
    for i, q in enumerate(qmarks):
        a = (q['page'], q['col'], q['y'])
        if i+1 < len(qmarks):
            nq = qmarks[i+1]; b = (nq['page'], nq['col'], nq['y'])
        else:
            b = (q['page'], q['col'], dims[q['page']][1]-30)
        slots = slots_between(a, b, dims)
        ans = detect_ans(slots, ansmarks)
        rec = {'num': q['num'], 'subject': subj_for(q), 'ans': ans}
        if want_images:
            img = render_question(doc, slots, dims)
            fn = f'{prefix}_q{q["num"]}.png'
            if img:
                img.save(os.path.join(out_dir, fn))
                rec['img'] = fn
        out.append(rec)
    out.sort(key=lambda r: r['num'])
    return out

if __name__ == '__main__':
    import sys
    out = process_v2(sys.argv[1], sys.argv[2], sys.argv[3], want_images=(sys.argv[4]=='img'))
    print('q:', len(out), 'answers:', sum(1 for r in out if r['ans']))
    print('missing ans:', [r['num'] for r in out if not r['ans']])
