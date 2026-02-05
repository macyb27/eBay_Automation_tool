# Android APK Build Guide - Ohne Sandbox

## Uebersicht

Dieses Dokument beschreibt, wie die eBay Automation Tool Android-APK **ohne Sandbox-Umgebung** gebaut wird. Der Build-Prozess nutzt Buildozer/python-for-android direkt im System-Python, ohne isolierte Virtualenvs oder Sandbox-Schichten.

## Architektur

```
mobile_app/
  main.py          # Kivy-basierte Android App (Haupteinstiegspunkt)

buildozer.spec     # Buildozer Konfiguration (Sandbox deaktiviert)
build_apk.sh       # Build-Script mit allen Optionen
Dockerfile.buildozer  # Docker-basierter Build-Container

.github/workflows/
  build-apk.yml    # CI/CD Pipeline fuer automatische Builds
```

## Schnellstart

### Option 1: Lokaler Build

```bash
# 1. Build-Umgebung einrichten
./build_apk.sh setup

# 2. Debug APK bauen
./build_apk.sh debug

# 3. APK liegt in bin/
ls -la bin/*.apk
```

### Option 2: Docker Build (empfohlen fuer CI/CD)

```bash
# Docker Image bauen
docker build -f Dockerfile.buildozer -t ebay-apk-builder .

# Debug APK bauen
docker run --rm -v $(pwd)/bin:/workspace/bin ebay-apk-builder debug

# Release APK bauen
docker run --rm -v $(pwd)/bin:/workspace/bin ebay-apk-builder release
```

### Option 3: GitHub Actions

Der Build wird automatisch ausgeloest bei:
- Push auf `main` oder `cursor/*` Branches (wenn mobile_app/ geaendert wird)
- Pull Requests mit Aenderungen an mobilen Dateien
- Manueller Trigger ueber GitHub Actions UI

## Warum ohne Sandbox?

### Problem mit Sandbox-Builds
- Sandbox/VirtualEnv-Isolation verursacht Kompatibilitaetsprobleme in CI/CD
- Container-Umgebungen (Docker, GitHub Actions) bieten bereits Isolation
- Doppelte Isolation (Docker + Buildozer Sandbox) fuehrt zu Pfad-Konflikten
- Schnellere Build-Zeiten ohne zusaetzliche Abstraktion

### Loesung
- Buildozer laeuft direkt im System-Python
- Docker Container bietet die notwendige Isolation
- `USE_VENV=0` deaktiviert die interne Sandbox
- Alle Abhaengigkeiten werden system-weit installiert

## Build-Modi

### Debug APK
```bash
./build_apk.sh debug
```
- Nicht signiert (nur fuer Entwicklung)
- Mit Debug-Symbolen
- ADB-Debugging aktiviert

### Release APK
```bash
./build_apk.sh release
```
- Signiert mit Keystore
- ProGuard Optimierung
- Bereit fuer Google Play Store

### Saeubern
```bash
./build_apk.sh clean
```
- Entfernt `.buildozer/` und `bin/`
- Erzwingt vollstaendigen Neubau

## Konfiguration

### buildozer.spec - Wichtige Einstellungen

| Einstellung | Wert | Beschreibung |
|------------|------|--------------|
| `android.api` | 33 | Target Android API Level |
| `android.minapi` | 24 | Minimale Android Version (7.0) |
| `android.ndk` | 25b | Android NDK Version |
| `android.archs` | arm64-v8a, armeabi-v7a | CPU Architekturen |
| `p4a.bootstrap` | sdl2 | Bootstrap fuer Kivy |
| `android.accept_sdk_license` | True | SDK Lizenzen auto-akzeptieren |

### Berechtigungen

Die App fordert folgende Berechtigungen an:
- `INTERNET` - Backend-Kommunikation
- `CAMERA` - Produktfotos aufnehmen
- `READ_EXTERNAL_STORAGE` - Bilder aus Galerie
- `WRITE_EXTERNAL_STORAGE` - Temporaere Dateien
- `ACCESS_NETWORK_STATE` - Netzwerk-Status pruefen
- `READ_MEDIA_IMAGES` - Android 13+ Medien-Zugriff

## Mobile App

### Funktionen
- Kamera-Integration fuer Produktfotos
- Galerie-Zugriff fuer bestehende Bilder
- AI-Analyse ueber Backend-API
- Offline-Modus mit Demo-Daten
- Ergebnis-Anzeige mit Preis, Keywords, Kategorie
- Konfigurierbare Backend-URL

### Architektur
```
EbayToolApp (Kivy App)
  |
  +-- HomeScreen
  |     +-- Bild-Upload (Kamera/Galerie)
  |     +-- API Client (Backend-Kommunikation)
  |     +-- Progress-Anzeige
  |
  +-- ResultScreen
        +-- Produkt-Details
        +-- Preis-Schaetzung
        +-- SEO Keywords
```

## Troubleshooting

### "Java not found"
```bash
sudo apt install openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### "NDK not found"
```bash
# Buildozer laedt NDK automatisch herunter
# Manuell: Android NDK r25b installieren
```

### "Build failed: permission denied"
```bash
# Docker Container mit korrekten Rechten starten
docker run --rm -u $(id -u):$(id -g) -v $(pwd)/bin:/workspace/bin ebay-apk-builder
```

### "SDK License not accepted"
```bash
# Automatisch in buildozer.spec:
android.accept_sdk_license = True

# Oder manuell:
yes | sdkmanager --licenses
```

### Build dauert sehr lange
- Erster Build: 30-60 Minuten (SDK/NDK Download)
- Folge-Builds: 5-15 Minuten (mit Cache)
- Docker Cache nutzen fuer schnellere CI-Builds

## Voraussetzungen

### Lokal
- Python 3.9+
- Java JDK 17
- ~10 GB freier Speicher (SDK + NDK)
- Linux oder macOS (Windows via WSL2)

### Docker
- Docker 20.10+
- ~15 GB Speicher fuer Image + Build

### CI/CD (GitHub Actions)
- ubuntu-22.04 Runner
- 120 Minuten Timeout
- Cache fuer .buildozer Verzeichnis
