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
```bash
# 임베디드 본체가 바뀌었으면 먼저 동기화
cp cbt/index.html android/app/src/main/assets/index.html

# Android SDK/Gradle (이 PC 설치 위치)
ANDROID_HOME=C:\Android\sdk  "C:\Android\gradle-8.9\bin\gradle.bat" \
  -p <repo>/android assembleDebug --no-daemon
# → android/app/build/outputs/apk/debug/app-debug.apk  (디버그 서명, 사이드로딩 설치)
```
- 최초 셋업/SDK 설치는 메모리의 `android-build-setup.md` 참고. 라이선스는 `C:\Android\sdk\licenses\` 해시파일로 수락됨.

## 버전 올리기 (★ 5곳 동시)
새 콘텐츠/코드 배포 때마다 숫자 N을 함께 올린다:
| 위치 | 내용 |
|---|---|
| `docs/version.json` | `"content": N` (OTA 배너 트리거) |
| `docs/sw.js` | `const VERSION = 'vN'` (서비스워커 캐시 무효화) |
| `android/app/build.gradle` | `versionCode N` + `versionName "1.N"` (앱 업데이트 설치) |
| `android/app/.../MainActivity.kt` | `const val BUNDLED_CONTENT = N` (OTA 우선순위) |

```bash
sed -i "s/const VERSION = 'v15'/const VERSION = 'v16'/" docs/sw.js
sed -i 's/const val BUNDLED_CONTENT = 15/const val BUNDLED_CONTENT = 16/' android/app/src/main/java/com/embedded/cbt/MainActivity.kt
sed -i 's/versionCode 15/versionCode 16/; s/versionName "1.15"/versionName "1.16"/' android/app/build.gradle
printf '{\n  "content": 16,\n  "notes": "...",\n  "apk": 16\n}\n' > docs/version.json
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
- **OTA**: 앱은 실행 시 `version.json` 확인 → `content > BUNDLED_CONTENT`면 배너 → 탭하면 `embedded.html` 받아 filesDir 저장+리로드. `loadDataWithBaseURL(asset base)`라 번들 이미지 사용.
- **서비스워커**: HTML/version.json은 network-first+no-store(GitHub Pages 10분 캐시 우회). 재배포 후 새로고침 1회면 반영. `sw.js`의 VERSION 바꿔야 워커 교체.
- **KaTeX**: CDN(jsdelivr) defer 로드. 렌더 후 `__km(document.body)`로 `$..$` 변환. 전기/건설만(임베디드는 미사용).
- **종목 분리**: `var NS`로 localStorage 키 네임스페이스. 뒤로가기(`backNav`)는 홈=종목선택, 그외=CBT홈.
