package dev.skippy.channel;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.content.res.AssetFileDescriptor;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.drawable.Drawable;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Base64;
import android.util.Log;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.webkit.ConsoleMessage;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import java.io.ByteArrayOutputStream;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONObject;

// Launcher Skippy (Fire TV do quarto, Fire OS 6 / Android 7.1, onde o Projectivy não roda).
// Wallpaper animado = MediaPlayer em loop numa SurfaceView; interface = assets/home.html num WebView transparente.
// O Watch (estatísticas de uso) traz esta tela de volta quando a home da Amazon aparece.
public class Home extends Activity implements SurfaceHolder.Callback {
    static final String TAG = "SkippyHome";
    static final boolean FIRE = android.os.Build.MODEL.startsWith("AFT");   // Fire TV do quarto; o resto (Shield da sala) usa o perfil sala
    final Handler ui = new Handler(Looper.getMainLooper());
    SurfaceView surface;
    WebView web;
    MediaPlayer mp;
    boolean haveSurface, resumed;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(5, 8, 10));
        if (Config.VIDEO) {   // video wallpaper: MediaPlayer on a SurfaceView behind the transparent WebView. Slideshow mode needs neither.
            surface = new SurfaceView(this);
            surface.getHolder().addCallback(this);
            root.addView(surface, new FrameLayout.LayoutParams(-1, -1));
        }

        web = new WebView(this);
        web.setBackgroundColor(Color.TRANSPARENT);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowUniversalAccessFromFileURLs(true);   // home.html (file://) busca o feed no .46
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);
        // página de 1920 px: zoom = px de tela por px CSS (o WebView da Amazon ignora o viewport; no Shield o file:// também)
        web.setInitialScale(Math.round(100f * getResources().getDisplayMetrics().widthPixels / 1920f));
        web.setWebViewClient(new WebViewClient());
        web.setWebChromeClient(new Chrome());
        web.addJavascriptInterface(new Bridge(this), "Launcher");
        root.addView(web, new FrameLayout.LayoutParams(-1, -1));
        root.setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        setContentView(root);
        web.loadUrl("file:///android_asset/home.html");
        Watch.start(this);
        // .HomeAlias (the HOME entry) is not switched here: the manifest enables it from install, and
        // `adb shell cmd package set-home-activity dev.skippy.channel/.HomeAlias` makes it the default home.
        web.requestFocus();
    }

    static class Chrome extends WebChromeClient {
        @Override public boolean onConsoleMessage(ConsoleMessage m) {
            Log.i(TAG, m.messageLevel() + " " + m.message() + " @" + m.lineNumber());
            return true;
        }
    }

    // ---------- ponte JS ----------
    static class Bridge {
        final Home h;
        Bridge(Home h) { this.h = h; }
        @JavascriptInterface public String apps() { return h.listApps(); }
        @JavascriptInterface public String slides() { return h.readSlides(); }
        @JavascriptInterface public String inputs() { return h.listInputs(); }
        @JavascriptInterface public void input(String id) { h.ui.post(() -> h.switchInput(id)); }
        @JavascriptInterface public void launch(String spec) { h.ui.post(() -> h.launch(spec)); }
        @JavascriptInterface public void open(String intentUri) { h.ui.post(() -> h.openUri(intentUri)); }
        @JavascriptInterface public boolean has(String spec) {
            try {
                String[] p = spec.split("/", 2);
                h.getPackageManager().getActivityInfo(new ComponentName(p[0], p[1].startsWith(".") ? p[0] + p[1] : p[1]), 0);
                return true;
            } catch (Exception e) { return false; }
        }
    }

    // Wallpaper override: images pushed to <app external files>/wallpapers (adb push ... /sdcard/Android/data/dev.skippy.channel/files/wallpapers/),
    // optionally with a slides.json next to them. Returns "" when the folder is empty, and the page then uses the images bundled in the APK.
    String readSlides() {
        try {
            java.io.File base = getExternalFilesDir(null);
            if (base == null) return "";
            java.io.File dir = new java.io.File(base, "wallpapers");
            String[] all = dir.list();
            if (all == null) return "";
            java.util.Arrays.sort(all);
            JSONArray files = new JSONArray();
            for (String n : all) {
                String l = n.toLowerCase();
                if (l.endsWith(".jpg") || l.endsWith(".jpeg") || l.endsWith(".png") || l.endsWith(".webp")) files.put(new JSONObject().put("file", n));
            }
            if (files.length() == 0) return "";
            JSONObject o = new JSONObject();
            o.put("base", "file://" + dir.getAbsolutePath() + "/");
            java.io.File cfg = new java.io.File(dir, "slides.json");
            if (cfg.isFile()) o.put("cfg", new JSONObject(readText(cfg)));
            else o.put("cfg", new JSONObject().put("slides", files));
            return o.toString();
        } catch (Exception e) { Log.w(TAG, "slides", e); return ""; }
    }

    static String readText(java.io.File f) throws java.io.IOException {
        try (java.io.FileInputStream in = new java.io.FileInputStream(f); ByteArrayOutputStream o = new ByteArrayOutputStream()) {
            byte[] b = new byte[8192]; int r;
            while ((r = in.read(b)) > 0) o.write(b, 0, r);
            return o.toString("UTF-8");
        }
    }

    String listApps() {
        PackageManager pm = getPackageManager();
        Set<String> seen = new HashSet<>();
        JSONArray out = new JSONArray();
        for (String cat : new String[]{Intent.CATEGORY_LEANBACK_LAUNCHER, Intent.CATEGORY_LAUNCHER}) {
            List<ResolveInfo> l = pm.queryIntentActivities(new Intent(Intent.ACTION_MAIN).addCategory(cat), 0);
            for (ResolveInfo r : l) {
                ActivityInfo a = r.activityInfo;
                if (a.packageName.equals(getPackageName()) || !seen.add(a.packageName)) continue;
                try {
                    JSONObject o = new JSONObject();
                    o.put("pkg", a.packageName);
                    o.put("spec", a.packageName + "/" + a.name);
                    o.put("label", String.valueOf(r.loadLabel(pm)));
                    o.put("tv", cat.equals(Intent.CATEGORY_LEANBACK_LAUNCHER));
                    Drawable d = a.loadBanner(pm);
                    if (d == null) d = a.applicationInfo.loadBanner(pm);
                    o.put("banner", d != null);
                    if (d == null) d = r.loadIcon(pm);
                    o.put("img", toDataUrl(d, d != null && o.getBoolean("banner") ? 320 : 128, d != null && o.getBoolean("banner") ? 180 : 128));
                    out.put(o);
                } catch (Exception e) { Log.w(TAG, "app " + a.packageName, e); }
            }
        }
        return out.toString();
    }

    static String toDataUrl(Drawable d, int w, int h) {
        if (d == null) return "";
        Bitmap bm = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(bm);
        d.setBounds(0, 0, w, h);
        d.draw(c);
        ByteArrayOutputStream o = new ByteArrayOutputStream();
        bm.compress(Bitmap.CompressFormat.PNG, 100, o);
        bm.recycle();
        return "data:image/png;base64," + Base64.encodeToString(o.toByteArray(), Base64.NO_WRAP);
    }

    void launch(String spec) {
        try {
            Intent i;
            if (spec.contains("/")) {
                String[] p = spec.split("/", 2);
                i = new Intent(Intent.ACTION_MAIN).setComponent(new ComponentName(p[0], p[1].startsWith(".") ? p[0] + p[1] : p[1]));
            } else {
                i = getPackageManager().getLeanbackLaunchIntentForPackage(spec);
                if (i == null) i = getPackageManager().getLaunchIntentForPackage(spec);
            }
            if (i == null) return;
            if (spec.startsWith("com.amazon.tv.launcher/") && spec.contains("Home")) Watch.pauseFor(60000);
            startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        } catch (Exception e) { Log.e(TAG, "launch " + spec, e); }
    }

    // External inputs (HDMI 1/2/3, AV...) as JSON [{id, label, state}]; state 0 = signal/device present, 1 = standby, 2 = nothing plugged in.
    String listInputs() {
        JSONArray out = new JSONArray();
        try {
            android.media.tv.TvInputManager tim = (android.media.tv.TvInputManager) getSystemService(Context.TV_INPUT_SERVICE);
            if (tim == null) return "[]";
            for (android.media.tv.TvInputInfo in : tim.getTvInputList()) {
                if (!in.isPassthroughInput()) continue;
                CharSequence cl = in.loadCustomLabel(this), l = in.loadLabel(this);
                String label = cl != null && cl.length() > 0 ? cl.toString() : l != null ? l.toString() : in.getId();
                out.put(new JSONObject().put("id", in.getId()).put("label", label).put("state", tim.getInputState(in.getId())));
            }
        } catch (Exception e) { Log.e(TAG, "inputs", e); }
        return out.toString();
    }

    // Switch the TV to a passthrough input: the TV's Live TV app plays the content://android.media.tv/passthrough/<id> URI.
    void switchInput(String id) {
        try {
            Uri u = android.media.tv.TvContract.buildChannelUriForPassthroughInput(id);
            // Live TV (com.heytap.tv.livetv/.ActivityEntrance on this TV) only matches the VIEW intent when the MIME type is set too (measured with cmd package query-activities).
            startActivity(new Intent(Intent.ACTION_VIEW).setDataAndType(u, "vnd.android.cursor.item/channel").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        } catch (Exception e) { Log.e(TAG, "input " + id, e); }
    }

    void openUri(String u) {
        try {
            Intent i = u.startsWith("intent:") ? Intent.parseUri(u, Intent.URI_INTENT_SCHEME) : new Intent(Intent.ACTION_VIEW, Uri.parse(u));
            startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        } catch (Exception e) { Log.e(TAG, "open " + u, e); }
    }

    // ---------- wallpaper ----------
    @Override public void surfaceCreated(SurfaceHolder h) { haveSurface = true; play(); }
    @Override public void surfaceChanged(SurfaceHolder h, int f, int w, int hh) { }
    @Override public void surfaceDestroyed(SurfaceHolder h) { haveSurface = false; release(); }

    void play() {
        if (!Config.VIDEO || !haveSurface || !resumed || mp != null) return;
        try {
            AssetFileDescriptor fd = getAssets().openFd(FIRE ? "wallpaper-fire.mp4" : "wallpaper-tv.mp4");
            mp = new MediaPlayer();
            mp.setDataSource(fd.getFileDescriptor(), fd.getStartOffset(), fd.getLength());
            fd.close();
            mp.setDisplay(surface.getHolder());
            mp.setLooping(true);
            mp.setVolume(0, 0);
            mp.setOnPreparedListener(MediaPlayer::start);
            mp.prepareAsync();
        } catch (Exception e) { Log.e(TAG, "wallpaper", e); release(); }
    }

    void release() { if (mp != null) { try { mp.release(); } catch (Exception ignored) { } mp = null; } }

    @Override protected void onResume() {
        super.onResume();
        resumed = true;
        play();
        if (web != null) {
            web.onResume(); web.resumeTimers();   // the page (slideshow + particles) only runs while the launcher is on screen
            web.evaluateJavascript("window.onHome && onHome()", null);
        }
    }

    @Override protected void onPause() {
        super.onPause(); resumed = false; release();
        if (web != null) { web.onPause(); web.pauseTimers(); }   // no background CPU while a game or app is in front
    }

    @Override public void onBackPressed() {
        web.evaluateJavascript("window.onBack ? onBack() : true", v -> { });   // a home nunca fecha com Voltar
    }

    @Override protected void onNewIntent(Intent i) {
        super.onNewIntent(i);
        if (web != null) web.evaluateJavascript("window.onHomePressed && onHomePressed()", null);
    }
}
