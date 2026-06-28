package com.embedded.cbt

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.webkit.JavascriptInterface
import android.webkit.MimeTypeMap
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest

/**
 * 자격증 CBT — docs 웹 번들을 assets 에 담아 오프라인으로 제공.
 * index.html(종목 선택) → embedded/electric/gconsafety.html 멀티페이지.
 *
 * OTA(앱 재배포 없이 콘텐츠 갱신): 페이지는 여전히 file:///android_asset/ 에서 로드하되,
 * shouldInterceptRequest 에서 filesDir/web/<경로> 에 받아둔 파일이 있으면 그걸 우선 서빙한다.
 * file:// origin 을 유지하므로 기존 사용자의 localStorage(진행/오답노트)가 보존된다.
 * 실행 시 GitHub Pages 의 version.json 을 확인해 content 가 더 크면 manifest.json 을 받아
 * '해시가 다른 파일만' filesDir 로 내려받는다(다음 실행/리로드부터 적용).
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val prefs by lazy { getSharedPreferences("cbt", Context.MODE_PRIVATE) }
    private val webRoot by lazy { File(filesDir, "web") }

    companion object {
        const val START_URL = "file:///android_asset/index.html"
        const val ASSET_MARK = "/android_asset/"

        /** APK 에 번들된 콘텐츠 버전(= assets/version.json 의 content). 버전 올릴 때 함께 수정. */
        const val BUNDLED_CONTENT = 24

        /** GitHub Pages 배포 루트(끝에 /). version.json / manifest.json / 각 파일이 이 밑에 있다. */
        const val OTA_BASE = "https://emacser0.github.io/certification-study/"
        const val TAG = "CBT-OTA"
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this)
        setContentView(webView)
        webView.fitsSystemWindows = true
        webView.setBackgroundColor(0xFF0F172A.toInt())

        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            loadWithOverviewMode = true
            useWideViewPort = true
            allowFileAccess = true
            allowFileAccessFromFileURLs = true
            textZoom = 100
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, url: String): Boolean {
                if (url.startsWith("file://")) return false
                return try {
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); true
                } catch (e: Exception) { false }
            }

            // OTA: file:///android_asset/<경로> 요청을 filesDir/web/<경로> 가 있으면 그걸로 대체
            override fun shouldInterceptRequest(
                view: WebView, request: WebResourceRequest
            ): WebResourceResponse? = serveFromFilesDir(request.url)

            override fun onPageFinished(view: WebView?, url: String?) {
                if (url != null && url.startsWith("file://")) prefs.edit().putString("lastUrl", url).apply()
            }
        }

        // JS 다이얼로그(alert/confirm/prompt) 기본 처리 — 없으면 goHome 등의 confirm()이 막힌다
        webView.webChromeClient = WebChromeClient()

        webView.addJavascriptInterface(BrowserBridge(), "AndroidBridge")

        if (savedInstanceState == null) {
            // 콜드 스타트: 프로세스가 죽었다 살아나면 마지막 보던 페이지로 복원(진행은 localStorage 이어풀기)
            val last = prefs.getString("lastUrl", null)
            webView.loadUrl(if (last != null && last.startsWith("file://")) last else START_URL)
        }
        // savedInstanceState != null 이면 onRestoreInstanceState 의 restoreState 가 복원

        // 하드웨어 뒤로가기: 페이지에 위임(문제풀기→CBT 홈), 홈/선택화면이면 네이티브 히스토리/종료
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                webView.evaluateJavascript("(window.__appBack&&window.__appBack())||'exit'") { res ->
                    val r = res?.trim('"') ?: "exit"
                    if (r != "handled") finish()
                }
            }
        })

        // 백그라운드에서 OTA 확인(네트워크 실패는 조용히 무시 — 오프라인이면 번들 그대로)
        Thread { runCatching { checkOta() }.onFailure { Log.w(TAG, "ota skip: ${it.message}") } }
            .apply { isDaemon = true }.start()
    }

    // ---- OTA 서빙 ----

    /** file://.../android_asset/<rel> → filesDir/web/<rel> 파일이 있으면 그 스트림을 반환. 없으면 null(=번들 사용). */
    private fun serveFromFilesDir(url: Uri?): WebResourceResponse? {
        if (url == null || url.scheme != "file") return null
        val path = url.path ?: return null
        val i = path.indexOf(ASSET_MARK)
        if (i < 0) return null
        val rel = path.substring(i + ASSET_MARK.length)
        if (rel.isEmpty() || rel.contains("..")) return null
        return try {
            val f = File(webRoot, rel).canonicalFile
            if (!f.path.startsWith(webRoot.canonicalFile.path) || !f.isFile) return null
            WebResourceResponse(mimeOf(rel), encodingOf(rel), FileInputStream(f))
        } catch (e: Exception) { null }
    }

    private fun mimeOf(p: String): String {
        val ext = p.substringAfterLast('.', "").lowercase()
        return when (ext) {
            "html", "htm" -> "text/html"
            "js", "mjs" -> "application/javascript"
            "css" -> "text/css"
            "json" -> "application/json"
            "png" -> "image/png"
            "jpg", "jpeg" -> "image/jpeg"
            "gif" -> "image/gif"
            "svg" -> "image/svg+xml"
            "woff" -> "font/woff"
            "woff2" -> "font/woff2"
            "ttf" -> "font/ttf"
            else -> MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext) ?: "application/octet-stream"
        }
    }

    private fun encodingOf(p: String): String? {
        val ext = p.substringAfterLast('.', "").lowercase()
        return if (ext in setOf("html", "htm", "js", "mjs", "css", "json", "svg")) "utf-8" else null
    }

    // ---- OTA 업데이트 ----

    private fun checkOta() {
        // 기준선: filesDir 에 받아둔 manifest 가 있으면 그 content, 없으면 번들 content
        val localContent = maxOf(BUNDLED_CONTENT, prefs.getInt("otaContent", 0))
        val remoteVer = fetchJson(OTA_BASE + "version.json")
        val remoteContent = remoteVer.optInt("content", -1)
        if (remoteContent <= localContent) {
            Log.i(TAG, "up to date (local=$localContent remote=$remoteContent)")
            return
        }
        Log.i(TAG, "update available: $localContent -> $remoteContent")

        // 기준 해시: 번들(assets/manifest.json) + 이미 받아둔 filesDir/manifest.json(우선)
        val baseHash = HashMap<String, String>()
        readManifestFiles(assetsManifest()).forEach { (p, h) -> baseHash[p] = h }
        readManifestFiles(filesDirManifest())?.forEach { (p, h) -> baseHash[p] = h }

        val remoteManifest = fetchJson(OTA_BASE + "manifest.json")
        val files = remoteManifest.optJSONArray("files") ?: return
        webRoot.mkdirs()
        var got = 0
        for (k in 0 until files.length()) {
            val o = files.getJSONObject(k)
            val p = o.getString("p"); val h = o.getString("h")
            val target = File(webRoot, p)
            // 이미 올바른 파일이 filesDir 에 있거나, 번들에 같은 해시가 있으면 건너뜀
            if (target.isFile && sha1OfFile(target) == h) continue
            if (baseHash[p] == h && !target.exists()) continue
            if (downloadVerified(OTA_BASE + p, target, h)) got++
            else { Log.w(TAG, "download failed: $p"); return }  // 실패 시 manifest 미커밋 → 다음 실행 재시도
        }
        // 전부 성공: filesDir 에 manifest 저장 + content 갱신
        File(webRoot.parentFile, "manifest.json").writeText(remoteManifest.toString())
        prefs.edit().putInt("otaContent", remoteContent).apply()
        Log.i(TAG, "OTA done: content=$remoteContent, downloaded=$got files")
        runOnUiThread {
            Toast.makeText(this,
                "콘텐츠 업데이트 완료(v$remoteContent) — 새로고침/재실행 시 적용됩니다.",
                Toast.LENGTH_LONG).show()
        }
    }

    private fun assetsManifest(): JSONObject? = try {
        JSONObject(assets.open("manifest.json").bufferedReader().use { it.readText() })
    } catch (e: Exception) { null }

    private fun filesDirManifest(): JSONObject? {
        val f = File(webRoot.parentFile, "manifest.json")
        return if (f.isFile) try { JSONObject(f.readText()) } catch (e: Exception) { null } else null
    }

    /** manifest 의 files 배열 → {path: hash} */
    private fun readManifestFiles(m: JSONObject?): Map<String, String> {
        val out = HashMap<String, String>()
        val arr = m?.optJSONArray("files") ?: return out
        for (k in 0 until arr.length()) {
            val o = arr.getJSONObject(k)
            out[o.getString("p")] = o.getString("h")
        }
        return out
    }

    private fun fetchJson(urlStr: String): JSONObject {
        val text = httpGetText(urlStr + (if (urlStr.contains('?')) "&" else "?") + "t=" + System.currentTimeMillis())
        return JSONObject(text)
    }

    private fun httpGetText(urlStr: String): String {
        val c = (URL(urlStr).openConnection() as HttpURLConnection).apply {
            connectTimeout = 8000; readTimeout = 12000; requestMethod = "GET"
        }
        try {
            if (c.responseCode !in 200..299) throw RuntimeException("HTTP ${c.responseCode} for $urlStr")
            return c.inputStream.bufferedReader().use { it.readText() }
        } finally { c.disconnect() }
    }

    /** 임시파일로 받아 sha1 검증 후 원자적 교체. 성공 true. */
    private fun downloadVerified(urlStr: String, target: File, wantHash: String): Boolean {
        target.parentFile?.mkdirs()
        val tmp = File(target.parentFile, target.name + ".tmp")
        val c = (URL(urlStr).openConnection() as HttpURLConnection).apply {
            connectTimeout = 8000; readTimeout = 30000; requestMethod = "GET"
        }
        return try {
            if (c.responseCode !in 200..299) return false
            val md = MessageDigest.getInstance("SHA-1")
            c.inputStream.use { ins ->
                FileOutputStream(tmp).use { out ->
                    val buf = ByteArray(1 shl 16)
                    while (true) {
                        val n = ins.read(buf); if (n < 0) break
                        md.update(buf, 0, n); out.write(buf, 0, n)
                    }
                }
            }
            if (toHex(md.digest()) != wantHash) { tmp.delete(); return false }
            if (target.exists()) target.delete()
            tmp.renameTo(target)
        } catch (e: Exception) { tmp.delete(); false } finally { c.disconnect() }
    }

    private fun sha1OfFile(f: File): String {
        val md = MessageDigest.getInstance("SHA-1")
        FileInputStream(f).use { ins ->
            val buf = ByteArray(1 shl 16)
            while (true) { val n = ins.read(buf); if (n < 0) break; md.update(buf, 0, n) }
        }
        return toHex(md.digest())
    }

    private fun toHex(b: ByteArray): String {
        val s = StringBuilder(b.size * 2)
        for (x in b) { val v = x.toInt() and 0xFF; s.append("0123456789abcdef"[v ushr 4]); s.append("0123456789abcdef"[v and 0xF]) }
        return s.toString()
    }

    /** AI 질문하기: 외부 브라우저로 GPT/Gemini/Claude 열기 */
    inner class BrowserBridge {
        @JavascriptInterface
        fun openUrl(url: String) {
            runOnUiThread {
                try {
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                } catch (e: Exception) {
                    Toast.makeText(this@MainActivity, "브라우저를 열 수 없습니다.", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        webView.saveState(outState)
    }

    override fun onRestoreInstanceState(savedInstanceState: Bundle) {
        super.onRestoreInstanceState(savedInstanceState)
        webView.restoreState(savedInstanceState)
    }
}
