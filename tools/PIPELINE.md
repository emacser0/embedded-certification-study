# 데이터 파이프라인 — PDF 기출 → CBT

전기/건설안전은 PDF 기출을 **추출 → 비전 전사(텍스트/LaTeX화) → AI 해설 → 합성**해 만든다.
모든 워크플로우는 **다중 에이전트(general-purpose)가 청크 파일을 직접 Read/Write** 하는 방식 → 데이터가 오케스트레이터 컨텍스트를 거치지 않음.

> 작업 디렉터리(청크/중간산출물)는 세션 scratchpad를 썼다. 새 세션에선 임의의 작업폴더 `WORK=`를 정해 동일하게 쓰면 된다. 스크립트의 절대경로(`C:\Users\emacser\...\scratchpad\...`)는 그 폴더로 바꿀 것.

## 단계 (전기/건설 공통)

### 1) 추출 (로컬, pymupdf) — `tools/extract_v2.py`
- `process_v2(pdf, out_dir, prefix, want_images)` →  각 문항을 **읽기순서 스티칭 크롭**(보기가 다음 컬럼/페이지로 넘치는 레이아웃 대응)으로 PNG 저장 + `{num, subject, ans, img}` 반환.
- 정답 검출: 교사용 PDF의 `❶❷❸❹` 마커(전기). **건설(gunsys)은 1페이지 정답표**라 별도 파싱 → `tools/batch_cons_all.py`의 `parse_answers()`.
- 과목: 전기는 "N과목 : 과목명" 헤더. 건설은 과목명 파싱 실패 시 표준 6과목 범위(1-20,21-40,...) 폴백.
- 배치 예: `tools/batch_remaining.py`(전기), `tools/batch_cons_all.py`(건설). → 크롭 PNG들 + `*_questions.json`(이미지 기반 문항 staging) 생성.

