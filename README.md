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

---
데이터: 연도별 기출 + 2025 복원본 · 로컬 전용 학습 도구
