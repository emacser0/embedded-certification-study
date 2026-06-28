package com.embedded.cbt

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    companion object {
        /** Content version bundled in this APK's assets/index.html. Bump when you ship
         *  a new APK whose bundled HTML is newer than what OTA might have delivered. */
        const val BUNDLED_CONTENT = 16

        /** GitHub Pages base that hosts version.json + index.html (+ images). */
        const val BASE = "https://emacser0.github.io/certification-study"

        const val ASSET_BASE = "file:///android_asset/"
        const val LOCAL_HTML = "index.html"
        const val PREFS = "cbt_update"
        const val KEY_APPLIED = "appliedContent"
    }

    private val prefs by lazy { getSharedPreferences(PREFS, Context.MODE_PRIVATE) }
    private var updateChecked = false

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Fresh APK with newer bundled content wins over any previously OTA-applied copy.
        if (BUNDLED_CONTENT > prefs.getInt(KEY_APPLIED, 0)) {
            File(filesDir, LOCAL_HTML).delete()
            prefs.edit().putInt(KEY_APPLIED, BUNDLED_CONTENT).apply()
        }

        webView = WebView(this)
        setContentView(webView)
        webView.fitsSystemWindows = true
        webView.setBackgroundColor(0xFFF1F5F9.toInt())

        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            loadWithOverviewMode = true
            useWideViewPort = true
            allowFileAccess = true
            textZoom = 100
        }

        webView.addJavascriptInterface(UpdaterBridge(), "AndroidUpdater")
        webView.addJavascriptInterface(BrowserBridge(), "AndroidBridge")

        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                if (!updateChecked) {
                    updateChecked = true
                    checkForUpdate()
                }
            }
        }

        loadActiveHtml()

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) webView.goBack()
                else { isEnabled = false; onBackPressedDispatcher.onBackPressed() }
            }
        })
    }

    /** Load the OTA copy from filesDir if present, otherwise the bundled asset.
     *  Base URL is the asset dir so relative images/ resolve to bundled images. */
    private fun loadActiveHtml() {
        val f = File(filesDir, LOCAL_HTML)
        val html = try {
            if (f.exists()) f.readText()
            else assets.open(LOCAL_HTML).bufferedReader().use { it.readText() }
        } catch (e: Exception) {
            assets.open(LOCAL_HTML).bufferedReader().use { it.readText() }
        }
        webView.loadDataWithBaseURL(ASSET_BASE, html, "text/html", "utf-8", null)
    }

    private fun effectiveLocalContent(): Int =
        maxOf(prefs.getInt(KEY_APPLIED, BUNDLED_CONTENT), BUNDLED_CONTENT)

    /** Background check; if a newer content version exists, tell the page to show a banner. */
    private fun checkForUpdate() {
        Thread {
            try {
                val vj = httpGet("$BASE/version.json?_=${System.currentTimeMillis()}") ?: return@Thread
                val obj = JSONObject(vj)
                val remote = obj.optInt("content", 0)
                val notes = obj.optString("notes", "")
                if (remote > effectiveLocalContent()) {
                    runOnUiThread {
                        val n = JSONObject.quote(notes)
                        webView.evaluateJavascript(
                            "window.cbtUpdate&&window.cbtUpdate.show($remote,$n)", null
                        )
                    }
                }
            } catch (_: Exception) { /* offline / not published yet — ignore silently */ }
        }.start()
    }

    /** Download the latest HTML, persist it, and reload. */
    private fun downloadAndApply() {
        Thread {
            try {
                val vj = httpGet("$BASE/version.json?_=${System.currentTimeMillis()}")
                val remote = if (vj != null) JSONObject(vj).optInt("content", 0) else 0
                // 웹 진입점은 선택화면(index.html)이므로, 앱은 임베디드 앱 본체(embedded.html)를 받는다.
                val html = httpGet("$BASE/embedded.html?_=${System.currentTimeMillis()}")
                if (html == null || html.length < 1000) throw IllegalStateException("bad html")
                File(filesDir, LOCAL_HTML).writeText(html)
                if (remote > 0) prefs.edit().putInt(KEY_APPLIED, remote).apply()
                runOnUiThread {
                    Toast.makeText(this, "업데이트 완료 (v$remote)", Toast.LENGTH_SHORT).show()
                    loadActiveHtml()
                }
            } catch (e: Exception) {
                runOnUiThread {
                    webView.evaluateJavascript("window.cbtUpdate&&window.cbtUpdate.fail()", null)
                }
            }
        }.start()
    }

    private fun httpGet(urlStr: String): String? {
        var con: HttpURLConnection? = null
        return try {
            con = (URL(urlStr).openConnection() as HttpURLConnection).apply {
                connectTimeout = 8000
                readTimeout = 8000
                requestMethod = "GET"
                instanceFollowRedirects = true
                setRequestProperty("Cache-Control", "no-cache")
            }
            if (con.responseCode in 200..299)
                con.inputStream.bufferedReader().use { it.readText() }
            else null
        } catch (e: Exception) {
            null
        } finally {
            con?.disconnect()
        }
    }

    /** Exposed to the WebView JS as `AndroidUpdater`. */
    inner class UpdaterBridge {
        @JavascriptInterface
        fun applyUpdate() {
            runOnUiThread { downloadAndApply() }
        }
    }

    /** Exposed as `AndroidBridge`: open a URL in the external browser/app
     *  so the WebView itself never navigates away from the CBT. */
    inner class BrowserBridge {
        @JavascriptInterface
        fun openUrl(url: String) {
            runOnUiThread {
                try {
                    val i = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    startActivity(i)
                } catch (_: Exception) {
                    Toast.makeText(this@MainActivity, "브라우저를 열 수 없습니다.", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        webView.saveState(outState)
    }
}
