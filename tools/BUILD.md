# 빌드 & 배포

## 웹 페이지 생성
```bash
cd <repo>
python tools/build_pages.py
# → docs/embedded.html, docs/electric.html, docs/gconsafety.html 재생성
#    (cbt/index.html 템플릿 + docs/*/data.json + ai_exp.json 주입, NS·KaTeX·뒤로가기버튼 포함)
```
- `build_pages.py`의 `ROOT` 절대경로가 이 PC 기준. 다른 PC면 수정.
- 임베디드 데이터는 `cbt/index.html`에 인라인이라 build_pages가 그대로 복사(+뒤로가기).

## APK 빌드
앱은 docs 웹 전체를 assets로 번들(선택화면→3종 CBT 오프라인). **빌드 전 docs→assets 복사 필수**:
```bash
A=android/app/src/main/assets
rm -rf "$A" && mkdir -p "$A/electric" "$A/gconsafety"
cp docs/index.html docs/embedded.html docs/electric.html docs/gconsafety.html "$A/"
cp -r docs/images "$A/images"
cp -r docs/electric/img "$A/electric/img"
cp -r docs/gconsafety/img "$A/gconsafety/img"
cp -r docs/vendor "$A/vendor"
# (sw.js/data.json은 불필요 — 페이지에 데이터 인라인, 오프라인이라 SW 미사용)

# OTA 기준선: version.json + manifest.json(파일별 sha1)을 생성·복사
python tools/make_manifest.py   # docs/manifest.json 생성 + assets에 version/manifest 복사

# Android SDK/Gradle (이 PC 설치 위치)
ANDROID_HOME=C:\Android\sdk  "C:\Android\gradle-8.9\bin\gradle.bat" \
  -p <repo>/android assembleDebug --no-daemon
# → android/app/build/outputs/apk/debug/app-debug.apk  (디버그 서명, 사이드로딩 설치)
```
- 최초 셋업/SDK 설치는 메모리의 `android-build-setup.md` 참고. 라이선스는 `C:\Android\sdk\licenses\` 해시파일로 수락됨.

## 버전 올리기

콘텐츠(문항/해설/HTML) 변경과 앱 코드 변경은 별개 숫자다:

- **콘텐츠만 변경** → `docs/version.json`의 `content` 만 올림(+`sw.js` VERSION). APK 재배포 불필요.
  설치된 앱은 실행 시 OTA로 `content > BUNDLED_CONTENT` 면 바뀐 파일만 받아 적용한다.
- **앱 코드 변경**(MainActivity 등) → `versionCode`/`versionName` 올리고 APK 재배포.
  이때 assets 도 최신 콘텐츠로 동기화하므로 `BUNDLED_CONTENT` = 그 시점 `content` 로 맞춘다.

| 위치 | 내용 | 트리거 |
|---|---|---|
| `docs/version.json` | `"content": N` | OTA(앱·웹 모두 갱신 감지) |
| `docs/sw.js` | `const VERSION = 'vN'` | 웹 서비스워커 캐시 무효화 |
| `android/app/.../MainActivity.kt` | `const val BUNDLED_CONTENT = M` | APK에 번들된 콘텐츠 버전(= 빌드시 content) |
| `android/app/build.gradle` | `versionCode`/`versionName` | APK 업데이트 설치(코드 변경 때만) |

```bash
# 예: 콘텐츠를 25로 올리고 OTA만 (APK 그대로)
sed -i "s/const VERSION = 'v24'/const VERSION = 'v25'/" docs/sw.js
printf '{\n  "content": 25,\n  "notes": "...",\n  "apk": 26\n}\n' > docs/version.json
python tools/make_manifest.py           # manifest.json 갱신(필수 — OTA가 이걸로 파일 비교)
git add -A && git commit && git push     # GitHub Pages 반영 → 앱이 다음 실행때 받아감
```

## 커밋 & 푸시
```bash
git add -A
git commit -F-  # 메시지 끝에 Co-Authored-By / Claude-Session 트레일러
GIT_SSH_COMMAND="ssh -o BatchMode=yes" git push origin main
```
- 대용량 이미지를 새로 추가할 때만 `docs/*/img/`가 커밋에 포함되게 한다(전사 전 WIP 크롭 수천 장은 커밋 금지 — prune 후 그림만 남기고 커밋).
- `node_modules/`·`package*.json`은 `.gitignore`(KaTeX는 CDN).

## JS 문법 검증 (배포 전 필수)
```bash
python -c "import re;h=open('docs/electric.html',encoding='utf-8').read();open('docs/_c.js','w',encoding='utf-8').write(re.search(r'<script>(.*)</script>',h,re.S).group(1))"
node --check docs/_c.js && rm docs/_c.js
```

## 동작 메커니즘 메모
- **OTA(앱 재배포 없이 갱신)**: 페이지는 그대로 `file:///android_asset/…` 에서 로드하되, `MainActivity.shouldInterceptRequest` 가 `filesDir/web/<경로>` 에 받아둔 파일이 있으면 그걸 우선 서빙한다(없으면 번들 assets). `file://` origin 을 유지하므로 기존 진행/오답노트(localStorage) 보존. 실행 시 `version.json` 의 `content > max(BUNDLED_CONTENT, 받아둔버전)` 이면 `manifest.json`(파일별 sha1)을 받아 **해시가 다른 파일만** `filesDir/web/` 로 내려받고(원자적 .tmp→rename + sha1 검증), 완료 토스트. 다음 리로드/재실행부터 적용. 오프라인/실패 시 조용히 번들 사용.
- **서비스워커**: HTML/version.json은 network-first+no-store(GitHub Pages 10분 캐시 우회). 재배포 후 새로고침 1회면 반영. `sw.js`의 VERSION 바꿔야 워커 교체.
- **KaTeX**: CDN(jsdelivr) defer 로드. 렌더 후 `__km(document.body)`로 `$..$` 변환. 전기/건설만(임베디드는 미사용).
- **종목 분리**: `var NS`로 localStorage 키 네임스페이스. 뒤로가기(`backNav`)는 홈=종목선택, 그외=CBT홈.
