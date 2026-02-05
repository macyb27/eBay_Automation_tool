#!/bin/bash
# ============================================
# eBay Automation Tool - APK Build Script
# Baut die Android APK OHNE Sandbox-Umgebung
# ============================================
#
# Verwendung:
#   ./build_apk.sh              # Debug APK bauen
#   ./build_apk.sh release      # Release APK bauen
#   ./build_apk.sh clean        # Build-Verzeichnis aufraeumen
#   ./build_apk.sh setup        # Nur Build-Umgebung einrichten
#
# ============================================

set -e

# Farben fuer Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Konfiguration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_MODE="${1:-debug}"
BUILDOZER_SPEC="$SCRIPT_DIR/buildozer.spec"
MOBILE_APP_DIR="$SCRIPT_DIR/mobile_app"
OUTPUT_DIR="$SCRIPT_DIR/bin"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  eBay Automation Tool - APK Builder${NC}"
echo -e "${BLUE}  Modus: ${YELLOW}${BUILD_MODE}${NC}"
echo -e "${BLUE}  Sandbox: ${RED}DEAKTIVIERT${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================
# Hilfsfunktionen
# ============================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# ============================================
# Voraussetzungen pruefen
# ============================================

check_prerequisites() {
    log_info "Pruefe Voraussetzungen..."

    # Python pruefen
    if check_command python3; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        log_info "Python gefunden: $PYTHON_VERSION"
    else
        log_error "Python3 nicht gefunden! Bitte installieren."
        exit 1
    fi

    # pip pruefen
    if ! check_command pip3 && ! check_command pip; then
        log_error "pip nicht gefunden! Bitte installieren."
        exit 1
    fi

    # Java pruefen (fuer Android SDK)
    if check_command java; then
        JAVA_VERSION=$(java -version 2>&1 | head -n 1)
        log_info "Java gefunden: $JAVA_VERSION"
    else
        log_warn "Java nicht gefunden. Wird fuer Android SDK benoetigt."
        log_info "Installation: sudo apt install openjdk-17-jdk"
    fi

    # Buildozer pruefen
    if ! check_command buildozer; then
        log_warn "Buildozer nicht installiert. Wird jetzt installiert..."
        install_buildozer
    else
        BUILDOZER_VERSION=$(buildozer version 2>&1 || echo "unbekannt")
        log_info "Buildozer gefunden: $BUILDOZER_VERSION"
    fi

    # Buildozer Spec pruefen
    if [ ! -f "$BUILDOZER_SPEC" ]; then
        log_error "buildozer.spec nicht gefunden unter: $BUILDOZER_SPEC"
        exit 1
    fi

    # Mobile App pruefen
    if [ ! -f "$MOBILE_APP_DIR/main.py" ]; then
        log_error "mobile_app/main.py nicht gefunden!"
        exit 1
    fi

    log_info "Alle Voraussetzungen erfuellt!"
    echo ""
}

# ============================================
# Build-Umgebung einrichten (OHNE Sandbox)
# ============================================

install_buildozer() {
    log_info "Installiere Build-Abhaengigkeiten OHNE Sandbox..."

    # System-Pakete (Debian/Ubuntu)
    if check_command apt-get; then
        log_info "Installiere System-Pakete..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq \
            python3-pip \
            python3-setuptools \
            python3-venv \
            build-essential \
            git \
            zip \
            unzip \
            openjdk-17-jdk \
            autoconf \
            libtool \
            pkg-config \
            zlib1g-dev \
            libncurses5-dev \
            libncursesw5-dev \
            libtinfo5 \
            cmake \
            libffi-dev \
            libssl-dev \
            automake \
            lld \
            2>/dev/null || true
    fi

    # Buildozer und Cython installieren (System-weit, OHNE virtualenv)
    log_info "Installiere Buildozer und Python-Abhaengigkeiten..."
    pip3 install --user --upgrade \
        buildozer \
        cython==0.29.36 \
        virtualenv \
        sh \
        2>/dev/null || \
    pip install --user --upgrade \
        buildozer \
        cython==0.29.36 \
        virtualenv \
        sh

    # python-for-android installieren
    pip3 install --user --upgrade python-for-android 2>/dev/null || \
    pip install --user --upgrade python-for-android

    # PATH aktualisieren
    export PATH="$HOME/.local/bin:$PATH"

    log_info "Build-Umgebung eingerichtet!"
}

setup_android_sdk() {
    log_info "Pruefe Android SDK..."

    # Android SDK Verzeichnis
    ANDROID_HOME="${ANDROID_HOME:-$HOME/.buildozer/android/platform/android-sdk}"

    if [ -d "$ANDROID_HOME" ]; then
        log_info "Android SDK gefunden: $ANDROID_HOME"
    else
        log_info "Android SDK wird von Buildozer automatisch heruntergeladen."
    fi

    export ANDROID_HOME
    export ANDROID_SDK_ROOT="$ANDROID_HOME"
}

# ============================================
# Build-Aktionen
# ============================================

clean_build() {
    log_info "Raeume Build-Verzeichnisse auf..."

    if [ -d "$SCRIPT_DIR/.buildozer" ]; then
        rm -rf "$SCRIPT_DIR/.buildozer"
        log_info ".buildozer Verzeichnis entfernt"
    fi

    if [ -d "$OUTPUT_DIR" ]; then
        rm -rf "$OUTPUT_DIR"
        log_info "bin/ Verzeichnis entfernt"
    fi

    log_info "Aufraeumen abgeschlossen!"
}

