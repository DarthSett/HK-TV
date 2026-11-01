#!/bin/bash
# Builds the launcher app (plain Java, no Gradle) -> dist/skippy-channel.apk
# Everything configurable comes from house.json via tools/render_home.py (see docs/STANDALONE.md).
set -e
P=$(cd "$(dirname "$0")" && pwd); R=$(cd "$P/.." && pwd); T=${ANDROID_BUILD_DIR:-~/ai/tools/android-build}
BT=$T/android-14; JAR=$T/android-34/android.jar; export JAVA_HOME=$(ls -d $T/jdk-*); export PATH=$JAVA_HOME/bin:$PATH
W=$R/dist/channel-build; rm -rf $W; mkdir -p $W/res/drawable-nodpi $W/gen $W/classes $W/dex $W/assets/banners
HJ=${HOUSE_JSON:-$R/house.json}

# banners (dist/out/banner-*.png come from tools/gen_banners.py); banner-home.png is the app icon
cp $R/dist/out/banner-home.png $W/res/drawable-nodpi/banner.png
cp $R/dist/out/banner-*.png $W/assets/banners/

# home.html, modules/ and Config.java from house.json; in video mode this also names the wallpaper MP4s
eval "$(python3 "$R/tools/render_home.py" "$HJ" "$W" --print-env)"

# fonts (SIL OFL, see fonts/OFL-*.txt)
cp $R/fonts/*.ttf $W/assets/

# wallpaper slideshow: slides.json is tracked, the images live in local-assets/wallpapers (git-ignored, copyrighted)
mkdir -p $W/assets/wallpapers
[ -f $R/wallpapers/slides.json ] && cp $R/wallpapers/slides.json $W/assets/wallpapers/
cp $R/local-assets/wallpapers/*.jpg $W/assets/wallpapers/ 2>/dev/null || echo "note: no images in local-assets/wallpapers (add them or push to the TV, see docs/STANDALONE.md)"
# optional video wallpaper
[ -n "$VIDEO_FIRE" ] && cp $R/$VIDEO_FIRE $W/assets/wallpaper-fire.mp4
[ -n "$VIDEO_TV" ] && cp $R/$VIDEO_TV $W/assets/wallpaper-tv.mp4

sed "s/VC/$(date +%s | cut -c3-)/g" $P/AndroidManifest.xml > $W/AndroidManifest.xml
cd $W
$BT/aapt2 compile --dir res -o res.zip
$BT/aapt2 link -o un.apk -I $JAR --manifest AndroidManifest.xml --java gen -A assets -0 mp4 -0 png -0 jpg -0 ttf res.zip
javac -nowarn -source 8 -target 8 -bootclasspath $JAR:$BT/core-lambda-stubs.jar -cp $JAR -d classes $(find $P/src gen -name '*.java') 2>&1 | grep -v "^warning\|bootstrap\|^1 warning" || true
(cd classes && zip -q -r ../classes.jar .) && $BT/d8 --min-api 25 --lib $JAR --output dex classes.jar
cp un.apk wd.apk && (cd dex && zip -q ../wd.apk classes.dex)
$BT/zipalign -f 4 wd.apk al.apk
# signing: keystore and password stay OUTSIDE the repo (default ~/ai/keys; override with KEYSTORE / KEYSTORE_PASS_FILE)
KS=${KEYSTORE:-$HOME/ai/keys/skippy.keystore}; KSP=${KEYSTORE_PASS_FILE:-$HOME/ai/keys/skippy-keystore.pass}
[ -f "$KS" ] || { echo "keystore missing: $KS (create with: keytool -genkeypair -keystore $KS -alias skippy -keyalg RSA -keysize 2048 -validity 20000)"; exit 1; }
$BT/apksigner sign --ks "$KS" --ks-pass file:"$KSP" --out $R/dist/skippy-channel.apk al.apk
echo "ok $R/dist/skippy-channel.apk"
