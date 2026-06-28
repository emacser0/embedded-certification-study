package com.embedded.cbt

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity

/**
 * 자격증 CBT — docs 웹 번들을 assets에 담아 오프라인으로 제공.
 * index.html(종목 선택) → embedded/electric/gconsafety.html 멀티페이지 내비게이션.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

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
            domStorageEnabled = true          // localStorage (종목별 NS로 분리)
            loadWithOverviewMode = true
            useWideViewPort = true
            allowFileAccess = true
            allowFileAccessFromFileURLs = true
            textZoom = 100
        }

        // 같은 출처(file://asset)는 WebView가 처리, 외부 링크는 외부 브라우저로
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, url: String): Boolean {
                if (url.startsWith("file://")) return false
                return try {
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                    true
                } catch (e: Exception) { false }
            }
        }

        webView.addJavascriptInterface(BrowserBridge(), "AndroidBridge")

        if (savedInstanceState == null) webView.loadUrl(START_URL)

        // 하드웨어 뒤로가기: 페이지 히스토리(선택→CBT→시험) 따라 뒤로
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) webView.goBack()
                else { isEnabled = false; onBackPressedDispatcher.onBackPressed() }
            }
        })
    }

    /** AI 질문하기: 외부 브라우저로 GPT/Gemini/Claude 열기 (WebView 이탈 방지) */
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
