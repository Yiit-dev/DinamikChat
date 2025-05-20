from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QHBoxLayout, QTextEdit, QSizePolicy, QProgressBar, QGraphicsOpacityEffect
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QEvent, QRect
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QCursor, QPainter, QPainterPath
import os
import json
import datetime
import tempfile
import sounddevice as sd
import soundfile as sf

class MessageCard(QFrame):
    def __init__(self, text, sender="user", parent=None, tema_yonetici=None):
        super().__init__(parent)
        self.sender = sender
        self.tema_yonetici = tema_yonetici
        self.setObjectName("messageCard")
        self.setMinimumHeight(40)
        self.setMaximumWidth(800)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        sender_label = QLabel("Siz" if sender == "user" else "Yapay Zeka")
        sender_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        sender_label.setObjectName("senderLabel")
        layout.addWidget(sender_label)
        
        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)
        message_label.setObjectName("messageLabel")
        layout.addWidget(message_label)
        
        self.setStyleSheet(self._get_style())
        self.animasyonBaslat()
    
    def animasyonBaslat(self):
        self.opak_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opak_anim.setDuration(150)
        self.opak_anim.setStartValue(0)
        self.opak_anim.setEndValue(1)
        self.opak_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.opak_anim.start()
    
    def _get_style(self):
        if not self.tema_yonetici:
            return ""
        
        renkler = self.tema_yonetici.renkleri_al()
        return f"""
            #messageCard {{
                background-color: {renkler['kullanici_mesaj'] if self.sender == 'user' else renkler['yapay_zeka_mesaj']};
                border-radius: 12px;
                border: 1px solid {renkler['kenar']};
            }}
            
            #senderLabel {{
                color: {renkler['metin']};
            }}
            
            #messageLabel {{
                color: {renkler['metin']};
                font-size: 14px;
                line-height: 1.4;
            }}
        """

class ChatMessage(QFrame):
    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.text = text
        self.init_ui()
    
    def init_ui(self):
        self.setObjectName("chatMessage")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        message_container = QFrame()
        message_container.setObjectName("userMessage" if self.is_user else "aiMessage")
        
        container_layout = QVBoxLayout(message_container)
        container_layout.setContentsMargins(12, 10, 12, 10)
        container_layout.setSpacing(5)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        icon_label = QLabel()
        if self.is_user:
            icon_label.setText("👤")
        else:
            icon_label.setText("🤖")
        icon_label.setFixedWidth(20)
        
        sender_label = QLabel("Siz" if self.is_user else "AI")
        sender_label.setObjectName("messageSender")
        sender_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        
        time_label = QLabel(datetime.datetime.now().strftime("%H:%M"))
        time_label.setObjectName("messageTime")
        time_label.setFont(QFont("Arial", 8))
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(sender_label)
        header_layout.addStretch(1)
        header_layout.addWidget(time_label)
        
        content_label = QLabel(self.text)
        content_label.setObjectName("messageContent")
        content_label.setFont(QFont("Arial", 10))
        content_label.setWordWrap(True)
        content_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        content_label.setTextFormat(Qt.TextFormat.PlainText)
        
        container_layout.addLayout(header_layout)
        container_layout.addWidget(content_label)
        
        if self.is_user:
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(message_container)
        
        self.initial_opacity = 0.0
        self.setStyleSheet(f"opacity: {self.initial_opacity};")
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setStartValue(self.initial_opacity)
        self.animation.setEndValue(1.0)
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        QTimer.singleShot(10, self.animation.start)

class VoiceRecordButton(QPushButton):
    recordingFinished = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recording = False
        self.setObjectName("micButton")
        self.setIcon(QIcon("assets/icons/mic.svg"))
        self.setIconSize(QSize(18, 18))
        self.setFixedSize(36, 36)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Sesli Mesaj Kaydet")
        
        self.progress = QProgressBar(self)
        self.progress.setObjectName("recordingProgress")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setFixedWidth(36)
        self.progress.move(0, 32)
        self.progress.hide()
        
        self.clicked.connect(self.toggle_recording)
        
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.pulse_effect)
    
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.recording = True
        self.setObjectName("micButtonRecording")
        self.setStyleSheet("""
            #micButtonRecording {
                background-color: #F44336;
                border: none;
                border-radius: 18px;
                padding: 6px;
            }
            
            #micButtonRecording:hover {
                background-color: #D32F2F;
            }
        """)
        self.progress.show()
        self.progress.setValue(0)
        
        self.pulse_animation = QPropertyAnimation(self, b"iconSize")
        self.pulse_animation.setDuration(500)
        self.pulse_animation.setStartValue(QSize(18, 18))
        self.pulse_animation.setEndValue(QSize(14, 14))
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.pulse_animation.setLoopCount(-1)
        self.pulse_animation.start()
        
        self.pulse_timer.start(100)
        
        QTimer.singleShot(3000, self.stop_recording)
    
    def stop_recording(self):
        if self.recording:
            self.pulse_animation.stop()
            self.pulse_timer.stop()
            self.progress.hide()
            self.setIconSize(QSize(18, 18))
            self.setObjectName("micButton")
            self.setStyleSheet("")
            self.recording = False
            
            temp_file = tempfile.mktemp(suffix='.wav')
            with open(temp_file, 'w') as f:
                f.write("dummy")
            
            self.recordingFinished.emit(temp_file)
    
    def pulse_effect(self):
        current_value = self.progress.value()
        new_value = current_value + 5
        if new_value > 100:
            new_value = 0
        self.progress.setValue(new_value)

