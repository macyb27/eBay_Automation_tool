# 📦 APK Build (ohne Sandbox)

Dieses Repo enthält aktuell **keinen nativen Android-Quellcode** (kein Gradle/Android-Studio-Projekt). Wenn du trotzdem ein Android-APK ausliefern willst, ist der schnellste Weg, die Mobile-UI als **Web-App** zu hosten und sie in eine **WebView-Hülle** (z. B. Capacitor) zu packen.

Wichtig für „ohne Sandbox“: Stelle sicher, dass deine Umgebung auf **Production** steht.

## 1) eBay-Sandbox deaktivieren (Production)

In deiner `.env`:

```bash
EBAY_ENVIRONMENT=production
# optional, nur für Backwards-Kompatibilität:
EBAY_SANDBOX=false
```

Damit werden (z. B. im Setup-Check) die **Live-Endpoints** verwendet statt `svcs.sandbox.ebay.com`.

## 2) Mobile UI hosten

Die Demo-UI ist in `simple_mobile_app.py` als mobile-optimierte Weboberfläche implementiert. Für ein APK brauchst du eine **stabile HTTPS-URL**, z. B.:

- `https://app.example.com/` (zeigt die UI)
- `https://app.example.com/analyze` (API-Call der UI)

## 3) APK via Capacitor (WebView Wrapper)

Voraussetzungen lokal (nicht in dieser Repo-VM):

- Node.js (LTS)
- Android Studio + Android SDK + Java (JDK 17)

Beispiel (neues Wrapper-Projekt, lädt deine gehostete URL):

```bash
mkdir mobile-apk && cd mobile-apk
npm init -y
npm i @capacitor/core @capacitor/cli
npx cap init "eBay Tool" "com.example.ebaytool" --web-dir=www
mkdir -p www
printf '<!doctype html><html><body>Redirecting…</body></html>' > www/index.html

npm i @capacitor/android
npx cap add android
```

Dann in `capacitor.config.*` (je nach Setup `json`/`ts`) die Server-URL setzen:

- `server.url = "https://app.example.com"`

Build (Release APK):

```bash
npx cap sync android
cd android
./gradlew assembleRelease
```

Das APK liegt dann unter `android/app/build/outputs/apk/release/`.

---

## Hinweis

Wenn du statt einer Remote-URL lieber **Assets im APK bundlen** willst, müssten wir die Mobile-UI aus `simple_mobile_app.py` als statische Dateien exportieren (HTML/CSS/JS) und im Wrapper-Projekt unter `www/` ablegen.

