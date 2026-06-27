package com.embedded.cbt

import android.annotation.SuppressLint
import android.os.Bundle
import android.view.View
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this)
        setContentView(webView)

        // Draw edge-to-edge behind the status bar with a light background.
        webView.fitsSystemWindows = true
        webView.setBackgroundColor(0xFFF1F5F9.toInt())

        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true        // localStorage / sessionStorage
            loadWithOverviewMode = true
            useWideViewPort = true
            allowFileAccess = true
            cacheMode = android.webkit.WebSettings.LOAD_NO_CACHE
            textZoom = 100
        }

        webView.webViewClient = WebViewClient()

        if (savedInstanceState == null) {
            webView.loadUrl("file:///android_asset/index.html")
        }

        // Hardware back button: navigate within the WebView history first.
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })
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
