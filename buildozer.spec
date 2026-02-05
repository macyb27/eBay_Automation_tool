[app]

# ============================================
# eBay Automation Tool - Buildozer Konfiguration
# APK Build OHNE Sandbox-Umgebung
# ============================================

# App Metadaten
title = eBay Automation Tool
package.name = ebayautomation
package.domain = com.ebaytools

# Source Directory
source.dir = ./mobile_app
source.include_exts = py,png,jpg,kv,atlas,json,txt
source.exclude_exts = spec

# Versionierung
version = 1.0.0
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# App Requirements (Kivy + Dependencies)
requirements = python3,kivy==2.3.0,pillow,urllib3,certifi,charset-normalizer,idna,requests

# Android-spezifische Konfiguration
# ============================================

# Android SDK/NDK Versionen
android.api = 33
android.minapi = 24
android.ndk = 25b
android.sdk = 33

# NDK API Level
android.ndk_api = 24

# Architektur (arm64-v8a fuer moderne Geraete, armeabi-v7a fuer Kompatibilitaet)
android.archs = arm64-v8a, armeabi-v7a

# Berechtigungen
android.permissions = INTERNET,CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,READ_MEDIA_IMAGES

# Features
android.features = android.hardware.camera,android.hardware.camera.autofocus

# Gradle Dependencies
android.gradle_dependencies = 

# App-Modus: debug oder release
# android.release_artifact = apk

# WICHTIG: Kein Sandbox/VirtualEnv verwenden
# ============================================
# Diese Einstellungen deaktivieren die Sandbox-Umgebung
# und bauen direkt im System-Python

# Buildozer Virtual Environment deaktivieren
# (Standard in neueren Versionen, explizit gesetzt fuer Kompatibilitaet)
# p4a.branch = develop

# Python-for-Android Konfiguration
p4a.bootstrap = sdl2
# p4a.source_dir = 

# Kein lokales Virtualenv
# buildozer_profile = 

# Build-Optionen
build_dir = ./.buildozer
# bin_dir = ./bin

# Android Accept License automatisch
android.accept_sdk_license = True

# Skip SDK Update (beschleunigt Build)
android.skip_update = False

# ANT nicht verwenden (veraltet)
android.ant_path = 

# Presplash und Icon
# presplash.filename = %(source.dir)s/data/presplash.png
# icon.filename = %(source.dir)s/data/icon.png

# App Orientierung
orientation = portrait

# Fullscreen
fullscreen = 0

# Android Manifest Anpassungen
android.manifest.intent_filters = 
android.manifest.application_attribs = 
android.add_jars = 
android.add_src = 
android.add_libs_armeabi_v7a = 
android.add_libs_arm64_v8a = 

# Whitelist/Blacklist
android.whitelist = 

# Logcat Filter
android.logcat_filters = *:S python:D

# Copy Libraries
android.copy_libs = 1

# Backup erlauben
android.allow_backup = True

# Entrypoint
android.entrypoint = org.kivy.android.PythonActivity

# Activity Theme
android.apptheme = "@android:style/Theme.NoTitleBar"

# Kompilierung
android.enable_androidx = True

# ProGuard (fuer Release)
# android.add_proguard_rules =

# AAB statt APK (fuer Google Play)
# android.release_artifact = aab

# ============================================
# iOS Konfiguration (optional)
# ============================================
# ios.kivy_ios_url = https://github.com/kivy/kivy-ios
# ios.kivy_ios_branch = master
# ios.ios_deploy_url = https://github.com/nicholasjackson/python-for-ios
# ios.ios_deploy_branch = 1.0.0

# ============================================
# Build-System Konfiguration
# ============================================

# Log Level
log_level = 2

# Warnungen als Fehler behandeln
warn_on_root = 0

# Kein Sandbox/VirtualEnv im Build-Prozess
# Dies ist die Kerneinstellung fuer "Build ohne Sandbox"
# In aelteren Buildozer-Versionen:
#   use_virtualenv = 0
# In neueren Versionen ist dies Standard
