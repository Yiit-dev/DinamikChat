from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QLineEdit, QPushButton, QScrollArea, QLabel, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QDateTime
from PyQt6.QtGui import QIcon, QFont, QColor
import speech_recognition as sr
import threading
import markdown
import json

class ChatMessage(QFrame):
    def __init__(self, is_user, message, timestamp=None, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.message = message
        self.timestamp = timestamp or QDateTime.currentDateTime()
        
        self.setObjectName("userMessage" if is_user else "aiMessage")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()

        icon_label = QLabel()
        icon_label.setObjectName("messageIcon")
        icon_label.setText("👤" if self.is_user else "🤖")
        icon_label.setFont(QFont("Arial", 10))

        name_label = QLabel("Sen" if self.is_user else "DinamikChat")
        name_label.setObjectName("messageName")
        name_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))

        time_str = self.timestamp.toString("hh:mm")
        time_label = QLabel(time_str)
        time_label.setObjectName("messageTime")
        time_label.setFont(QFont("Arial", 8))

        copy_button = QPushButton("📋")
        copy_button.setObjectName("copyButton")
        copy_button.setFixedSize(20, 20)
        copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_button.clicked.connect(self.copy_message)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        header_layout.addWidget(time_label)
        header_layout.addWidget(copy_button)

        message_label = QTextEdit()
        message_label.setObjectName("messageContent")
        message_label.setReadOnly(True)

        html_content = markdown.markdown(self.message)
        message_label.setHtml(html_content)

        message_label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        message_label.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        doc_height = message_label.document().size().height()
        message_label.setMinimumHeight(min(doc_height + 10, 300))
        
        layout.addLayout(header_layout)
        layout.addWidget(message_label)
    
    def copy_message(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.message)

class ChatPanel(QWidget):
    send_message = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        with open('settings.json', 'r', encoding='utf-8') as f:
            self.settings = json.load(f)
        
        self.theme = self.settings['ui']['theme']['dark']
        
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.messages_container)

        input_frame = QFrame()
        input_frame.setObjectName("inputFrame")
        input_layout = QHBoxLayout(input_frame)
        
        self.message_input = QTextEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText("Bir mesaj yazın...")
        self.message_input.setMinimumHeight(50)
        self.message_input.setMaximumHeight(100)
        
        send_button = QPushButton()
        send_button.setObjectName("sendButton")
        send_button.setIcon(QIcon("assets/icons/send.svg"))
        send_button.setFixedSize(40, 40)
        send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        send_button.clicked.connect(self.send_user_message)
        
        mic_button = QPushButton()
        mic_button.setObjectName("micButton")
        mic_button.setIcon(QIcon("assets/icons/mic.svg"))
        mic_button.setFixedSize(40, 40)
        mic_button.setCursor(Qt.CursorShape.PointingHandCursor)
        mic_button.clicked.connect(self.start_voice_input)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(mic_button)
        input_layout.addWidget(send_button)

        main_layout.addWidget(self.scroll_area, 1)
        main_layout.addWidget(input_frame)

        self.apply_styles()

        self.message_widgets = []
    
    def apply_styles(self):
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #121212;
            }
            
            #userMessage {
                background-color: #1E3A8A;
                border-radius: 10px;
                padding: 10px;
                margin: 5px 50px 5px 10px;
            }
            
            #aiMessage {
                background-color: #2A2A2A;
                border-radius: 10px;
                padding: 10px;
                margin: 5px 10px 5px 50px;
            }
            
            #messageIcon {
                font-size: 16px;
            }
            
            #messageName {
                color: #E0E0E0;
                font-weight: bold;
            }
            
            #messageTime {
                color: #909090;
                font-size: 8pt;
            }
            
            #messageContent {
                border: none;
                background-color: transparent;
                color: #F0F0F0;
            }
            
            #copyButton {
                background-color: transparent;
                border: none;
                color: #909090;
                font-size: 12px;
            }
            
            #copyButton:hover {
                color: #E0E0E0;
            }
            
            #inputFrame {
                background-color: #2A2A2A;
                border-top: 1px solid #3A3A3A;
                padding: 10px;
            }
            
            #messageInput {
                background-color: #363636;
                border-radius: 10px;
                padding: 10px;
                color: #F0F0F0;
                border: 1px solid #555;
            }
            
            #sendButton, #micButton {
                background-color: #00AAFF;
                border-radius: 20px;
                border: none;
            }
            
            #sendButton:hover, #micButton:hover {
                background-color: #0088CC;
            }
        """)
    
    def add_message(self, message, is_user=True):
        chat_message = ChatMessage(is_user, message)
        self.messages_layout.addWidget(chat_message)
        self.message_widgets.append(chat_message)

        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

        if is_user:
            self.send_message.emit(message)
    
    def send_user_message(self):
        message = self.message_input.toPlainText().strip()
        if message:
            self.add_message(message, True)
            self.message_input.clear()
    
    def start_voice_input(self):
        def recognize_speech():
            recognizer = sr.Recognizer()
            
            try:
                with sr.Microphone() as source:
                    self.message_input.setPlaceholderText("Dinleniyor...")
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.listen(source, timeout=5)
                
                self.message_input.setPlaceholderText("İşleniyor...")
                try:
                    text = recognizer.recognize_google(audio, language="tr-TR")
                    self.message_input.setText(text)
                except sr.UnknownValueError:
                    self.message_input.setPlaceholderText("Ses anlaşılamadı, tekrar deneyin...")
                except sr.RequestError:
                    self.message_input.setPlaceholderText("Ses tanıma servisi çalışmıyor...")
            except Exception as e:
                self.message_input.setPlaceholderText(f"Hata: {str(e)}")

            def reset_placeholder():
                import time
                time.sleep(2)
                self.message_input.setPlaceholderText("Bir mesaj yazın...")
            
            threading.Thread(target=reset_placeholder).start()

        threading.Thread(target=recognize_speech).start()

    def get_last_ai_message(self):
        if not hasattr(self, 'message_widgets') or not self.message_widgets:
            return None

        for widget in reversed(self.message_widgets):
            if hasattr(widget, 'is_user') and not widget.is_user:
                return widget.message
        
        return None

    def clear_messages(self):
        self.messages_layout.clear()

    def update_theme(self, theme):
        self.theme = theme

        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.theme['background']};
            }}
            
            #userMessage {{
                background-color: {self.theme['user_message']};
            }}
            
            #aiMessage {{
                background-color: {self.theme['ai_message']};
            }}
            
            #messageIcon {{
                color: {self.theme['icon']};
            }}
            
            #messageName {{
                color: {self.theme['name']};
            }}
            
            #messageTime {{
                color: {self.theme['time']};
            }}
            
            #messageContent {{
                color: {self.theme['content']};
            }}
            
            #copyButton {{
                color: {self.theme['copy_button']};
            }}
            
            #copyButton:hover {{
                color: {self.theme['copy_button_hover']};
            }}
            
            #inputFrame {{
                background-color: {self.theme['input_frame']};
            }}
            
            #messageInput {{
                background-color: {self.theme['input']};
                color: {self.theme['input_text']};
                border: 1px solid {self.theme['input_border']};
            }}
            
            #sendButton, #micButton {{
                background-color: {self.theme['button']};
            }}
            
            #sendButton:hover, #micButton:hover {{
                background-color: {self.theme['button_hover']};
            }}
        """) 