build_debug_apk() {
    log_info "Starte DEBUG APK Build..."
    log_info "OHNE Sandbox-Umgebung (direkt im System)"
    echo ""

    cd "$SCRIPT_DIR"

    # Umgebungsvariablen fuer Build ohne Sandbox
    export ANDROIDSDK="$HOME/.buildozer/android/platform/android-sdk"
    export ANDROIDNDK="$HOME/.buildozer/android/platform/android-ndk-r25b"
    export ANDROIDAPI="33"
    export NDKAPI="24"

    # Buildozer ohne Sandbox ausfuehren
    # --verbose fuer detaillierte Ausgabe
    # Die Sandbox wird durch die Konfiguration in buildozer.spec deaktiviert
    buildozer -v android debug 2>&1 | tee "$SCRIPT_DIR/build.log"

    BUILD_EXIT_CODE=${PIPESTATUS[0]}

    if [ $BUILD_EXIT_CODE -eq 0 ]; then
        echo ""
        log_info "============================================"
        log_info "  DEBUG APK erfolgreich gebaut!"
        log_info "============================================"

        # APK finden
        APK_PATH=$(find "$OUTPUT_DIR" -name "*.apk" -type f 2>/dev/null | head -1)
        if [ -n "$APK_PATH" ]; then
            APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
            log_info "APK Pfad: $APK_PATH"
            log_info "APK Groesse: $APK_SIZE"
        fi
    else
        log_error "Build fehlgeschlagen! Siehe build.log fuer Details."
        exit 1
    fi
}

build_release_apk() {
    log_info "Starte RELEASE APK Build..."
    log_warn "Fuer Release wird ein Keystore benoetigt!"
    echo ""

    # Keystore pruefen/erstellen
    KEYSTORE_PATH="$SCRIPT_DIR/ebaytools.keystore"
    if [ ! -f "$KEYSTORE_PATH" ]; then
        log_info "Erstelle neuen Keystore..."
        keytool -genkey -v \
            -keystore "$KEYSTORE_PATH" \
            -keyalg RSA \
            -keysize 2048 \
            -validity 10000 \
            -alias ebaytools \
            -storepass ebaytools123 \
            -keypass ebaytools123 \
            -dname "CN=eBay Tools, OU=Development, O=eBayTools, L=Berlin, S=Berlin, C=DE"

        log_info "Keystore erstellt: $KEYSTORE_PATH"
        log_warn "WICHTIG: Keystore-Passwort aendern fuer Production!"
    fi

    cd "$SCRIPT_DIR"

    # Umgebungsvariablen fuer Release Build
    export P4A_RELEASE_KEYSTORE="$KEYSTORE_PATH"
    export P4A_RELEASE_KEYALIAS="ebaytools"
    export P4A_RELEASE_KEYSTORE_PASSWD="ebaytools123"
    export P4A_RELEASE_KEYALIAS_PASSWD="ebaytools123"

    # Release Build ohne Sandbox
    buildozer -v android release 2>&1 | tee "$SCRIPT_DIR/build.log"

    BUILD_EXIT_CODE=${PIPESTATUS[0]}

    if [ $BUILD_EXIT_CODE -eq 0 ]; then
        echo ""
        log_info "============================================"
        log_info "  RELEASE APK erfolgreich gebaut!"
        log_info "============================================"

        APK_PATH=$(find "$OUTPUT_DIR" -name "*-release*.apk" -type f 2>/dev/null | head -1)
        if [ -n "$APK_PATH" ]; then
            APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
            log_info "APK Pfad: $APK_PATH"
            log_info "APK Groesse: $APK_SIZE"
        fi
    else
        log_error "Release Build fehlgeschlagen! Siehe build.log fuer Details."
        exit 1
    fi
}

deploy_to_device() {
    log_info "Deploye APK auf verbundenes Geraet..."

    if ! check_command adb; then
        log_error "adb nicht gefunden! Android SDK Platform-Tools installieren."
        exit 1
    fi

    # Geraet pruefen
    DEVICES=$(adb devices | tail -n +2 | head -n -1)
    if [ -z "$DEVICES" ]; then
        log_error "Kein Android-Geraet verbunden!"
        log_info "Tipp: USB-Debugging aktivieren und Geraet verbinden."
        exit 1
    fi

    cd "$SCRIPT_DIR"
    buildozer android deploy run logcat 2>&1 | tee "$SCRIPT_DIR/deploy.log"
}

# ============================================
# Hauptprogramm
# ============================================

case "$BUILD_MODE" in
    debug)
        check_prerequisites
        setup_android_sdk
        build_debug_apk
        ;;
    release)
        check_prerequisites
        setup_android_sdk
        build_release_apk
        ;;
    clean)
        clean_build
        ;;
    setup)
        check_prerequisites
        install_buildozer
        setup_android_sdk
        log_info "Setup abgeschlossen! Starte Build mit: ./build_apk.sh"
        ;;
    deploy)
        deploy_to_device
        ;;
    *)
        echo "Verwendung: $0 {debug|release|clean|setup|deploy}"
        echo ""
        echo "  debug   - Debug APK bauen (Standard)"
        echo "  release - Signierte Release APK bauen"
        echo "  clean   - Build-Verzeichnisse aufraeumen"
        echo "  setup   - Nur Build-Umgebung einrichten"
        echo "  deploy  - APK auf Geraet installieren und starten"
        exit 1
        ;;
esac

echo ""
log_info "Fertig!"
