Hollow Knight TV home screen

Custom launcher on the OnePlus TV (C00, Android 11, 4K panel / 1080p UI), based on skippy-tv, branch hk-theme, package dev.skippy.channel. Verified on the TV: slideshow with per-picture particle effects, dock, Live TV tile, Inputs picker, Home button lands on it. All working as intended.

What it is
Wallpaper slideshow of six Hollow Knight pictures (1920x1080), each with its own effect (rain, spores, dust, fireflies, embers). Set in wallpapers/slides.json (interval, shuffle, fade, per-slide effect). Interval is 10 s, chosen on purpose (the project default was 90 s).
Dock: Netflix, Prime Video, Hotstar (in.startv.hotstar), YouTube, Twitch (tv.twitch.android.app), Live TV (com.heytap.tv.livetv/.ActivityEntrance), Inputs, Settings.
Inputs tile opens a list: AV, Switch (HDMI 1 = HW5), Misc (HDMI 2 = HW6), PlayStation (HDMI 3 = HW7). Switching uses a VIEW intent on the passthrough URI with MIME vnd.android.cursor.item/channel. Names are INPUT_NAMES / INPUT_IDS in channel-app/assets/home.html.
Smart-home features of the original project are switched off by flags in house.json (originals in house.skippy.json, code in channel-app/assets/modules/).
Install facts
TV IP 192.168.88.5:5555 (can change). Previous home: com.ansub.tvhome/.MainActivity.
The Home entry (.HomeAlias) is off by default. Turn on/off by launching with am start -n dev.skippy.channel/.Home --ez home_entry true|false, then cmd package set-home-activity dev.skippy.channel/.HomeAlias (adb cannot enable a single component on Android 11).
Build tools on the PC: E:\Android (jdk-17, Sdk, build-layout wrappers, hollow-venv, keys). Undo files: E:\ClaudeTV (undo-hollow.sh, undo-hollow-state.txt, tv-changes-hollow.log). undo-hollow.sh only reverses this project; it never touches the TV Detox cleanup (undo.sh, undo-list.txt are separate).
Rollback
Just the home: adb shell cmd package set-home-activity com.ansub.tvhome/.MainActivity
Everything of this project: bash undo-hollow.sh (dry run: DRY_RUN=1 bash undo-hollow.sh)
Changing things later
Interval/effects: edit wallpapers/slides.json, rebuild with channel-app/build.sh, adb install -r dist/skippy-channel.apk.
New pictures without rebuilding: push to /sdcard/Android/data/dev.skippy.channel/files/wallpapers/ (replaces the bundled set).
Optional: commit on hk-theme (leave out local-assets/, dist/, keys).
