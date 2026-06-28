# 기사 필기 CBT — 개발/인수인계 문서

여러 국가기술자격 **필기 CBT**(임베디드기사·전기기사·건설안전기사)를 **웹(GitHub Pages) + 안드로이드 WebView 앱**으로 제공. 한 개의 자립형 HTML 템플릿을 종목별 데이터로 찍어내는 구조.

> 이어서 작업하는 세션이 가장 먼저 읽을 문서. 작업 규칙·문서 갱신 규칙은 루트 [`CLAUDE.md`](CLAUDE.md). 파이프라인은 [`tools/PIPELINE.md`](tools/PIPELINE.md), 빌드/배포는 [`tools/BUILD.md`](tools/BUILD.md).

## 1. 현재 상태 (2026-06-29 기준, content 34)

| 종목 | 문항 | 회차 | 데이터 위치 | AI해설 | 개념학습 |
|---|---|---|---|---|---|
| 📘 임베디드기사 | 733 | - | `cbt/index.html` 인라인 + `docs/embedded/concepts.json` | ✅ | 5과목×16=80 |
| ⚡ 전기기사 | 2,898 | 29 (2013~2022) | `docs/electric/` | ✅ | 5과목×16=80 |
| 🦺 건설안전기사 | 6,474 | 54 (2007~2024) | `docs/consafety/` | ✅ | 6과목×16=96 |

- 총 **약 10,105문항**, 전 문항 AI 해설 + 종목별 개념학습.
- 웹: https://emacser0.github.io/certification-study/ — 배포 버전 **content 34 / sw v34**. 앱: v1.26(versionCode 26), `BUNDLED_CONTENT=24`.
- 기능: 연습/🎯실전 시험 모드(과목수×30분·합격판정), 🗓오늘의 5문제, 📚개념학습→관련문제, 오답노트·북마크·통계, AI 질문하기(GPT/Gemini/Claude), 다크모드, 회차 최신순, 패치노트 페이지.

## 2. 아키텍처

```
cbt/index.html        ← 단일 자립형 CBT 템플릿(임베디드 데이터·전 기능 인라인). 모든 기능의 원천.
   │                     localStorage 키는 var NS 로 종목 분리(임베디드='', 전기='elec_', 건설='cons_')
   ├─ build_pages.py: add_back(+뒤로가기/__appBack) + concepts 주입 → docs/embedded.html
   ├─ build_pages.py: DATA/AI_EXP/CONCEPTS 교체 +KaTeX +뒤로가기 → docs/electric.html (NS=elec_)
   │                                                              → docs/consafety.html (NS=cons_)
   └─ docs/ 전체를 android assets로 복사 → APK도 선택화면→3종 CBT 오프라인(멀티페이지)

docs/index.html       ← 종목 선택 랜딩 + 모바일 앱 다운로드 버튼 + 버전/패치노트 링크
docs/changelog.html   ← 패치노트(version.json의 changelog 렌더)
docs/sw.js            ← 서비스워커(network-first). VERSION 바꾸면 웹 재배포 반영.
docs/version.json     ← OTA 버전(content) + apk 정보 + changelog
docs/manifest.json    ← OTA용 파일별 sha1(make_manifest.py 생성). 앱이 바뀐 파일만 받음.
docs/app/cbt-latest.apk  ← 배포용 APK(모바일 다운로드 버튼이 이걸 가리킴)
docs/{electric,consafety,embedded}/{data.json, ai_exp.json, concepts.json, img/}
```

- **data.json**: `{questions:[{id(int),setKey,setLabel,year,subjectNorm,num,q,opts[4],ans(1~4),exp,tag}], sets:[{key,label,count,gradable}]}`
  - `q`: 마크다운(텍스트+`$LaTeX$`+`![](consafety/img/...)` 이미지). 그림문항은 `q`에 이미지, 보기는 텍스트(또는 표 문항이면 `opts=['①','②','③','④']`).
  - `setKey`: 8자리 정렬키(YYYYMMDD 또는 합성 `YYYYRR01`). `subjectNorm`: 정확한 과목명 문자열(개념/필터가 이걸로 매칭).
- **ai_exp.json**: `{"<id>": "해설"}`. 템플릿 `expFor()`가 `q.exp` 없으면 여기서 찾음.
- **concepts.json**: `{"과목명": [{title, note(마크다운+LaTeX), qids:[연결 문제 id]}]}`. 홈 "📚 개념 학습" 카드.
- **id 대역**(충돌 방지): 임베디드 1~733 / 전기 1000~ / 건설 5000~6499. 새 건설 회차는 11514~12353 사용 중 → 다음은 12354+.
- **OTA**: 앱은 `file:///android_asset/` 로드 + `MainActivity.shouldInterceptRequest`가 `filesDir/web/<경로>`에 받아둔 파일을 우선 서빙. 실행 시 `version.json` 확인→`content>BUNDLED_CONTENT`면 `manifest.json` 받아 바뀐 파일만 다운로드. file:// origin 유지로 진행기록 보존.

