import sys
import os
import re
import datetime
import random
import wikipedia
import pyttsx3
import requests
from collections import deque
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea, QFrame,
    QMenuBar, QAction, QGraphicsOpacityEffect, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QRect, QSize
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient, QIcon


# ==================== TASARIM AYARLARI ====================
class Design:
    PRIMARY_COLOR = "#7C4DFF"
    SECONDARY_COLOR = "#651FFF"
    BACKGROUND_COLOR = "#121212"
    CARD_COLOR = "#1E1E1E"
    TEXT_COLOR = "#FFFFFF"
    SUBTEXT_COLOR = "#BDBDBD"
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE = 14
    BORDER_RADIUS = 15
    SHADOW_COLOR = "#00000060"
    ANIMATION_DURATION = 400


# ==================== TÜRKÇE YAPAY ZEKA ====================
class TurkishAI:
    def __init__(self):
        self.responses = {
            'greeting': [
                "Merhaba! Nasıl yardımcı olabilirim? 🌟",
                "Selamlar! Sohbete başlamak için hazırım. 😊",
                "İyi günler! Bilgi almak için sorunuzu yazın. 📚"
            ],
            'question': [
                "Bu konuda daha fazla ayrıntı verebilir misiniz? 🤔",
                "Tam olarak neyi merak ediyorsunuz? 🧐",
                "Soru biraz daha açıklayıcı olursa yardımcı olabilirim. 💡"
            ],
            'error': [
                "Şu anda bu bilgiye ulaşamıyorum. 🌐",
                "Sanırım bir yanlış anlaşılma oldu. 😅",
                "Bu konuda yeterli bilgim yok, özür dilerim. 🙏"
            ]
        }

    def get_response(self, text):
        try:
            if self.is_greeting(text):
                return random.choice(self.responses['greeting'])

            result = self.wiki_search(text)
            return result if result else random.choice(self.responses['error'])

        except Exception as e:
            return f"Teknik bir hata oluştu: {str(e)}"

    def is_greeting(self, text):
        greetings = ['merhaba', 'selam', 'hey', 'nasılsın', 'iyi günler']
        return any(word in text.lower() for word in greetings)

    def wiki_search(self, text):
        try:
            wikipedia.set_lang("tr")
            results = wikipedia.search(text)
            if not results:
                return None

            page = wikipedia.page(results[0], auto_suggest=False)
            summary = wikipedia.summary(results[0], sentences=2)
            return f"📘 {page.title}:\n{summary}\n\n🔗 Daha fazlası: {page.url}"
        except:
            return None


# ==================== MODERN YÜKLEME EKRANI ====================
class LoadingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)
        self.setVisible(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(Design.PRIMARY_COLOR))
        gradient.setColorAt(1, QColor(Design.SECONDARY_COLOR))

        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        painter.drawEllipse(-25, -25, 50, 50)
        self.angle = (self.angle + 8) % 360


# ==================== MESAJ BİLEŞENİ ====================
class MessageBubble(QLabel):
    def __init__(self, text, is_user, parent=None):
        super().__init__(text, parent)
        self.is_user = is_user
        self.setup_ui()

    def setup_ui(self):
        self.setWordWrap(True)
        self.setMinimumWidth(200)
        self.setMaximumWidth(500)
        self.setMargin(15)
        self.setStyleSheet(f"""
            QLabel {{
                background: {Design.PRIMARY_COLOR if self.is_user else Design.CARD_COLOR};
                color: {Design.TEXT_COLOR};
                border-radius: {Design.BORDER_RADIUS}px;
                padding: 15px;
                font-family: {Design.FONT_FAMILY};
                font-size: {Design.FONT_SIZE}px;
                border: {'2px solid ' + Design.SECONDARY_COLOR if self.is_user else 'none'};
            }}
        """)
        self.setGraphicsEffect(QGraphicsOpacityEffect(opacity=0))


