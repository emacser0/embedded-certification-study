package com.embedded.cbt

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity

/**
 * 자격증 CBT — docs 웹 번들을 assets에 담아 오프라인으로 제공.
 * index.html(종목 선택) → embedded/electric/gconsafety.html 멀티페이지.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val prefs by lazy { getSharedPreferences("cbt", Context.MODE_PRIVATE) }

    companion object {
        const val START_URL = "file:///android_asset/index.html"
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
                // 페이지가 처리(CBT홈/문제풀기 단계)하면 handled, 선택화면이면 exit→앱 종료
                webView.evaluateJavascript("(window.__appBack&&window.__appBack())||'exit'") { res ->
                    val r = res?.trim('"') ?: "exit"
                    if (r != "handled") finish()
                }
            }
        })
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
