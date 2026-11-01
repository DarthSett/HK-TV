#!/usr/bin/env python3
"""Headless preview of the home screen: assemble the APK's assets folder, load home.html in Chromium with a stub launcher,
step through every slide and save screenshots + a small report (JS errors, frame times).

usage: python3 tools/preview.py [out_dir] [--house house.json] [--wait 5]
Needs: playwright (+ chromium), and tools/gen_banners.py already run (dist/out/banner-*.png).
"""
import glob, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[1:]
house = os.path.join(ROOT, 'house.json')
wait = 5.0
out = None
while args:
    a = args.pop(0)
    if a == '--house': house = args.pop(0)
    elif a == '--wait': wait = float(args.pop(0))
    else: out = a
out = os.path.abspath(out or os.path.join(ROOT, 'dist', 'preview'))
assets = os.path.join(out, 'assets')
shots = os.path.join(out, 'shots')
shutil.rmtree(out, ignore_errors=True)
os.makedirs(shots)

# same layout build.sh gives the APK
subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'render_home.py'), house, out], check=True)
for f in glob.glob(os.path.join(ROOT, 'fonts', '*.ttf')):
    shutil.copy(f, assets)
os.makedirs(os.path.join(assets, 'banners'))
for f in glob.glob(os.path.join(ROOT, 'dist', 'out', 'banner-*.png')):
    shutil.copy(f, os.path.join(assets, 'banners'))
wp = os.path.join(assets, 'wallpapers'); os.makedirs(wp)
shutil.copy(os.path.join(ROOT, 'wallpapers', 'slides.json'), wp)
for f in glob.glob(os.path.join(ROOT, 'local-assets', 'wallpapers', '*.jpg')):
    shutil.copy(f, wp)

# apps the TV reported (names only; icons are blank in the preview)
APPS = [('com.netflix.ninja', 'Netflix'), ('com.amazon.amazonvideo.livingroom', 'Prime Video'), ('in.startv.hotstar', 'Hotstar'),
        ('com.google.android.youtube.tv', 'YouTube'), ('tv.twitch.android.app', 'Twitch'), ('com.spotify.tv.android', 'Spotify'),
        ('com.sonyliv', 'SonyLIV'), ('com.graymatrix.did', 'ZEE5'), ('com.jio.media.ondemand', 'JioCinema'), ('com.lionsgate.play', 'Lionsgate Play'),
        ('com.jio.jiogames', 'JioGames'), ('com.jio.web', 'Jio Browser'), ('com.google.android.youtube.tvmusic', 'YouTube Music'),
        ('com.android.vending', 'Google Play Store'), ('com.android.tv.settings', 'Settings')]
BLANK = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
STUB = """
window.Launcher = {
  apps: () => JSON.stringify(%s.map(a => ({pkg: a[0], spec: a[0] + '/.Main', label: a[1], tv: true, banner: false, img: '%s'}))),
  launch: () => {}, open: () => {}, has: spec => spec.startsWith('com.heytap.tv.livetv'), slides: () => '',
  inputs: () => JSON.stringify([{id:'com.mediatek.tvinput/.hdmi.HDMIInputService/HW7',label:'HDMI 3',state:0},{id:'com.mediatek.tvinput/.hdmi.HDMIInputService/HW5',label:'HDMI 1',state:2},{id:'com.mediatek.tvinput/.hdmi.HDMIInputService/HW6',label:'HDMI 2',state:2},{id:'com.mediatek.tvinput/.hdmi.HDMIInputService/HDMI300004',label:'PlayStation 5',state:0},{id:'com.mediatek.tvinput/.composite.CompositeInputService/HW2',label:'AV',state:2}]),
  input: id => { window.__input = id; }
};
""" % (json.dumps(APPS), BLANK)

from playwright.sync_api import sync_playwright

report = {'errors': [], 'slides': []}
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1920, 'height': 1080})
    pg.on('console', lambda m: report['errors'].append(m.text) if m.type == 'error' else None)
    pg.on('pageerror', lambda e: report['errors'].append('pageerror: ' + str(e)))
    pg.on('requestfailed', lambda r: report['errors'].append('request failed: ' + r.url))
    pg.add_init_script(STUB)
    pg.goto('file://' + os.path.join(assets, 'home.html'))
    pg.wait_for_timeout(1500)
    n = pg.evaluate('HOME.SS.list.length')
    report['slide_count'] = n
    for k in range(n):
        name = pg.evaluate(f'(() => {{ HOME.SS.jump({k}); return HOME.SS.list[{k}].file + " / " + (HOME.SS.list[{k}].effect || "none"); }})()')
        pg.wait_for_timeout(int(wait * 1000))
        fn = os.path.join(shots, f'slide-{k + 1}.png')
        pg.screenshot(path=fn)
        # frames the page actually drew over ~2 s (headless software rendering: only a rough guide)
        fps = pg.evaluate("""() => new Promise(res => { let c = 0, t0 = performance.now();
            const f = () => { c++; if (performance.now() - t0 < 2000) requestAnimationFrame(f); else res(c / 2); }; requestAnimationFrame(f); })""")
        report['slides'].append({'n': k + 1, 'slide': name, 'fps': fps})
    pg.keyboard.press('ArrowDown'); pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(1200)
    pg.screenshot(path=os.path.join(shots, 'apps.png'))
    pg.keyboard.press('ArrowUp'); pg.wait_for_timeout(1000)
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(700)
    pg.screenshot(path=os.path.join(shots, 'dock-focus.png'))
    # input picker: dock -> Inputs -> pick the 2nd row -> Enter
    pg.evaluate("HOME.SS.jump(0)"); pg.wait_for_timeout(500)
    n = pg.evaluate("Array.from(document.querySelectorAll('#dock .app img')).findIndex(i => i.src.includes('banner-inputs'))")
    report['inputs_tile_index'] = n
    pg.keyboard.press('ArrowUp'); pg.keyboard.press('ArrowUp')   # back to the dock row
    for _ in range(12): pg.keyboard.press('ArrowLeft')
    for _ in range(n): pg.keyboard.press('ArrowRight')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(shots, 'inputs.png'))
    pg.keyboard.press('ArrowDown'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    report['switched_to'] = pg.evaluate("window.__input")
    report['picker_closed'] = pg.evaluate("!document.body.classList.contains('picking')")
    report['dock'] = pg.evaluate("Array.from(document.querySelectorAll('#dock .app img')).map(i => i.getAttribute('src'))")
    b.close()

json.dump(report, open(os.path.join(out, 'report.json'), 'w'), indent=1)
print(json.dumps(report, indent=1))