### 2) 비전 전사 (Workflow, 다중 에이전트)
청크 = `[{id, img(절대경로)}]` 8문항씩. 에이전트가 이미지를 Read 해서 아래 JSON을 Write.
출력: `[{id, q, opts[4], figure(bool), figbox([x0,y0,x1,y1]|null)}]`
- `q`/`opts`: 한국어 + 수식은 LaTeX `$...$`. **백슬래시는 한 번만**(과다 이스케이프 금지 — 안 그러면 KaTeX 이탤릭 깨짐).
- `figure`: 회로도/그래프/표 등 그림 필수면 true. `figbox`: 그림 영역 비율.
- 프롬프트 전문은 [§부록 프롬프트](#부록-워크플로우-프롬프트).

### 3) AI 해설 (Workflow, 텍스트)
청크 = `[{id, subj, q(그림은 [그림]로 치환), opts, ans}]` 20문항씩. 출력 `[{id, exp}]`.
- 정답 근거 3~5문장 + 오답 이유 + 법규/공식. 수식 LaTeX `$...$`, **백슬래시 1개만**.

### 4) 합성 — `tools/compose_cons_all.py` (전기는 동형 스크립트)
- 전사 결과 병합: `figure=false`면 q=텍스트, `figure=true`면 q=텍스트+`![](그림크롭)`(figbox로 PIL 크롭한 `fig_*` 이미지), opts=텍스트.
- 정답/과목/회차 메타 결합 → `data.json`. 안 쓰는 풀크롭 이미지는 prune(그림 문항만 남김).

### 5) 새너타이즈 → 빌드
- `python tools/fix_math.py && python tools/fix_matrix.py` (data + ai_exp 모두 대상)
- `python tools/build_pages.py` → 페이지 재생성. [BUILD.md](BUILD.md) 따라 버전 올리고 커밋.

## 한솔 CBT 복원 PDF (2023~ 건설안전 신규 회차) — 두 갈래

기존 gunsys 포맷과 다른 한솔아카데미 "CBT 복원" PDF는 아래로 처리한다. 회차 추가 절차는 [PROJECT.md §3A].

### (가) 텍스트 추출이 되는 PDF — `tools/parse_cons_cbt.py`
- `parse_pdf(path)` → `(questions, answers)`. **2단 레이아웃**·페이지마다 반복되는 면책문 푸터·과목 헤더(`제N과목: 이름`)·문항 끝 정답표를 처리.
  - 정답표 = 뒤쪽의 `qmark==0` 페이지(번호 10개 + ①②③④ 10개 반복) → circled 순서대로 = 정답.
  - 보기 시작은 **줄 첫 글자가 ①②③④일 때만** 분리(지문 속 `①~⑤`는 보기로 오인 금지). 한 줄에 `③..④..`처럼 묶이면 마커로 split.
- **그림문항**: 위치기반(`get_text('words')`의 `N.` 마커)으로 컬럼별 영역을 잡고, 그 영역과 raster 이미지가 겹치면 figure로 판단 → 컬럼 단위로 크롭. 보기까지 표 이미지면(opts 파싱이 4개 아님) 영역 전체를 크롭하고 `opts=['①','②','③','④']`.

### (나) 폰트가 깨져 텍스트가 안 나오는 PDF — 비전 OCR
- 글자는 화면엔 정상 렌더되지만 텍스트 레이어가 깨짐 → 각 콘텐츠 페이지를 200dpi PNG로 렌더.
- 다중 비전 에이전트(페이지 3~4장/에이전트)가 2단 읽기순서로 `[{num,q,opts[4]}]` 전사(백슬래시/LaTeX 금지 지시로 JSON 안정화).
- 정답: 정답표가 표준 ①②③④면 텍스트로, 깨졌으면 **정답표 페이지를 렌더해 직접 판독**. 과목은 표준 6과목 블록(1-20,21-40,…)으로 배정.
- 조립: 전사 병합 + 정답 + 과목 + 그림문항(`[그림]` 표시분만 컬럼 크롭) → `data.json` append. id는 기존 max+1.

> 세션 scratchpad에 `build_cons_new.py`(텍스트 회차 조립)·`assemble_garbled.py`(OCR 조립) 원형이 있음. 재사용 시 `tools/`로 옮기고 절대경로만 바꾼다.

## AI 해설 / 개념 생성 (다중 에이전트)
- **해설**: `{id,label,subject,q,opts,ans}` 청크(약 40문항) → 에이전트가 `{id:exp}` Write → `ai_exp.json` 병합. 해설은 "정답 근거+오답 이유 2~4문장, '따라서 정답은 N번이다.'". **백슬래시/LaTeX 금지**가 JSON 깨짐 예방에 가장 효과적(수식은 a/b·m^2).
- **개념**: 과목별 에이전트가 16개 개념(title/note/keywords) Write → keywords를 문제 지문에 매칭해 qids 연결(`build_concepts` 류) → `concepts.json`. build_pages가 주입(임베디드는 `docs/embedded/concepts.json` 별도 주입).
- 산출 JSON은 미이스케이프 따옴표로 깨지기 쉬움 → 따옴표-스캔 복구 함수 또는 실패 청크만 재생성.

## 검증 (수식)
```bash
npm install katex   # (이미 설치됨, node_modules는 .gitignore)
node -e '...'       # 각 $..$ 스팬을 katex.renderToString(throwOnError:true) → 오류 스팬 출력
```
오류 대부분은 ① 이중 백슬래시(fix_math) ② 행렬 행구분자 소실(fix_matrix) ③ `$` 안 한글(fix_math가 \text{}로 감쌈).

## 부록: 워크플로우 프롬프트

### 전사(통합) 프롬프트 핵심
```
각 img(PNG)를 Read해 전사:
- q: 지문(번호/보기 제외). 수식은 LaTeX $...$.
- opts: 보기 4개(마커 제외).
- figure: 그림 필수면 true / figbox: figure면 [x0,y0,x1,y1](0~1), 아니면 null.
LaTeX 백슬래시는 JSON에서 정확히 \\(이스케이프 1개). 문자열 내 개행 금지. 유효 JSON만.
출력 [{"id","q","opts":[..],"figure":bool,"figbox":[..]|null}] 을 out 파일에 Write.
```

### 해설 프롬프트 핵심
```
[{id,subj,q,opts,ans}] 읽고 각 문제 상세 해설(정답 근거 3~5문장 + 오답 이유 + 법규/공식).
수식 LaTeX $...$, 마크다운 강조·개행 금지(한 단락). 백슬래시 1개만.
출력 [{"id","exp"}] 을 Write.
```

### figbox(그림영역) 별도 추출이 필요할 때
이미지를 보고 그림(도형) 영역만 `[x0,y0,x1,y1]`(0~1 비율, 약간 여백) 반환 → PIL로 크롭.
