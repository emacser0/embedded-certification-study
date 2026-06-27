# 임베디드기사 필기 CBT — Android 앱

기존 자립형 웹앱(`cbt/index.html`)을 그대로 안드로이드 **WebView 앱**으로 감싼 프로젝트입니다.
문제 733개와 이미지 44개가 앱 안에 모두 번들되어 있어 **인터넷 연결 없이 오프라인**으로 동작합니다.

## 구조

```
android/
├─ app/
│  └─ src/main/
│     ├─ assets/
│     │  ├─ index.html          ← CBT 웹앱(문제 데이터 포함)
│     │  └─ images/             ← 문제 이미지 44개 (questions.db에서 추출)
│     ├─ java/com/embedded/cbt/MainActivity.kt   ← WebView 1개짜리 액티비티
│     ├─ res/                   ← 아이콘 / 테마 / 문자열
│     └─ AndroidManifest.xml
│  └─ build.gradle
├─ build.gradle, settings.gradle, gradle.properties
└─ gradle/wrapper/gradle-wrapper.properties
```

## 빌드 방법 (가장 쉬운 길: Android Studio)

1. **Android Studio**(Koala 이상 권장)를 설치합니다.
2. `File → Open` 에서 이 `android` 폴더를 엽니다.
3. 처음 열면 Gradle 동기화가 자동으로 진행됩니다. (인터넷 필요 — 의존성 다운로드)
   - Gradle Wrapper jar가 없다고 나오면 Android Studio가 자동 생성하거나,
     `Sync Project with Gradle Files` 버튼을 누르면 됩니다.
4. 상단의 ▶(Run) 버튼으로 에뮬레이터/실기기에 바로 설치·실행합니다.

### APK 파일로 뽑기
- 디버그용: `Build → Build App Bundle(s) / APK(s) → Build APK(s)`
  → `app/build/outputs/apk/debug/app-debug.apk`
- 배포(서명)용: `Build → Generate Signed Bundle / APK` 에서 키스토어를 만들어 서명.

### 커맨드라인으로 빌드 (Android SDK 설치되어 있을 때)
```bash
cd android
./gradlew assembleDebug      # Windows: gradlew.bat assembleDebug
# 결과: app/build/outputs/apk/debug/app-debug.apk
```
> 참고: 이 저장소에는 `gradlew` 래퍼 jar가 포함되어 있지 않습니다.
> Android Studio로 한 번 열거나, gradle이 설치돼 있으면 `gradle wrapper`로 생성하세요.

## 주요 설정
- `applicationId` : `com.embedded.cbt`
- `minSdk 26` (Android 8.0+) / `targetSdk 34`
- 세로 고정, 뒤로가기 버튼은 웹앱 내 화면 이동에 연동

## 데이터 갱신 방법
문제/이미지를 새로 반영하려면:
1. 원본 `cbt/index.html` 을 `app/src/main/assets/index.html` 로 복사
2. 이미지가 바뀌었다면 `questions.db` 의 `images` 테이블에서 다시 추출해
   `app/src/main/assets/images/` 에 덮어쓰기
