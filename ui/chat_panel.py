from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QHBoxLayout, QTextEdit, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QEvent, QRect
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QCursor
import os
import json
import datetime

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

class ChatPanel(QWidget):
    send_message = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = {}
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        messages_container = QWidget()
        messages_container.setObjectName("messagesContainer")
        messages_layout = QVBoxLayout(messages_container)
        messages_layout.setContentsMargins(15, 15, 15, 15)
        messages_layout.setSpacing(15)
        messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("messagesScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidget(messages_container)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        input_container = QWidget()
        input_container.setObjectName("inputContainer")
        input_container.setMinimumHeight(80)
        input_container.setMaximumHeight(150)
        
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(15, 10, 15, 10)
        input_layout.setSpacing(10)
        
        self.message_input = QTextEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setMinimumHeight(60)
        self.message_input.setPlaceholderText("Mesajınızı buraya yazın...")
        self.message_input.installEventFilter(self)
        
        button_layout = QVBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.mic_button = QPushButton()
        self.mic_button.setObjectName("micButton")
        self.mic_button.setIcon(QIcon("assets/icons/mic.svg"))
        self.mic_button.setIconSize(QSize(18, 18))
        self.mic_button.setFixedSize(36, 36)
        self.mic_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mic_button.setToolTip("Mikrofon (Henüz aktif değil)")
        
        self.send_button = QPushButton()
        self.send_button.setObjectName("sendButton")
        self.send_button.setIcon(QIcon("assets/icons/send.svg"))
        self.send_button.setIconSize(QSize(18, 18))
        self.send_button.setFixedSize(36, 36)
        self.send_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.send_button.setToolTip("Mesaj Gönder")
        self.send_button.clicked.connect(self.send_user_message)
        
        button_layout.addWidget(self.mic_button)
        button_layout.addWidget(self.send_button)
        
        input_layout.addWidget(self.message_input)
        input_layout.addLayout(button_layout)
        
        main_layout.addWidget(self.scroll_area, 1)
        main_layout.addWidget(input_container)
        
        self.messages_widget = messages_container
        self.messages_layout = messages_layout
        
        self.apply_styles()
    
    def apply_styles(self):
        self.setStyleSheet("""
            #messagesContainer {
                background-color: #252526;
            }
            
            #messagesScrollArea {
                background-color: transparent;
                border: none;
            }
            
            #inputContainer {
                background-color: #1E1E1E;
                border-top: 1px solid #3E3E3E;
            }
            
            #messageInput {
                background-color: #3A3A3A;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 8px 12px;
                selection-background-color: #1E88E5;
            }
            
            #messageInput:focus {
                border: 1px solid #1E88E5;
            }
            
            #micButton, #sendButton {
                background-color: #3A3A3A;
                border: none;
                border-radius: 18px;
                padding: 6px;
            }
            
            #micButton:hover, #sendButton:hover {
                background-color: #1E88E5;
            }
            
            #micButton:pressed, #sendButton:pressed {
                background-color: #1976D2;
            }
            
            #chatMessage {
                margin: 2px 0px;
            }
            
            #userMessage {
                background-color: #3A3A3A;
                border-radius: 12px;
                border-top-right-radius: 2px;
                padding: 2px;
                max-width: 550px;
            }
            
            #aiMessage {
                background-color: #2A2A2A;
                border-radius: 12px;
                border-top-left-radius: 2px;
                padding: 2px;
                max-width: 550px;
            }
            
            #messageSender {
                color: #FFFFFF;
                font-weight: bold;
            }
            
            #messageTime {
                color: #AAAAAA;
            }
            
            #messageContent {
                color: #FFFFFF;
                font-size: 10pt;
                padding: 5px 2px;
            }
        """)
    
    def update_theme(self, theme):
        self.theme = theme
        self.apply_styles()
    
    def add_user_message(self, text):
        message = ChatMessage(text, is_user=True)
        self.messages_layout.addWidget(message)
        QTimer.singleShot(100, self.scroll_to_bottom)
        return message
    
    def add_ai_message(self, text):
        message = ChatMessage(text, is_user=False)
        self.messages_layout.addWidget(message)
        QTimer.singleShot(100, self.scroll_to_bottom)
        return message
    
    def send_user_message(self):
        text = self.message_input.toPlainText().strip()
        if text:
            self.send_message.emit(text)
            self.message_input.clear()
    
    def clear_messages(self):
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())
    
    def eventFilter(self, obj, event):
        if obj == self.message_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.send_user_message()
                return True
        return super().eventFilter(obj, event) 