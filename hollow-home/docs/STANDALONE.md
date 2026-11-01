# Standalone home screen (branch `hk-theme`)

A launcher with a **wallpaper slideshow**, per-picture **particle effects**, a clock and a **dock**. The smart-home extras of the original
Skippy project are still in the repo but **switched off** by flags, so they can be brought back later.

## Build and install

```bash
pip install pillow numpy cairosvg
python3 tools/gen_banners.py $PWD            # dist/out/banner-*.png (dock tiles + app icon)
python3 tools/prep_wallpapers.py local-assets/originals local-assets/wallpapers   # optional: re-crop the source images
channel-app/build.sh                         # dist/skippy-channel.apk (needs the Android build tools, see AGENTS.md; keystore stays outside the repo)
adb install -r dist/skippy-channel.apk
adb shell dumpsys deviceidle whitelist +dev.skippy.channel
adb shell cmd package resolve-activity -a android.intent.action.MAIN -c android.intent.category.HOME   # NOTE the current home before changing it
adb shell cmd package set-home-activity dev.skippy.channel/.HomeAlias
```

**Roll back:** `adb shell cmd package set-home-activity com.ansub.tvhome/.MainActivity` (the home this TV had before; confirm with the resolve-activity line above).
Launch the app once by hand (`adb shell am start -n dev.skippy.channel/.Home`) and look at it before making it the default home.

Preview without a TV: `python3 tools/preview.py` (headless Chromium, screenshots in `dist/preview/shots`).

## house.json

| Key | Meaning |
|---|---|
| `language` | Locale for the clock and date (default `en-GB`). |
| `wallpaper.mode` | `slideshow` (default) or `video` (the old looping MP4 on a SurfaceView; needs `devices[].wallpaper`). |
| `features.cards` | HUD card row from the cards server. Needs `server.public_url`. |
| `features.quips` | The typed Skippy line. Needs the server. |
| `features.plex` | Plex capsule. Needs the server and Plex tokens on it. |
| `features.bridge` | Bridge panel with the live camera and lights. Needs the server and `camera.go2rtc` + `camera.stream`. |
| `features.watchnext` | Publish cards to Android's Watch Next row (for the Projectivy setup). Needs the server. |
| `features.warp` | Konami hyperspace easter egg. |

To bring a feature back: set its flag to `true`, copy the matching block (`server`, `hass`, `plex`, `camera`, `lights`, `devices`) from
`house.skippy.json`, deploy `cards/` (see `deploy-cards.sh`) and rebuild. `render_home.py` stops with a clear message if a flag needs a block you
have not filled in. Their code lives in `channel-app/assets/modules/` (loaded only when the flag is on), `cards/`, `Ponte.java`, `LiveCam.java`,
`Sync.java`, `Watch.java`.

## Wallpapers: `wallpapers/slides.json`

Pictures are bundled from `local-assets/wallpapers/` (git-ignored: the artwork is not ours). The list says how to show them:

```json
{ "interval": 90, "shuffle": true, "fade": 2.5, "zoom": true, "effects": true,
  "default": { "effect": "spores", "shade": 1 },
  "slides": [ { "file": "memorial-rain.jpg", "effect": "rain", "count": 130, "angle": 10, "color": "#bcd8ff", "shade": 0.9 } ] }
```

| Key | Meaning |
|---|---|
| `interval` | Seconds per picture (a slide can set its own). |
| `shuffle` | Random order; never opens on the picture shown last time. |
| `fade` | Cross-fade seconds. `zoom`: slow drift on each picture. `effects`: `false` turns all particles off. |
| `shade` | 0 to 1: strength of the dark gradients that keep the clock and dock readable. Brighter pictures need 1. |
| `effect` | `spores`, `fireflies`, `ash`, `embers`, `rain`, `dust`, `fog` or `none`. |
| options | `count`, `speed`, `size`, `color` (hex), `opacity`; `angle` (rain); `beam: [x1, y1, x2, y2, width]` in 1920x1080 space (dust glows only inside the beam). |

**Change pictures without rebuilding:** push them to the app's folder on the TV. If that folder has images, it replaces the bundled set;
a `slides.json` next to them is used if present, otherwise every picture gets the default effect. Delete the folder's contents to go back to the bundle.

```bash
adb shell mkdir -p /sdcard/Android/data/dev.skippy.channel/files/wallpapers
adb push my-pictures/. /sdcard/Android/data/dev.skippy.channel/files/wallpapers/
```

Input switching: Live TV only answers the VIEW intent when the MIME type `vnd.android.cursor.item/channel` is set (done in `Home.switchInput`). HDMI 1/2/3 = ids `.../HW5`, `HW6`, `HW7`.

Input names: `INPUT_NAMES` in home.html renames HDMI ports (1 Switch, 2 Misc, 3 PlayStation); the Inputs dock tile opens the picker.

Pictures should be 16:9, 1920x1080. The UI layer of this TV is 1080p (the panel is 4K but Android only offers a 1080p mode), so a 4K still would be downscaled anyway.
Keep the bottom quarter calm: the dock sits at y 800 to 967.

## Dock

`DOCK_ALL` at the top of the first script in `channel-app/assets/home.html`: the first installed entry of each row is used; entries whose
app is missing are skipped. Package names were confirmed on this TV (Hotstar `in.startv.hotstar`, Twitch `tv.twitch.android.app`, Live TV `com.heytap.tv.livetv/.ActivityEntrance`). Banners come from `tools/gen_banners.py` (add a key to its `APPS`).

## Notes

- The page stops its timers and animation while another app is in front (`Home.onPause`), so games and the PS5 input pay nothing for it.
- Everything in the page is plain ES2017 on purpose: the TV's WebView may be old. Glow effects use pre-drawn sprites, never `shadowBlur`.
- The Java edits were checked for syntax only; they have not been compiled against the Android SDK yet.
- Fonts: Cinzel and Cormorant Garamond, SIL Open Font License (`fonts/OFL-*.txt`). Logos: Simple Icons (CC0).