class ChatPanel(QWidget):
    mesaj_gonderildi = pyqtSignal(str)
    ses_kaydi_basladi = pyqtSignal()
    ses_kaydi_bitti = pyqtSignal(str)
    
    def __init__(self, parent=None, tema_yonetici=None):
        super().__init__(parent)
        self.tema_yonetici = tema_yonetici
        self.aktif_konusma = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("messageScrollArea")
        
        self.mesaj_container = QWidget()
        self.mesaj_layout = QVBoxLayout(self.mesaj_container)
        self.mesaj_layout.setContentsMargins(16, 16, 16, 16)
        self.mesaj_layout.setSpacing(12)
        self.mesaj_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.mesaj_container)
        layout.addWidget(self.scroll_area)
        
        self.input_container = QWidget()
        self.input_container.setObjectName("inputContainer")
        self.input_container.setFixedHeight(60)
        
        input_layout = QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(16, 8, 16, 8)
        input_layout.setSpacing(8)
        
        self.mesaj_input = QTextEdit()
        self.mesaj_input.setPlaceholderText("Mesajınızı yazın...")
        self.mesaj_input.setObjectName("messageInput")
        self.mesaj_input.setMaximumHeight(44)
        self.mesaj_input.installEventFilter(self)
        input_layout.addWidget(self.mesaj_input)
        
        self.ses_kayit_btn = VoiceRecordButton()
        self.ses_kayit_btn.recordingFinished.connect(self.ses_kaydi_bitti.emit)
        input_layout.addWidget(self.ses_kayit_btn)
        
        self.gonder_btn = QPushButton()
        self.gonder_btn.setIcon(QIcon("assets/icons/send.png"))
        self.gonder_btn.setObjectName("sendButton")
        self.gonder_btn.setFixedSize(44, 44)
        self.gonder_btn.clicked.connect(self.send_message_clicked)
        input_layout.addWidget(self.gonder_btn)
        
        layout.addWidget(self.input_container)
        self.setStyleSheet(self._get_style())
        
    def _get_style(self):
        if not self.tema_yonetici:
            return ""
        
        renkler = self.tema_yonetici.renkleri_al()
        return f"""
            #messageScrollArea {{
                background-color: {renkler['arka_plan']};
                border: none;
            }}
            
            #messageScrollArea QWidget {{
                background-color: {renkler['arka_plan']};
            }}
            
            #inputContainer {{
                background-color: {renkler['panel']};
                border-top: 1px solid {renkler['kenar']};
            }}
            
            #messageInput {{
                background-color: {renkler['buton']};
                border: 1px solid {renkler['kenar']};
                border-radius: 8px;
                padding: 8px 12px;
                color: {renkler['metin']};
                font-size: 14px;
            }}
            
            #messageInput:focus {{
                border: 1px solid {renkler['vurgu']};
            }}
            
            #sendButton {{
                background-color: {renkler['vurgu']};
                border: none;
                border-radius: 8px;
                padding: 8px;
            }}
            
            #sendButton:hover {{
                background-color: {renkler['vurgu_hover']};
            }}
            
            #sendButton:pressed {{
                background-color: {renkler['vurgu_pressed']};
            }}
            
            #micButton {{
                background-color: {renkler['buton']};
                border: none;
                border-radius: 8px;
                padding: 8px;
            }}
            
            #micButton:hover {{
                background-color: {renkler['buton_hover']};
            }}
            
            #micButton:pressed {{
                background-color: {renkler['buton_pressed']};
            }}
            
            #micButtonRecording {{
                background-color: {renkler['hata']};
                border: none;
                border-radius: 8px;
                padding: 8px;
            }}
            
            #micButtonRecording:hover {{
                background-color: {renkler['hata']};
                opacity: 0.8;
            }}
            
            #recordingProgress {{
                background-color: {renkler['hata']};
                border: none;
                border-radius: 2px;
            }}
        """
        
    def set_conversation(self, conversation):
        self.aktif_konusma = conversation
        self.clear()
        if conversation:
            self.load_messages()
            
    def clear(self):
        while self.mesaj_layout.count():
            item = self.mesaj_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
    def load_messages(self):
        if not self.aktif_konusma:
            return
            
        for message in self.aktif_konusma.messages:
            self.add_message(message.text, message.sender)
            
    def add_message(self, text, sender="user"):
        message_card = MessageCard(text, sender, self, self.tema_yonetici)
        self.mesaj_layout.addWidget(message_card)
        self.scroll_to_bottom()
        
    def send_message_clicked(self):
        text = self.mesaj_input.toPlainText().strip()
        if text:
            self.mesaj_gonderildi.emit(text)
            self.mesaj_input.clear()
            
    def scroll_to_bottom(self):
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
        
    def eventFilter(self, obj, event):
        if obj == self.mesaj_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.send_message_clicked()
                return True
        return super().eventFilter(obj, event) 