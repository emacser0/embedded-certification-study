# 임베디드기사 필기 CBT (Embedded Engineer Written Exam · Study App)

대한민국 **임베디드기사 필기** 시험 대비 CBT(Computer-Based Testing) 학습 도구입니다.
연도별 기출 + 2025 복원본 **733문항**(이미지 44개 포함)을 담고 있으며, **웹**과 **안드로이드 앱**에서 동일하게 동작합니다.

## 구성

| 경로 | 설명 |
|---|---|
| `cbt/index.html` | 자립형(self-contained) 웹 CBT 앱. 문제 데이터가 내장되어 인터넷 없이 동작. |
| `android/` | 위 HTML을 감싼 안드로이드 WebView 앱 (Android Studio 프로젝트). 빌드 방법은 `android/README.md`. |
| `questions.db` | 원본 SQLite DB (`questions`, `images` 테이블). 앱 데이터의 원천. |
| `2025년도_임베디드기사_필기_복원(오류_수정본).pdf` | 2025 복원 원본 PDF. |
| `links.txt` | 연도별 기출 출처(Notion) 링크. |

## 기능

- **풀이 모드**: 연습(즉시 정답 확인) / 실전, OMR 답안지, 경과·**카운트다운 제한시간**, 보기 순서 섞기
- **채점**: 점수·합격 예상(60점 + 과목 40% 과락), 과목별 결과, 문제 리뷰(틀린 문제만 보기)
- **복습**: 진행상황 자동저장·이어풀기, **오답노트(누적)**, **북마크**, 틀린 문제만 다시 풀기
- **분석/탐색**: 누적 학습 통계·취약 과목, 과목/유형별 학습, 키워드 검색
- **편의**: 다크 모드, 키보드 단축키(←/→, 1~4), **문제를 AI 질문 형태로 클립보드 복사**
- 모든 학습 기록은 브라우저/기기의 `localStorage`에 로컬 저장

## 웹으로 실행

`cbt/index.html` 을 브라우저로 열면 됩니다. (이미지가 보이려면 `questions.db`의 이미지가 `cbt/images/` 로 추출되어 있어야 합니다. 안드로이드 빌드에는 이미 번들됨.)

## 안드로이드 앱

`android/README.md` 참고. Android Studio로 `android` 폴더를 열어 빌드하거나, SDK가 있으면 `gradle assembleDebug`.

## 콘텐츠 OTA 업데이트 (앱 재설치 없이 갱신)

앱은 실행 시 GitHub Pages의 `version.json`을 확인해, 더 새로운 콘텐츠가 있으면 화면 하단에
**"지금 업데이트" 배너**를 띄웁니다. 탭하면 최신 `index.html`을 받아 내부저장소에 저장하고 즉시
새로고침합니다(설치창 없음). 이미지는 APK에 번들된 것을 사용하므로 깨지지 않습니다.

### 최초 1회 설정 — GitHub Pages 켜기
1. 저장소를 GitHub에 푸시
2. **Settings → Pages → Source: `Deploy from a branch` → `main` / `/docs`** 저장
3. 잠시 후 `https://emacser0.github.io/certification-study/` 에서 `version.json`·`index.html` 제공됨
   - 이 URL은 `MainActivity.kt`의 `BASE` 상수와 일치해야 합니다.

### 콘텐츠 업데이트를 배포하는 방법 (APK 재빌드 불필요)
1. `cbt/index.html` 수정
2. `docs/index.html` 로 복사 (`cp cbt/index.html docs/index.html`)
3. `docs/version.json` 의 `content` 값을 +1 (예: 1 → 2)
4. `git add docs && git commit && git push`
→ 다음 앱 실행 시 사용자에게 업데이트 배너가 뜸. (이미지를 새로 추가했다면 그 이미지는 APK 갱신이 필요)

### 네이티브(Kotlin)·이미지가 바뀌는 경우
콘텐츠 OTA로는 안 되고 **새 APK 배포**가 필요합니다. 이때 `MainActivity.kt`의 `BUNDLED_CONTENT` 를
새 `content` 값으로 올려 빌드하면, 구버전 OTA본을 덮어쓰고 번들 콘텐츠가 우선 적용됩니다.

---
데이터: 연도별 기출 + 2025 복원본 · 로컬 전용 학습 도구
