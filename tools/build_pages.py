# -*- coding: utf-8 -*-
import re, json, os

ROOT = r'C:\Users\emacser\Desktop\playground\embeded'
src = open(os.path.join(ROOT, 'cbt', 'index.html'), encoding='utf-8').read()

def inject_before_last_script(html, code):
    """메인 앱 스크립트(마지막 </script>) 직전에만 코드 주입 (head의 외부 스크립트 태그는 건드리지 않음)"""
    i = html.rfind('</script>')
    return html[:i] + code + html[i:] if i != -1 else html

KATEX_HEAD = (
  '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">\n'
  '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>\n'
  '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" '
  'onload="window.__katexReady=true;window.__rerenderMath&&window.__rerenderMath();"></script>\n'
)
KATEX_PATCH = (
  '\n/* KaTeX: 렌더 후 $..$ 수식 변환 */\n'
  'function __km(el){if(el&&window.renderMathInElement){try{renderMathInElement(el,{delimiters:['
  "{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false});}catch(e){}}}\n"
  "window.__rerenderMath=function(){['quiz','results','study','home'].forEach(function(id){__km(document.getElementById(id));});};\n"
  "['renderQ','renderReview','showStudy','renderResults'].forEach(function(nm){var o=window[nm];"
  'if(typeof o==="function"){window[nm]=function(){var r=o.apply(this,arguments);__km(document.body);return r;};}});\n'
)

def add_back(e):
    """상황별 뒤로가기 버튼 (웹 전용): CBT 홈이면 종목 선택(index.html), 시험/학습/결과 화면이면 CBT 홈"""
    e = e.replace('<header class="top">',
                  '<header class="top">\n  <button id="backBtn" class="btn ghost backsel" onclick="backNav()" title="뒤로">← 종목</button>')
    e = e.replace('</style>', '  .backsel{padding:7px 11px;font-size:13px;white-space:nowrap}\n</style>')
    back_js = (
        '\n/* 상황별 뒤로가기: 홈이면 종목 선택, 그 외(시험/학습/결과)면 CBT 홈 */\n'
        'function backNav(){var h=document.getElementById("home");'
        'if(h&&!h.classList.contains("hide")){location.href="index.html";}'
        'else if(window.goHome){goHome();}}\n'
        '/* 앱 하드웨어 뒤로가기: 시험/학습/결과 화면이면 CBT 홈, CBT 홈이면 종목 선택. 항상 handled(앱이 임의로 종료/뒤로가지 않도록). */\n'
        'window.__appBack=function(){var h=document.getElementById("home");'
        'if(h&&!h.classList.contains("hide")){location.href="index.html";return "handled";}'
        'if(window.goHome){goHome();}return "handled";};\n'
        '(function(){var o=window.show;if(typeof o==="function"){window.show=function(){'
        'var r=o.apply(this,arguments);var b=document.getElementById("backBtn");'
        'if(b)b.textContent=(arguments[0]==="home")?"\\u2190 \\uc885\\ubaa9":"\\u2190 \\ub4a4\\ub85c";'
        'return r;};}})();\n'
    )
    e = inject_before_last_script(e, back_js)
    return e

def make_app(data_path, out_html, ns, html_title, header_html, footer_text, ai_exp_path=None, katex=True, concepts_path=None):
    data = json.load(open(data_path, encoding='utf-8'))
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    e = src
    e = re.sub(r'(?m)^var DATA = .*$', lambda m: 'var DATA = ' + js + ';', e)
    aejs = '{}'
    if ai_exp_path and os.path.exists(ai_exp_path):
        aejs = json.dumps(json.load(open(ai_exp_path, encoding='utf-8')), ensure_ascii=False, separators=(',', ':'))
    e = re.sub(r'(?m)^var AI_EXP = .*$', lambda m: 'var AI_EXP = ' + aejs + ';', e)
    cjs = '{}'
    if concepts_path and os.path.exists(concepts_path):
        cjs = json.dumps(json.load(open(concepts_path, encoding='utf-8')), ensure_ascii=False, separators=(',', ':'))
    e = re.sub(r'(?m)^var CONCEPTS = .*$', lambda m: 'var CONCEPTS = ' + cjs + ';', e)
    e = e.replace("var NS='';", "var NS='%s';" % ns)
    e = e.replace('<title>임베디드기사 필기 CBT</title>', '<title>%s</title>' % html_title)
    e = e.replace('📘 임베디드기사 필기 CBT', header_html)
    e = e.replace('임베디드기사 필기 CBT · 데이터: 연도별 기출 + 2025 복원본 · 로컬 전용', footer_text)
    e = e.replace('</style>', '  .katex{font-size:1.05em}\n  .qbody .katex-display{margin:8px 0}\n</style>')
    if katex:
        e = e.replace('</head>', KATEX_HEAD + '</head>')
        e = inject_before_last_script(e, KATEX_PATCH)
    e = add_back(e)
    open(out_html, 'w', encoding='utf-8').write(e)
    return len(data['questions']), data['sets']

# 임베디드 웹: 종목 선택 버튼 + 개념 학습(concepts.json) 주입 (APK용 cbt/index.html 원본은 그대로 둠)
emb = add_back(src)
emb_cp = os.path.join(ROOT, 'docs', 'embedded', 'concepts.json')
if os.path.exists(emb_cp):
    _ecjs = json.dumps(json.load(open(emb_cp, encoding='utf-8')), ensure_ascii=False, separators=(',', ':'))
    emb = re.sub(r'(?m)^var CONCEPTS = .*$', lambda m: 'var CONCEPTS = ' + _ecjs + ';', emb)
    print('embedded: concepts injected')
open(os.path.join(ROOT, 'docs', 'embedded.html'), 'w', encoding='utf-8').write(emb)

# 전기기사
nq, sets = make_app(
    os.path.join(ROOT, 'docs', 'electric', 'data.json'),
    os.path.join(ROOT, 'docs', 'electric.html'), 'elec_',
    '전기기사 필기 CBT', '⚡ 전기기사 필기 CBT',
    '전기기사 필기 CBT · 데이터: 연도별 기출(전자문제집 CBT) · 로컬 전용',
    ai_exp_path=os.path.join(ROOT, 'docs', 'electric', 'ai_exp.json'),
    concepts_path=os.path.join(ROOT, 'docs', 'electric', 'concepts.json'))
print('electric:', nq, 'questions,', len(sets), 'sets')

# 건설안전기사
cpath = os.path.join(ROOT, 'docs', 'gconsafety', 'data.json')
if os.path.exists(cpath):
    nq, sets = make_app(
        cpath, os.path.join(ROOT, 'docs', 'gconsafety.html'), 'cons_',
        '건설안전기사 필기 CBT', '🦺 건설안전기사 필기 CBT',
        '건설안전기사 필기 CBT · 데이터: 기출(건시스템 gunsys.com) · 로컬 전용',
        ai_exp_path=os.path.join(ROOT, 'docs', 'gconsafety', 'ai_exp.json'),
        concepts_path=os.path.join(ROOT, 'docs', 'gconsafety', 'concepts.json'))
    print('construction:', nq, 'questions,', len(sets), 'sets')
