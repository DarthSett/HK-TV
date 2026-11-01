#!/bin/bash
# undo-hollow.sh: puts the TV back to how it was BEFORE the hollow-home project (dev.skippy.channel).
# It only reverses what that project did: the Home setting, our app and its data, our Doze whitelist entry,
# files we pushed and settings we changed. It never re-enables, reinstalls or changes anything from the
# earlier TV Detox cleanup (that has its own undo.sh / undo-list.txt, which this script never calls).
#
# Usage (Git Bash):   bash undo-hollow.sh [TV_IP[:PORT]]          default 192.168.88.5:5555
#                     DRY_RUN=1 bash undo-hollow.sh               prints the commands, changes nothing
# The TV's IP can change: check it first (adb mdns services, or the TV's network settings).
set -u
export MSYS_NO_PATHCONV=1            # stop Git Bash from rewriting /sdcard/... paths into C:/Program Files/Git/...
HERE=$(cd "$(dirname "$0")" && pwd)
STATE=$HERE/undo-hollow-state.txt
LOG=$HERE/tv-changes-hollow.log
BACKUP_DIR=$HERE/hollow-backup
ADB=${ADB:-"/e/Users/Sourav Sett/Downloads/platform-tools-latest-windows/platform-tools/adb.exe"}
PKG=dev.skippy.channel

TV=${1:-192.168.88.5:5555}
case "$TV" in *:*) ;; *) TV=$TV:5555 ;; esac

[ -f "$STATE" ] || { echo "Missing $STATE: can't know what to restore." >&2; exit 1; }
val() { sed -n "s/^$1=\([^ ]*\).*/\1/p" "$STATE" | head -1; }
HOME_ACTIVITY=$(val HOME_ACTIVITY)          # expected com.ansub.tvhome/.MainActivity
HOME_ROLE=$(val HOME_ROLE_HOLDERS)          # expected com.ansub.tvhome
SKIPPY_INSTALLED=$(val SKIPPY_INSTALLED)    # no = we installed it, so undo uninstalls it
SKIPPY_WHITELISTED=$(val SKIPPY_WHITELISTED)
TV_SERIAL=$(val TV_SERIAL)

# ---- added as the project goes (each entry is also in tv-changes-hollow.log) ----
PUSHED_FILES=()        # files we pushed to the TV, removed by step 5 (none so far)
SETTINGS_RESTORE=()    # "namespace key old_value" ("null" = delete the key), restored by step 6 (none so far)
# ---------------------------------------------------------------------------------

[ -n "$HOME_ACTIVITY" ] || { echo "No HOME_ACTIVITY in $STATE." >&2; exit 1; }

"$ADB" connect "$TV" >/dev/null 2>&1 || true
[ "$("$ADB" -s "$TV" get-state 2>/dev/null)" = device ] || { echo "Can't reach $TV (debugging on? right IP?)." >&2; exit 1; }
serial=$("$ADB" -s "$TV" shell getprop ro.serialno | tr -d '\r')
[ "$serial" = "$TV_SERIAL" ] || { echo "Device at $TV is '$serial', not the recorded TV '$TV_SERIAL'. Stopping." >&2; exit 1; }

tv() {                      # runs one TV-changing command, logs it
  if [ "${DRY_RUN:-0}" = 1 ]; then echo "[dry-run] adb shell $*"; return 0; fi
  out=$("$ADB" -s "$TV" shell "$@" 2>&1 | tr -d '\r'); rc=$?
  echo "$(date '+%Y-%m-%d %H:%M:%S') | undo-hollow: adb shell $* | rc=$rc ${out//$'\n'/ }" >> "$LOG"
  echo "  adb shell $*  ->  ${out:-ok}"
}
installed() { "$ADB" -s "$TV" shell pm list packages "$PKG" | tr -d '\r' | grep -qx "package:$PKG"; }

echo "Restoring $TV (serial $serial) to the state recorded in $(basename "$STATE")"

echo "1. Our Home entry"
# Android 11 refuses 'pm disable <app>/.HomeAlias' from adb (SecurityException), so the entry is not switched off
# on its own: step 2 moves Home back, and step 4 (uninstall) removes the entry with the app.
echo "  removed with the app in step 4"

echo "2. Home back to $HOME_ACTIVITY"
tv cmd package set-home-activity "$HOME_ACTIVITY"
[ -n "$HOME_ROLE" ] && tv cmd role add-role-holder --user 0 android.app.role.HOME "$HOME_ROLE"

echo "3. Doze whitelist"
if [ "$SKIPPY_WHITELISTED" = yes ]; then echo "  $PKG was whitelisted before, leaving it"
else tv dumpsys deviceidle whitelist -"$PKG"; fi

echo "4. Our app"
if [ "$SKIPPY_INSTALLED" = yes ]; then
  # it existed before the project: put the backed-up copy back
  apk=$(ls "$BACKUP_DIR"/*.apk 2>/dev/null | head -1)
  if [ -n "$apk" ]; then
    if [ "${DRY_RUN:-0}" = 1 ]; then echo "[dry-run] adb uninstall $PKG; adb install $apk"
    else
      "$ADB" -s "$TV" uninstall "$PKG"; "$ADB" -s "$TV" install "$apk"
      echo "$(date '+%Y-%m-%d %H:%M:%S') | undo-hollow: reinstalled backup $apk" >> "$LOG"
    fi
  else echo "  WARNING: it was installed before but no backup APK is in $BACKUP_DIR; leaving the current one" >&2; fi
else
  if installed; then tv pm uninstall "$PKG"; else echo "  $PKG not installed"; fi   # also deletes /sdcard/Android/data/$PKG
fi

echo "5. Files we pushed"
[ ${#PUSHED_FILES[@]} -eq 0 ] && echo "  none"
for f in "${PUSHED_FILES[@]}"; do tv rm -rf "$f"; done

echo "6. Settings we changed"
[ ${#SETTINGS_RESTORE[@]} -eq 0 ] && echo "  none"
for s in "${SETTINGS_RESTORE[@]}"; do
  set -- $s
  if [ "$3" = null ]; then tv settings delete "$1" "$2"; else tv settings put "$1" "$2" "$3"; fi
done

echo
echo "Now:"
echo "  HOME resolves to: $("$ADB" -s "$TV" shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME | tr -d '\r' | tail -1)   (expected $HOME_ACTIVITY)"
echo "  pm list packages | grep skippy: $("$ADB" -s "$TV" shell pm list packages | tr -d '\r' | grep skippy || echo '(none)')"