## 3. 흔한 작업 방법

### A. 회차(기출 PDF) 추가
1. PDF를 `construction-safety/`(또는 `electric/`)에 둔다.
2. **텍스트 추출 가능 PDF**(한솔 CBT 복원 등): `tools/parse_cons_cbt.py` 류 텍스트 파서로 문항/보기/정답표/과목 파싱. 2단·페이지푸터·문항내 ①~⑤ 처리 주의. 그림문항은 컬럼 단위 크롭(raster 교차) → `docs/consafety/img/fig_cbt<setkey>_q<num>.png`.
3. **폰트 깨진 PDF**: 페이지를 200dpi 렌더 → 다중 비전 에이전트가 전사(2단 읽기순서). 정답표가 표준 ①②③④면 텍스트로, 깨졌으면 렌더 이미지에서 직접 판독. 과목은 표준 6과목 블록(1-20,21-40,…)으로 배정.
4. 레코드 `data.json`에 append + `sets`에 추가(setKey 합성 `YYYYRR01`, setLabel "YYYY년 N회"), id는 기존 max+1부터.
5. (선택) AI 해설: `{id,subj,q,opts,ans}` 청크로 다중 에이전트 → `ai_exp.json` 병합. **LaTeX/백슬래시 금지 지시**로 JSON 깨짐 예방.
6. `python tools/build_pages.py` → `node --check` 검증 → **버전 올리기(§CLAUDE.md 규칙)** → 커밋·푸시.

### B. 새 종목 추가
1. 데이터를 `docs/<slug>/data.json`(+`ai_exp.json`,`concepts.json`,`img/`)로 만든다(§3A 방식).
2. `tools/build_pages.py`에 `make_app(...)` 호출 추가(슬러그·NS·타이틀·헤더·footer·ai_exp·concepts 경로). NS는 새 접두어.
3. `docs/index.html` 종목 선택에 카드 추가(href=`<slug>.html`, 배지 문항수).
4. `docs/sw.js`의 SHELL, `MainActivity.kt` 주석 멀티페이지 목록에 추가. APK 빌드시 assets 동기화 대상에 포함(BUILD.md).
5. 버전 올리고 배포. (앱에 새 페이지가 보이려면 APK 재빌드 필요 — assets 번들. 웹은 즉시.)

### C. 폴리싱(기능/UI 수정)
- 전부 `cbt/index.html`에서 수정 → `build_pages.py`로 3종 반영(임베디드 inline 데이터는 그대로 복사됨).
- 거대 파일이라 Read 도구 실패 가능 → Grep/`sed`로 위치 확인, Python `replace`(count 단언)로 패치.
- 웹 전용 요소(뒤로가기 버튼/__appBack/KaTeX)는 `build_pages.py`의 `add_back`/`KATEX_*`에서 주입.
- 항상 `node --check`로 3페이지 JS 검증 후 버전 올려 배포.

## 4. 핵심 관례 / 함정
- **버전 5요소**: `version.json content` · `sw.js VERSION` · `build.gradle versionCode/Name` · `MainActivity BUNDLED_CONTENT`. 콘텐츠만이면 앞 둘 + `make_manifest`. 앱코드면 전부.
- **수식**: AI LaTeX 과다 백슬래시→`fix_math.py`(`\\`→`\`, `$`내 한글 `\text{}`), 행렬 행구분자→`fix_matrix.py`. 임베디드/전기/건설 모두 KaTeX 사용(build_pages가 주입). KaTeX는 CDN(jsdelivr) — 완전 오프라인 시 수식 미렌더(개선 여지).
- **JSON 깨짐**: 에이전트 산출 JSON은 미이스케이프 따옴표/백슬래시로 깨질 수 있음 → 복구 함수(따옴표 스캔) 또는 재생성. 해설 생성은 "백슬래시 금지, 수식은 a/b·m^2" 지시가 안전.
- **그림 최소화**: 텍스트화 가능한 문항은 텍스트로, 그림 필수만 크롭 이미지.

## 5. TODO / 개선 여지
- [ ] 새 건설 회차(840문항) AI해설 품질 점검(OCR 전사라 드물게 오타 가능).
- [ ] 2023년 3회·2024년 4회 등 빠진 회차 PDF 확보 시 추가.
- [ ] KaTeX 로컬 번들(현재 CDN — 오프라인 수식 미표시). `docs/vendor/katex` 활용해 head를 로컬로 바꾸면 됨.
- [ ] 이미지 호스팅 분리(repo가 docs 이미지로 커짐). 
- [ ] `tools/parse_cons_cbt.py`·OCR 조립 스크립트를 `tools/`에 정식 편입(현재 일부는 세션 scratchpad 기반).
