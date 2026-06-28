# CLAUDE.md — 세션 작업 지침 (자동 로드)

이 저장소는 국가기술자격 **필기 CBT**(임베디드기사·전기기사·건설안전기사)를 **웹(GitHub Pages) + 안드로이드 WebView 앱**으로 제공한다. 한 개의 자립형 HTML 템플릿(`cbt/index.html`)을 종목별 데이터로 찍어내고, 앱은 같은 `docs/` 번들을 오프라인으로 싣는다.

## 문서 지도 (작업 전 해당 문서를 읽어라)
- **[PROJECT.md](PROJECT.md)** — 현재 상태·아키텍처·"흔한 작업"(회차 추가/종목 추가/폴리싱) 방법. **가장 먼저 읽을 문서.**
- **[tools/BUILD.md](tools/BUILD.md)** — 페이지 생성·APK 빌드·버전 올리기·배포(OTA) 절차.
- **[tools/PIPELINE.md](tools/PIPELINE.md)** — PDF 기출 → 문항 추출/전사/정답/AI해설/개념 파이프라인.

## ★ 문서 자동 갱신 규칙 (이 저장소에서 작업하는 모든 세션이 지킬 것)
작업을 마칠 때, 아래에 해당하면 **반드시 해당 문서를 같은 커밋에서 갱신**한다. 별도 지시가 없어도 알아서 한다.

| 무엇을 바꿨나 | 갱신할 곳 |
|---|---|
| 문항/해설/HTML/기능 등 **콘텐츠 변경** | `docs/version.json`의 `content`+1, `docs/sw.js`의 `VERSION`+1, `python tools/make_manifest.py` 실행, `changelog`에 한 줄 추가, `updated` 시각 갱신 |
| **앱 코드**(MainActivity/gradle 등) 변경 | `versionCode`/`versionName`+1, `MainActivity.kt`의 `BUNDLED_CONTENT`=빌드시 content, APK 재빌드→`docs/app/cbt-latest.apk` 교체, `version.json`의 `apkName`/`apkDate` 갱신 |
| 종목/회차/문항수/기능 등 **현재 상태**가 달라짐 | `PROJECT.md`의 상태표·기능 목록·`종목 선택 카드 배지(docs/index.html)`·이 파일 상단 요약 |
| **추출/전사/해설 파이프라인** 변경·새 스크립트 | `tools/PIPELINE.md` |
| **빌드/배포 절차** 변경 | `tools/BUILD.md` |
| 사용자에게 보이는 변화 | `docs/version.json`의 `changelog` 맨 앞에 항목 추가(이게 앱/웹 패치노트로 노출됨) |

> 콘텐츠만 바뀌면 APK 재배포 불필요 — 설치된 앱이 OTA로 바뀐 파일만 받아간다. 앱 *코드*가 바뀔 때만 APK를 다시 만든다.

## 핵심 관례 (어기지 말 것)
- **버전 의존**: OTA/SW캐시/APK업데이트가 숫자에 의존. 콘텐츠 변경 = `content`+`sw VERSION` 올리고 `make_manifest` 실행. 안 올리면 반영 안 됨.
- **`cbt/index.html`가 단일 원천**(임베디드 데이터·전 기능 인라인). 기능 수정은 여기서 → `tools/build_pages.py`로 3종 페이지 재생성. 이 파일은 거대해서 Read 도구가 실패할 수 있음 → `sed`/Grep으로 부분 확인, Python 스크립트로 패치.
- **AI 생성 LaTeX**: 과다 백슬래시(`\\dfrac`)·미이스케이프 따옴표로 깨지기 쉬움. 데이터/해설 생성 후 `tools/fix_math.py && tools/fix_matrix.py`, 배포 전 `node --check`로 JS 문법 검증.
- **종목별 localStorage 분리**: `var NS`(임베디드='', 전기='elec_', 건설='cons_'). URL/디렉터리를 바꿔도 NS는 유지해 사용자 진행기록 보존.
- **다중 에이전트 패턴**: 대량 생성(전사/해설/개념)은 general-purpose 에이전트가 청크 파일을 Read/Write(데이터가 오케스트레이터 컨텍스트를 안 거침). 깨진 JSON은 따옴표/백슬래시 복구 또는 재생성.
- **콘솔 인코딩**: 한글 출력은 cp949 에러 남 → 파일로 Write 후 Read, 또는 `io.open(...,encoding='utf-8')`.
- **커밋 트레일러**: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` + `Claude-Session: <url>`. push는 `GIT_SSH_COMMAND="ssh -o BatchMode=yes" git push origin main`.
- 배포 후 GitHub Pages 반영(약 30~60초)까지 `curl`로 `version.json`/대상 파일 확인.

## 환경 (이 PC)
- 웹: https://emacser0.github.io/certification-study/ · 저장소 `git@github.com:emacser0/certification-study.git` (Pages = `main` `/docs`)
- Android SDK `C:\Android\sdk`, Gradle `C:\Android\gradle-8.9\bin\gradle.bat`(자세한 빌드는 메모리 `android-build-setup.md`)
- Python: `pymupdf`(fitz)·`Pillow`. PDF 한글 텍스트 추출은 pymupdf만 됨(pdftotext 불가). 일부 PDF는 폰트가 깨져 텍스트 추출 불가 → 렌더 후 비전 OCR.
