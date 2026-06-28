# 기사 필기 CBT — 개발/인수인계 문서

여러 국가기술자격 **필기 CBT**(임베디드기사·전기기사·건설안전기사)를 **웹(GitHub Pages) + 안드로이드 WebView 앱**으로 제공하는 프로젝트. 한 개의 자립형 HTML 템플릿을 종목별 데이터로 찍어내는 구조.

> 이어서 작업하는 세션이 가장 먼저 읽을 문서. 파이프라인 상세는 [`tools/PIPELINE.md`](tools/PIPELINE.md), 빌드/배포는 [`tools/BUILD.md`](tools/BUILD.md).

## 1. 현재 상태 (2026-06-28 기준)

| 종목 | 문항 | 회차 | 데이터 | AI해설 | 비고 |
|---|---|---|---|---|---|
| 📘 임베디드기사 | 733 | - | `cbt/index.html`에 인라인 | 712 | 개념 학습 모드 있음(50카드) |
| ⚡ 전기기사 | 2,898 | 29 (2013~2022) | `docs/electric/` | 100% | LaTeX 수식(KaTeX) |
| 🦺 건설안전기사 | 5,634 | 47 (2007~2022) | `docs/gconsafety/` | **53%(진행중)** | gunsys 포맷 |

- 배포 버전: **content/SW VERSION/BUNDLED_CONTENT/versionCode = 16** (v1.16). 전부 같이 올린다.
- 웹: https://emacser0.github.io/certification-study/ (저장소 `emacser0/certification-study`, Pages = `main` `/docs`)
- ⚠️ **미완료 작업**: 건설안전기사 AI 해설 ~47%가 세션 한도로 미생성. 해설 워크플로우 resume → 병합 → 빌드 필요. ([PIPELINE.md §해설](tools/PIPELINE.md) 참고)

## 2. 아키텍처

```
cbt/index.html        ← 단일 자립형 CBT 템플릿(임베디드 데이터 인라인). 모든 기능의 원천.
                         · 풀이(연습/실전)·OMR·채점·리뷰·오답노트·북마크·통계·개념학습·AI질문·다크모드
                         · localStorage 키는 var NS 로 종목별 분리 (임베디드='', 전기='elec_', 건설='cons_')
   │
   ├─ (그대로) → docs/embedded.html        (웹 임베디드, +뒤로가기버튼)
   ├─ tools/build_pages.py 로 데이터 교체 → docs/electric.html   (NS=elec_, +KaTeX, +뒤로가기)
   │                                      → docs/gconsafety.html (NS=cons_, +KaTeX, +뒤로가기)
   └─ android/app/.../assets/index.html = cbt/index.html 복사본 (APK는 임베디드 단독)

docs/index.html       ← 종목 선택 랜딩(셀렉터). embedded/electric/gconsafety.html 로 링크.
docs/sw.js            ← 서비스워커(network-first, 캐시 우회). VERSION 바꾸면 재배포 반영.
docs/version.json     ← OTA 버전. 앱이 이걸 보고 업데이트 배너 표시.
docs/{electric,gconsafety}/{data.json, ai_exp.json, img/}  ← 종목 데이터 + 해설 + 그림크롭
```

- **데이터 형식** (`data.json`): `{questions:[{id,setKey,setLabel,year,subjectNorm,num,q,opts[4],ans,exp,tag}], sets:[...]}`
  - `q`: 마크다운(텍스트+`$LaTeX$`+`![](경로)` 이미지). `opts`: 보기 4개(빈 문자열이면 이미지에 보기 포함된 문항). `ans`: 1~4.
- **AI 해설** (`ai_exp.json`): `{ "<id>": "해설(LaTeX 포함)" }`. 템플릿의 `expFor()`가 `q.exp` 없으면 여기서 찾음.
- **id 대역**: 임베디드 1~733 / 전기 1~399·1000~ / 건설 5000~5119·6000~ (충돌 방지).

## 3. 빌드/배포 한 사이클 (요약)

1. `cbt/index.html` 또는 `docs/*/data.json`·`ai_exp.json` 수정
2. `python tools/fix_math.py && python tools/fix_matrix.py`  ← **AI가 만든 LaTeX는 반드시 새너타이즈**(과다 백슬래시→이탤릭 깨짐 방지)
3. `python tools/build_pages.py`  ← docs/embedded·electric·gconsafety.html 재생성
4. `cp cbt/index.html android/app/src/main/assets/index.html`  (임베디드 본체 바뀐 경우)
5. `docs/version.json` content +1, `docs/sw.js` VERSION +1, `android/app/build.gradle` versionCode/Name +1, `MainActivity.kt` BUNDLED_CONTENT +1  ← **다 같이**
6. APK 빌드(아래) → `git add -A && commit && push`

자세히: [`tools/BUILD.md`](tools/BUILD.md)

## 4. 환경 (이 PC)

- Android SDK: `C:\Android\sdk` / Gradle: `C:\Android\gradle-8.9\bin\gradle.bat` / Java 21
- APK 빌드: `gradle.bat -p <repo>/android assembleDebug --no-daemon` → `android/app/build/outputs/apk/debug/app-debug.apk`
- Python 패키지: `pymupdf`(fitz), `Pillow`(PIL), `katex`(npm, 검증용) 설치됨. PDF 텍스트 추출은 **pymupdf만** 한글 됨(pdftotext는 안 됨).
- git remote(SSH): `git@github.com:emacser0/certification-study.git`. push는 `GIT_SSH_COMMAND="ssh -o BatchMode=yes" git push`.
- 콘솔 인코딩: 한글 출력 시 `PYTHONIOENCODING=utf-8` 필요(cp949 에러 방지). 파일로 써서 Read 하는 게 안전.

## 5. 핵심 관례

- **버전은 5곳 동시**(content/version.json, sw.js VERSION, build.gradle versionCode+versionName, MainActivity BUNDLED_CONTENT). OTA·SW 캐시·APK 업데이트가 모두 이 숫자에 의존.
- **수식**: AI 생성 LaTeX는 백슬래시를 이중 이스케이프(`\\dfrac`)하는 버그가 잦음 → `tools/fix_math.py`로 `\\`→`\` 축소, `$..$` 내 한글은 `\text{}`로 감쌈, 행렬 행구분자는 `tools/fix_matrix.py`로 복원. **node로 KaTeX 렌더 검증** 권장.
- **이미지 최소화**: 전사로 텍스트화 가능한 문항은 텍스트로, 그림 필수 문항만 크롭 이미지 유지 → repo 가벼움.
- **커밋 트레일러**: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` + `Claude-Session: ...`.

## 6. 다음에 할 만한 일 (TODO)

- [ ] **건설 해설 나머지 47% 완성** (resume → merge → build). [PIPELINE.md §해설](tools/PIPELINE.md)
- [ ] 호스팅 개선: 이미지 R2/CDN 분리, KaTeX 오프라인 번들(현재 CDN이라 첫 접속 시 인터넷 필요)
- [ ] 앱(APK)에도 종목 선택 화면 번들(현재 앱은 임베디드 단독, 뒤로가기 버튼 없음)
- [ ] AI 전사/해설 품질 점검(드물게 오타·오답 해설 가능)
