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

## 건설 해설 미완성분 이어서 하기 (지금의 TODO)

해설 워크플로우가 세션 한도로 ~47% 실패함. **resume** 하면 성공 청크는 캐시, 실패분만 재생성:

```
Workflow({ scriptPath: ".../workflows/scripts/explain-construction-all-wf_b34953ce-65f.js",
           resumeFromRunId: "wf_b34953ce-65f" })
```
(스크립트/runId가 사라졌으면 `tools/PIPELINE.md`의 프롬프트로 새 워크플로우를 만들되, **이미 해설 있는 id는 제외**하고 청크 구성 — `docs/gconsafety/ai_exp.json` 키 제외.)

완료 후:
```python
# 병합: consexp2/out_*.json → 기존 ai_exp.json에 합치기 (id→exp)
# 그다음 fix_math.py, fix_matrix.py → build_pages.py → 버전+1 → 커밋
```

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
