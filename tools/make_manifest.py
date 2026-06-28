# -*- coding: utf-8 -*-
"""OTA 매니페스트 생성기.

docs/ 안의 웹 정적자원(html/js/css/png/폰트)을 훑어 파일별 sha1 해시 목록을
docs/manifest.json 에 기록한다. 앱은 실행 시 version.json(content) 을 보고
새 버전이면 manifest.json 을 받아 '해시가 다른 파일만' filesDir 에 내려받는다.

version.json / manifest.json 은 APK 의 OTA 기준선(baseline)이므로 assets 에도 복사한다.
사용: python tools/make_manifest.py
"""
import os, hashlib, json, shutil

ROOT = r'C:\Users\emacser\Desktop\playground\embeded'
DOCS = os.path.join(ROOT, 'docs')
ASSETS = os.path.join(ROOT, 'android', 'app', 'src', 'main', 'assets')

# OTA 로 서빙 가능한(앱이 실제 로드하는) 확장자만. data.json/pdf/py 등은 제외(앱이 안 씀).
EXTS = {'.html', '.js', '.css', '.png', '.jpg', '.jpeg', '.svg',
        '.woff', '.woff2', '.ttf', '.gif'}
SKIP_NAMES = {'manifest.json', 'version.json'}  # 자기 자신은 목록에서 제외


def sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def build():
    files = []
    for dirpath, _, names in os.walk(DOCS):
        for n in names:
            if n in SKIP_NAMES:
                continue
            if os.path.splitext(n)[1].lower() not in EXTS:
                continue
            full = os.path.join(dirpath, n)
            rel = os.path.relpath(full, DOCS).replace('\\', '/')
            files.append({'p': rel, 'h': sha1(full), 's': os.path.getsize(full)})
    files.sort(key=lambda x: x['p'])

    ver = json.load(open(os.path.join(DOCS, 'version.json'), encoding='utf-8'))
    content = int(ver.get('content', 1))
    manifest = {'content': content, 'files': files}

    mpath = os.path.join(DOCS, 'manifest.json')
    json.dump(manifest, open(mpath, 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))

    # APK 기준선: assets 에도 version.json / manifest.json 복사
    if os.path.isdir(ASSETS):
        for fn in ('version.json', 'manifest.json'):
            shutil.copyfile(os.path.join(DOCS, fn), os.path.join(ASSETS, fn))
        copied = True
    else:
        copied = False

    total = sum(f['s'] for f in files)
    print('manifest: %d files, content=%d, %.1f MB%s'
          % (len(files), content, total / 1e6,
             '' if copied else '  (assets 없음 — 복사 생략)'))


if __name__ == '__main__':
    build()
