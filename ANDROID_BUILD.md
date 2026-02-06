# Android APK Build

This repository now includes a minimal Android WebView app under `android_app/`.
The app loads the mobile UI from the backend (FastAPI).

## Requirements

- JDK 17+
- Android SDK (ANDROID_SDK_ROOT or ANDROID_HOME set)
- Android platform tools installed (platforms;android-34, build-tools;34.0.0)

## Backend (required for the app to show UI)

Example:

```
python simple_mobile_app.py
```

Default base URL used by the Android app (emulator):

```
http://10.0.2.2:8000
```

For a physical device, use your host IP, e.g.:

```
http://192.168.1.50:8000
```

Long press in the app to change the base URL.

## Build Debug APK

From repository root:

```
./build_apk.sh
```

Or manually:

```
cd android_app
./gradlew assembleDebug
```

Output:

```
android_app/app/build/outputs/apk/debug/app-debug.apk
```

## Build Release APK

```
cd android_app
./gradlew assembleRelease
```

Note: Release builds require signing. Configure a keystore and signing
config in `android_app/app/build.gradle` before distributing.
