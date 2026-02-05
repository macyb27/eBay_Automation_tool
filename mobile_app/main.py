"""
eBay Automation Tool - Android Mobile App
Kivy-basierte WebView-App fuer Android APK Build ohne Sandbox
"""

import os
import sys
import json
import threading
import logging
from functools import partial

# Kivy Configuration (muss VOR kivy imports stehen)
os.environ.setdefault('KIVY_LOG_LEVEL', 'info')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp, sp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivy.utils import platform

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Android-spezifische Imports
if platform == 'android':
    from android.permissions import request_permissions, Permission, check_permission
    from android.storage import primary_external_storage_path
    from android import activity
    from jnius import autoclass, cast

    # Java Klassen fuer Android
    Intent = autoclass('android.content.Intent')
    MediaStore = autoclass('android.provider.MediaStore')
    Uri = autoclass('android.net.Uri')
    Environment = autoclass('android.os.Environment')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')

# ============================================
# Backend API Client
# ============================================

class APIClient:
    """HTTP Client fuer die Backend-Kommunikation"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    def set_base_url(self, url):
        self.base_url = url

    def analyze_image(self, image_path, callback):
        """Sendet Bild an Backend zur Analyse (im Background Thread)"""
        def _worker():
            try:
                import urllib.request
                import urllib.parse

                url = f"{self.base_url}/analyze"

                # Multipart Form Data erstellen
                boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
                filename = os.path.basename(image_path)

                with open(image_path, 'rb') as f:
                    file_data = f.read()

                # Content-Type basierend auf Dateiendung
                ext = filename.lower().split('.')[-1]
                content_types = {
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'webp': 'image/webp',
                }
                content_type = content_types.get(ext, 'image/jpeg')

                body = (
                    f'--{boundary}\r\n'
                    f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                    f'Content-Type: {content_type}\r\n\r\n'
                ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')

                req = urllib.request.Request(
                    url,
                    data=body,
                    headers={
                        'Content-Type': f'multipart/form-data; boundary={boundary}',
                    },
                    method='POST'
                )

                with urllib.request.urlopen(req, timeout=60) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    Clock.schedule_once(lambda dt: callback(True, result))

            except Exception as e:
                logger.error(f"API Error: {e}")
                Clock.schedule_once(lambda dt: callback(False, str(e)))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def health_check(self, callback):
        """Prueft ob Backend erreichbar ist"""
        def _worker():
            try:
                import urllib.request
                url = f"{self.base_url}/health"
                with urllib.request.urlopen(url, timeout=5) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    Clock.schedule_once(lambda dt: callback(True, result))
            except Exception as e:
                Clock.schedule_once(lambda dt: callback(False, str(e)))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()


# ============================================
# Screens
# ============================================

class HomeScreen(Screen):
    """Hauptbildschirm mit Upload-Funktion"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_client = APIClient()
        self.selected_image_path = None
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(60))
        title = Label(
            text='eBay Automation Tool',
            font_size=sp(22),
            bold=True,
            color=(0.2, 0.2, 0.2, 1),
            halign='center'
        )
        header.add_widget(title)
        layout.add_widget(header)

        # Subtitle
        subtitle = Label(
            text='Foto -> AI-Analyse -> eBay Ready',
            font_size=sp(14),
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=dp(30),
            halign='center'
        )
        layout.add_widget(subtitle)

        # Status Indicator
        self.status_label = Label(
            text='Verbindung wird geprueft...',
            font_size=sp(12),
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=None,
            height=dp(30),
            halign='center'
        )
        layout.add_widget(self.status_label)

        # Image Preview Area
        self.preview_container = BoxLayout(
            orientation='vertical',
            size_hint_y=0.4,
            padding=dp(8)
        )
        self.preview_label = Label(
            text='Tippe hier um ein\nProduktfoto aufzunehmen\noder aus der Galerie zu waehlen',
            font_size=sp(16),
            color=(0.4, 0.4, 0.8, 1),
            halign='center',
            valign='middle'
        )
        self.preview_label.bind(size=self.preview_label.setter('text_size'))
        self.preview_image = AsyncImage(
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True
        )
        self.preview_image.opacity = 0
        self.preview_container.add_widget(self.preview_label)
        self.preview_container.add_widget(self.preview_image)

        # Touch Event auf Preview-Bereich
        self.preview_container.bind(on_touch_down=self._on_preview_touch)
        layout.add_widget(self.preview_container)

        # Buttons
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(8)
        )

        camera_btn = Button(
            text='Kamera',
            font_size=sp(14),
            background_color=(0.4, 0.5, 0.9, 1),
            background_normal='',
            color=(1, 1, 1, 1),
        )
        camera_btn.bind(on_press=self._open_camera)

        gallery_btn = Button(
            text='Galerie',
            font_size=sp(14),
            background_color=(0.5, 0.3, 0.8, 1),
            background_normal='',
            color=(1, 1, 1, 1),
        )
        gallery_btn.bind(on_press=self._open_gallery)

        button_layout.add_widget(camera_btn)
        button_layout.add_widget(gallery_btn)
        layout.add_widget(button_layout)

        # Analyze Button
        self.analyze_btn = Button(
            text='Mit AI analysieren',
            font_size=sp(16),
            bold=True,
            size_hint_y=None,
            height=dp(55),
            background_color=(0.2, 0.7, 0.3, 1),
            background_normal='',
            color=(1, 1, 1, 1),
            disabled=True
        )
        self.analyze_btn.bind(on_press=self._start_analysis)
        layout.add_widget(self.analyze_btn)

        # Progress Bar
        self.progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(6)
        )
        self.progress.opacity = 0
        layout.add_widget(self.progress)

        # Status Text
        self.analysis_status = Label(
            text='',
            font_size=sp(13),
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=dp(30),
            halign='center'
        )
        layout.add_widget(self.analysis_status)

        # Server URL Einstellung
        settings_layout = BoxLayout(
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8),
            padding=(dp(4), 0)
        )
        server_label = Label(
            text='Server:',
            font_size=sp(12),
            color=(0.5, 0.5, 0.5, 1),
            size_hint_x=0.2
        )
        self.server_input = TextInput(
            text='http://localhost:8000',
            font_size=sp(12),
            size_hint_x=0.8,
            multiline=False,
            height=dp(36)
        )
        self.server_input.bind(text=self._on_server_change)
        settings_layout.add_widget(server_label)
        settings_layout.add_widget(self.server_input)
        layout.add_widget(settings_layout)

        # Footer
        footer = Label(
            text='Powered by OpenAI GPT-4V',
            font_size=sp(10),
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=None,
            height=dp(25)
        )
        layout.add_widget(footer)

        self.add_widget(layout)

        # Health Check beim Start
        Clock.schedule_once(lambda dt: self._check_connection(), 1)

    def _on_server_change(self, instance, value):
        self.api_client.set_base_url(value.strip())

    def _check_connection(self):
        def _callback(success, data):
            if success:
                self.status_label.text = 'Backend verbunden'
                self.status_label.color = (0.2, 0.7, 0.3, 1)
            else:
                self.status_label.text = 'Backend nicht erreichbar - Offline-Modus'
                self.status_label.color = (0.9, 0.5, 0.1, 1)

        self.api_client.health_check(_callback)

    def _on_preview_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self._open_gallery(None)

    def _request_permissions(self):
        """Android Berechtigungen anfordern"""
        if platform == 'android':
            request_permissions([
                Permission.CAMERA,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_MEDIA_IMAGES,
            ])

    def _open_camera(self, instance):
        """Kamera oeffnen"""
        if platform == 'android':
            self._request_permissions()
            try:
                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                currentActivity = cast(
                    'android.app.Activity',
                    PythonActivity.mActivity
                )
                currentActivity.startActivityForResult(intent, 1)
                activity.bind(on_activity_result=self._on_activity_result)
            except Exception as e:
                logger.error(f"Camera error: {e}")
                self._show_error(f"Kamera-Fehler: {e}")
        else:
            self._show_file_chooser()

    def _open_gallery(self, instance):
        """Galerie oeffnen"""
        if platform == 'android':
            self._request_permissions()
            try:
                intent = Intent(Intent.ACTION_PICK)
                intent.setType("image/*")
                currentActivity = cast(
                    'android.app.Activity',
                    PythonActivity.mActivity
                )
                currentActivity.startActivityForResult(intent, 2)
                activity.bind(on_activity_result=self._on_activity_result)
            except Exception as e:
                logger.error(f"Gallery error: {e}")
                self._show_error(f"Galerie-Fehler: {e}")
        else:
            self._show_file_chooser()

    def _on_activity_result(self, request_code, result_code, intent):
        """Callback fuer Android Activity Results"""
        if result_code == -1:  # RESULT_OK
            try:
                if request_code in (1, 2) and intent:
                    uri = intent.getData()
                    if uri:
                        # URI in Dateipfad konvertieren
                        path = self._uri_to_path(uri)
                        if path:
                            self._set_image(path)
            except Exception as e:
                logger.error(f"Activity result error: {e}")

    def _uri_to_path(self, uri):
        """Android URI zu Dateipfad konvertieren"""
        if platform == 'android':
            try:
                ContentResolver = autoclass('android.content.ContentResolver')
                context = PythonActivity.mActivity.getApplicationContext()
                resolver = context.getContentResolver()
                cursor = resolver.query(uri, None, None, None, None)
                if cursor:
                    cursor.moveToFirst()
                    idx = cursor.getColumnIndex("_data")
                    if idx >= 0:
                        path = cursor.getString(idx)
                        cursor.close()
                        return path
                    cursor.close()

                # Fallback: InputStream verwenden
                input_stream = resolver.openInputStream(uri)
                if input_stream:
                    import tempfile
                    temp_path = os.path.join(
                        context.getCacheDir().getAbsolutePath(),
                        'temp_image.jpg'
                    )
                    FileOutputStream = autoclass('java.io.FileOutputStream')
                    fos = FileOutputStream(temp_path)
                    buffer = bytearray(4096)
                    while True:
                        bytes_read = input_stream.read(buffer)
                        if bytes_read == -1:
                            break
                        fos.write(buffer, 0, bytes_read)
                    fos.close()
                    input_stream.close()
                    return temp_path
            except Exception as e:
                logger.error(f"URI to path error: {e}")
        return None

    def _show_file_chooser(self):
        """Desktop File Chooser (fuer Entwicklung)"""
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserListView(
            filters=['*.png', '*.jpg', '*.jpeg', '*.webp'],
            path=os.path.expanduser('~')
        )
        content.add_widget(file_chooser)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        select_btn = Button(text='Auswaehlen', font_size=sp(14))
        cancel_btn = Button(text='Abbrechen', font_size=sp(14))

        btn_layout.add_widget(select_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(
            title='Bild auswaehlen',
            content=content,
            size_hint=(0.9, 0.9)
        )

        def _select(instance):
            if file_chooser.selection:
                self._set_image(file_chooser.selection[0])
                popup.dismiss()

        select_btn.bind(on_press=_select)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _set_image(self, path):
        """Ausgewaehltes Bild setzen"""
        self.selected_image_path = path
        self.preview_image.source = path
        self.preview_image.opacity = 1
        self.preview_label.text = ''
        self.analyze_btn.disabled = False
        self.analyze_btn.background_color = (0.2, 0.7, 0.3, 1)
        logger.info(f"Image selected: {path}")

    def _start_analysis(self, instance):
        """AI-Analyse starten"""
        if not self.selected_image_path:
            self._show_error("Bitte zuerst ein Bild auswaehlen!")
            return

        self.analyze_btn.disabled = True
        self.analyze_btn.text = 'Analyse laeuft...'
        self.progress.opacity = 1
        self.progress.value = 10
        self.analysis_status.text = 'AI analysiert dein Produkt...'

        # Simulierte Progress Updates
        Clock.schedule_once(lambda dt: self._update_progress(30, 'Bildanalyse...'), 1)
        Clock.schedule_once(lambda dt: self._update_progress(60, 'Marktdaten werden geladen...'), 3)
        Clock.schedule_once(lambda dt: self._update_progress(80, 'Content wird generiert...'), 5)

        # API Call
        self.api_client.analyze_image(
            self.selected_image_path,
            self._on_analysis_complete
        )

    def _update_progress(self, value, text):
        self.progress.value = value
        self.analysis_status.text = text

    def _on_analysis_complete(self, success, result):
        """Analyse-Ergebnis verarbeiten"""
        self.progress.value = 100
        self.analyze_btn.disabled = False
        self.analyze_btn.text = 'Mit AI analysieren'

        if success and result.get('success'):
            self.analysis_status.text = 'Analyse abgeschlossen!'
            self.analysis_status.color = (0.2, 0.7, 0.3, 1)

            # Zum Result Screen wechseln
            result_screen = self.manager.get_screen('result')
            result_screen.show_results(result.get('data', {}))
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = 'result'
        else:
            error_msg = result if isinstance(result, str) else result.get('error', 'Unbekannter Fehler')
            self.analysis_status.text = f'Fehler: {error_msg}'
            self.analysis_status.color = (0.9, 0.2, 0.2, 1)

            # Mock-Ergebnis fuer Offline-Modus
            if 'Connection' in str(error_msg) or 'urlopen' in str(error_msg):
                self._show_offline_result()

    def _show_offline_result(self):
        """Offline-Demo-Ergebnis anzeigen"""
        mock_data = {
            "product": {
                "name": "Demo Produkt",
                "category": "Elektronik",
                "condition": "Sehr gut",
                "brand": "Unbekannt",
                "features": ["Feature 1", "Feature 2"]
            },
            "estimated_value_range": [1500, 4500],
            "suggested_keywords": ["elektronik", "gebraucht", "top-zustand"],
            "condition_details": "Offline-Modus - Verbinde mit Backend fuer echte Analyse",
            "confidence_score": 0.0
        }
        result_screen = self.manager.get_screen('result')
        result_screen.show_results(mock_data)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'result'

    def _show_error(self, message):
        popup = Popup(
            title='Fehler',
            content=Label(text=message, font_size=sp(14)),
            size_hint=(0.8, 0.3)
        )
        popup.open()


class ResultScreen(Screen):
    """Ergebnis-Bildschirm"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        self.layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))

        # Header mit Zurueck-Button
        header = BoxLayout(size_hint_y=None, height=dp(50))
        back_btn = Button(
            text='< Zurueck',
            font_size=sp(14),
            size_hint_x=0.3,
            background_color=(0.5, 0.5, 0.5, 1),
            background_normal='',
            color=(1, 1, 1, 1)
        )
        back_btn.bind(on_press=self._go_back)
        header.add_widget(back_btn)
        header.add_widget(Label(
            text='Analyse-Ergebnis',
            font_size=sp(18),
            bold=True,
            color=(0.2, 0.2, 0.2, 1)
        ))
        self.layout.add_widget(header)

        # Scrollable Results
        self.scroll = ScrollView(size_hint=(1, 1))
        self.results_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(12),
            padding=dp(8)
        )
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        self.scroll.add_widget(self.results_layout)
        self.layout.add_widget(self.scroll)

        self.add_widget(self.layout)

    def show_results(self, data):
        """Ergebnisse anzeigen"""
        self.results_layout.clear_widgets()

        product = data.get('product', {})
        value_range = data.get('estimated_value_range', [0, 0])
        keywords = data.get('suggested_keywords', [])
        condition = data.get('condition_details', '')
        confidence = data.get('confidence_score', 0)

        # Produkt-Name
        self._add_result_card(
            'Produkt',
            product.get('name', 'Unbekannt'),
            (0.4, 0.5, 0.9, 1)
        )

        # Kategorie
        self._add_result_card(
            'Kategorie',
            product.get('category', 'Unbekannt'),
            (0.5, 0.3, 0.8, 1)
        )

        # Preis
        price_low = value_range[0] / 100 if value_range[0] > 100 else value_range[0]
        price_high = value_range[1] / 100 if value_range[1] > 100 else value_range[1]
        self._add_result_card(
            'Geschaetzter Preis',
            f'{price_low:.2f} EUR - {price_high:.2f} EUR',
            (0.15, 0.68, 0.38, 1)
        )

        # Zustand
        self._add_result_card(
            'Zustand',
            product.get('condition', 'Nicht erkannt'),
            (0.95, 0.6, 0.07, 1)
        )

        # Marke
        if product.get('brand'):
            self._add_result_card(
                'Marke',
                product['brand'],
                (0.2, 0.6, 0.8, 1)
            )

        # Keywords
        if keywords:
            self._add_result_card(
                'SEO Keywords',
                ', '.join(keywords),
                (0.8, 0.2, 0.4, 1)
            )

        # Details
        if condition:
            self._add_result_card(
                'Details',
                condition,
                (0.5, 0.5, 0.5, 1)
            )

        # Konfidenz
        self._add_result_card(
            'AI-Konfidenz',
            f'{confidence * 100:.0f}%',
            (0.3, 0.3, 0.3, 1)
        )

    def _add_result_card(self, label, value, color):
        """Ergebnis-Karte hinzufuegen"""
        card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(70),
            padding=dp(12)
        )

        label_widget = Label(
            text=label,
            font_size=sp(12),
            color=color,
            bold=True,
            halign='left',
            size_hint_y=None,
            height=dp(20)
        )
        label_widget.bind(size=label_widget.setter('text_size'))

        value_widget = Label(
            text=str(value),
            font_size=sp(16),
            color=(0.2, 0.2, 0.2, 1),
            halign='left',
            size_hint_y=None,
            height=dp(30)
        )
        value_widget.bind(size=value_widget.setter('text_size'))

        card.add_widget(label_widget)
        card.add_widget(value_widget)
        self.results_layout.add_widget(card)

    def _go_back(self, instance):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'


# ============================================
# Main App
# ============================================

class EbayToolApp(App):
    """Haupt-App Klasse"""

    title = 'eBay Automation Tool'

    def build(self):
        # Window-Groesse fuer Desktop-Entwicklung
        if platform != 'android':
            Window.size = (400, 700)

        # Screen Manager
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ResultScreen(name='result'))

        return sm

    def on_start(self):
        """App Start"""
        logger.info("eBay Automation Tool gestartet")
        if platform == 'android':
            self._request_android_permissions()

    def _request_android_permissions(self):
        """Android Berechtigungen anfordern"""
        try:
            request_permissions([
                Permission.CAMERA,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.INTERNET,
                Permission.READ_MEDIA_IMAGES,
            ])
        except Exception as e:
            logger.warning(f"Permission request error: {e}")

    def on_pause(self):
        """App in Hintergrund - True = App nicht beenden"""
        return True

    def on_resume(self):
        """App wieder im Vordergrund"""
        logger.info("App resumed")


# ============================================
# Entry Point
# ============================================

if __name__ == '__main__':
    EbayToolApp().run()