# ==================== ANA UYGULAMA ====================
class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ai = TurkishAI()
        self.engine = self.init_tts()
        self.setup_ui()
        self.history = deque(maxlen=20)

    def init_tts(self):
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        engine.setProperty('volume', 0.9)
        return engine

    def setup_ui(self):
        self.setWindowTitle("BilgiNova - Akıllı Asistan")
        self.setWindowIcon(QIcon("ai_icon.png"))
        self.setGeometry(100, 100, 1000, 800)
        self.setup_styles()

        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 15, 20, 15)
        self.main_layout.setSpacing(15)

        # Sohbet alanı
        self.setup_chat_area()

        # Giriş alanı
        self.setup_input_area()

        # Yükleme ekranı
        self.loading = LoadingScreen(self)
        self.loading.move(
            self.width() // 2 - self.loading.width() // 2,
            self.height() // 2 - self.loading.height() // 2
        )

    def setup_styles(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {Design.BACKGROUND_COLOR};
            }}
            QScrollArea {{
                border: none;
            }}
            QMenuBar {{
                background: {Design.CARD_COLOR};
                color: {Design.TEXT_COLOR};
                padding: 5px;
            }}
            QMenuBar::item:selected {{
                background: {Design.PRIMARY_COLOR};
            }}
        """)

    def setup_chat_area(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(15)
        self.chat_layout.setContentsMargins(5, 5, 5, 5)

        self.scroll_area.setWidget(self.chat_container)
        self.main_layout.addWidget(self.scroll_area)

    def setup_input_area(self):
        input_container = QFrame()
        input_container.setStyleSheet(f"""
            QFrame {{
                background: {Design.CARD_COLOR};
                border-radius: {Design.BORDER_RADIUS}px;
                padding: 10px;
            }}
        """)

        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(5, 5, 5, 5)
        input_layout.setSpacing(10)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Mesajınızı buraya yazın...")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {Design.TEXT_COLOR};
                font-family: {Design.FONT_FAMILY};
                font-size: {Design.FONT_SIZE}px;
                padding: 10px;
            }}
        """)
        self.input_field.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton()
        self.send_btn.setIcon(QIcon("send_icon.png"))
        self.send_btn.setIconSize(QSize(32, 32))
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Design.PRIMARY_COLOR};
                border-radius: {Design.BORDER_RADIUS}px;
                min-width: 50px;
                min-height: 50px;
            }}
            QPushButton:hover {{
                background: {Design.SECONDARY_COLOR};
            }}
        """)
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_field, 90)
        input_layout.addWidget(self.send_btn, 10)
        self.main_layout.addWidget(input_container)

    def add_message(self, text, is_user):
        bubble = MessageBubble(text, is_user)
        time_stamp = QLabel(datetime.datetime.now().strftime("%H:%M"))
        time_stamp.setStyleSheet(f"""
            color: {Design.SUBTEXT_COLOR};
            font-family: {Design.FONT_FAMILY};
            font-size: {Design.FONT_SIZE - 2}px;
        """)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)
        container_layout.addWidget(time_stamp, alignment=Qt.AlignRight if is_user else Qt.AlignLeft)
        container_layout.addWidget(bubble, alignment=Qt.AlignRight if is_user else Qt.AlignLeft)

        self.chat_layout.addWidget(container)
        self.animate_message(bubble)
        self.scroll_to_bottom()

    def animate_message(self, widget):
        anim = QPropertyAnimation(widget.graphicsEffect(), b"opacity")
        anim.setDuration(Design.ANIMATION_DURATION)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.OutBack)
        anim.start()

    def scroll_to_bottom(self):
        QTimer.singleShot(100, lambda:
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
                          )

    def send_message(self):
        text = self.input_field.text().strip()
        if text:
            self.add_message(text, True)
            self.input_field.clear()
            self.show_loading()
            QTimer.singleShot(800, lambda: self.process_message(text))

    def process_message(self, text):
        response = self.ai.get_response(text)
        self.add_message(response, False)
        self.speak(response)
        self.hide_loading()

    def show_loading(self):
        self.loading.setVisible(True)
        self.loading.raise_()

    def hide_loading(self):
        self.loading.setVisible(False)

    def speak(self, text):
        clean_text = re.sub(r'http\S+|\W+', ' ', text)
        self.engine.say(clean_text)
        self.engine.runAndWait()

    def closeEvent(self, event):
        self.engine.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont(Design.FONT_FAMILY, Design.FONT_SIZE))
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())