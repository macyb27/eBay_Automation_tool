#!/bin/sh
set -eu

ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
ANDROID_APP_DIR="$ROOT_DIR/android_app"

if [ ! -d "$ANDROID_APP_DIR" ]; then
    echo "ERROR: android_app directory not found." >&2
    exit 1
fi

SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
if [ -z "$SDK_ROOT" ]; then
    echo "ERROR: ANDROID_SDK_ROOT or ANDROID_HOME is not set." >&2
    echo "Install Android SDK and export ANDROID_SDK_ROOT first." >&2
    exit 1
fi

BUILD_TYPE="${BUILD_TYPE:-Debug}"
BUILD_TYPE_LOWER=$(printf "%s" "$BUILD_TYPE" | tr '[:upper:]' '[:lower:]')

cd "$ANDROID_APP_DIR"
./gradlew "assemble${BUILD_TYPE}"

APK_PATH="$ANDROID_APP_DIR/app/build/outputs/apk/${BUILD_TYPE_LOWER}/app-${BUILD_TYPE_LOWER}.apk"
if [ -f "$APK_PATH" ]; then
    echo "APK built at: $APK_PATH"
else
    echo "Build finished. APK should be under: $ANDROID_APP_DIR/app/build/outputs/apk/" >&2
fi
