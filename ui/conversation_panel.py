from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QHBoxLayout, QMenu, QLineEdit, QDialog, QSizePolicy, QMessageBox, QFileDialog
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QIcon, QFont, QAction, QColor, QPainter, QPainterPath

import datetime
from database import Conversation, get_db_session

class ConversationButton(QPushButton):
    rename_clicked = pyqtSignal()
    archive_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()
    
    def __init__(self, conversation, parent=None, tema_yonetici=None):
        super().__init__(parent)
        self.conversation = conversation
        self.tema_yonetici = tema_yonetici
        self.setObjectName("conversationButton")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        icon_label = QLabel()
        icon_label.setPixmap(QIcon("assets/icons/chat.png").pixmap(24, 24))
        layout.addWidget(icon_label)
        
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        
        title_label = QLabel(self.conversation.name)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        title_label.setObjectName("titleLabel")
        text_layout.addWidget(title_label)
        
        date_label = QLabel(self.conversation.created_at.strftime("%d.%m.%Y %H:%M"))
        date_label.setFont(QFont("Segoe UI", 8))
        date_label.setObjectName("dateLabel")
        text_layout.addWidget(date_label)
        
        layout.addWidget(text_container, 1)
        
        self.rename_btn = QPushButton()
        self.rename_btn.setIcon(QIcon("assets/icons/edit.png"))
        self.rename_btn.setToolTip("Yeniden Adlandır")
        self.rename_btn.setObjectName("renameButton")
        self.rename_btn.setFixedSize(32, 32)
        self.rename_btn.clicked.connect(self.rename_clicked.emit)
        self.rename_btn.hide()
        layout.addWidget(self.rename_btn)
        
        self.archive_btn = QPushButton()
        self.archive_btn.setIcon(QIcon("assets/icons/archive.png"))
        self.archive_btn.setToolTip("Arşivle")
        self.archive_btn.setObjectName("archiveButton")
        self.archive_btn.setFixedSize(32, 32)
        self.archive_btn.clicked.connect(self.archive_clicked.emit)
        self.archive_btn.hide()
        layout.addWidget(self.archive_btn)
        
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon("assets/icons/delete.png"))
        self.delete_btn.setToolTip("Sil")
        self.delete_btn.setObjectName("deleteButton")
        self.delete_btn.setFixedSize(32, 32)
        self.delete_btn.clicked.connect(self.delete_clicked.emit)
        self.delete_btn.hide()
        layout.addWidget(self.delete_btn)
        
        self.setStyleSheet(self._get_style())
        
    def enterEvent(self, event):
        self.rename_btn.show()
        self.archive_btn.show()
        self.delete_btn.show()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.rename_btn.hide()
        self.archive_btn.hide()
        self.delete_btn.hide()
        super().leaveEvent(event)
        
    def _get_style(self):
        if not self.tema_yonetici:
            return ""
        
        renkler = self.tema_yonetici.renkleri_al()
        return f"""
            #conversationButton {{
                background-color: {renkler['buton']};
                border: none;
                border-radius: 8px;
                text-align: left;
                padding: 0;
            }}
            
            #conversationButton:hover {{
                background-color: {renkler['buton_hover']};
            }}
            
            #conversationButton:pressed {{
                background-color: {renkler['buton_pressed']};
            }}
            
            #conversationButton:checked {{
                background-color: {renkler['vurgu']};
            }}
            
            #titleLabel {{
                color: {renkler['metin']};
            }}
            
            #dateLabel {{
                color: {renkler['metin_ikincil']};
            }}
            
            #renameButton, #archiveButton, #deleteButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px;
            }}
            
            #renameButton:hover, #archiveButton:hover {{
                background-color: {renkler['buton_hover']};
            }}
            
            #renameButton:pressed, #archiveButton:pressed {{
                background-color: {renkler['buton_pressed']};
            }}
            
            #deleteButton:hover {{
                background-color: {renkler['hata']};
            }}
            
            #deleteButton:pressed {{
                background-color: {renkler['hata']};
                opacity: 0.8;
            }}
        """

class ConversationPanel(QWidget):
    konusma_secildi = pyqtSignal(object)
    
    def __init__(self, parent=None, tema_yonetici=None):
        super().__init__(parent)
        self.tema_yonetici = tema_yonetici
        self.init_ui()
        self.load_conversations()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QWidget()
        header.setObjectName("conversationHeader")
        header.setFixedHeight(60)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(8)
        
        self.yeni_konusma_btn = QPushButton()
        self.yeni_konusma_btn.setIcon(QIcon("assets/icons/new.png"))
        self.yeni_konusma_btn.setObjectName("newConversationButton")
        self.yeni_konusma_btn.setFixedSize(44, 44)
        self.yeni_konusma_btn.clicked.connect(self.create_new_conversation_dialog)
        header_layout.addWidget(self.yeni_konusma_btn)
        
        self.arsivle_btn = QPushButton()
        self.arsivle_btn.setIcon(QIcon("assets/icons/archive.png"))
        self.arsivle_btn.setObjectName("archiveButton")
        self.arsivle_btn.setFixedSize(44, 44)
        self.arsivle_btn.clicked.connect(self.archive_all_conversations)
        header_layout.addWidget(self.arsivle_btn)
        
        header_layout.addStretch()
        layout.addWidget(header)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("conversationScrollArea")
        
        self.konusma_container = QWidget()
        self.konusma_layout = QVBoxLayout(self.konusma_container)
        self.konusma_layout.setContentsMargins(8, 8, 8, 8)
        self.konusma_layout.setSpacing(8)
        self.konusma_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.konusma_container)
        layout.addWidget(self.scroll_area)
        
        self.setStyleSheet(self._get_style())
        
    def _get_style(self):
        if not self.tema_yonetici:
            return ""
        
        renkler = self.tema_yonetici.renkleri_al()
        return f"""
            #conversationHeader {{
                background-color: {renkler['panel']};
                border-bottom: 1px solid {renkler['kenar']};
            }}
            
            #newConversationButton, #archiveButton {{
                background-color: {renkler['buton']};
                border: none;
                border-radius: 8px;
                padding: 8px;
            }}
            
            #newConversationButton:hover, #archiveButton:hover {{
                background-color: {renkler['buton_hover']};
            }}
            
            #newConversationButton:pressed, #archiveButton:pressed {{
                background-color: {renkler['buton_pressed']};
            }}
            
            #conversationScrollArea {{
                background-color: {renkler['arka_plan']};
                border: none;
            }}
            
            #conversationScrollArea QWidget {{
                background-color: {renkler['arka_plan']};
            }}
        """
        
    def load_conversations(self):
        self.clear_conversations()
        conversations = self.parent().db.get_conversations()
        for conversation in conversations:
            self.add_conversation_button(conversation)
            
    def add_conversation_button(self, conversation):
        button = ConversationButton(conversation, self, self.tema_yonetici)
        button.clicked.connect(lambda: self.conversation_clicked(conversation))
        button.rename_btn.clicked.connect(lambda: self.rename_conversation(conversation))
        button.archive_btn.clicked.connect(lambda: self.archive_conversation(conversation))
        button.delete_btn.clicked.connect(lambda: self.delete_conversation(conversation))
        button.archive_btn.setStyleSheet("background: #23272e; border: 1.5px solid #1E88E5; border-radius: 12px; color: #e0e0e0;")
        button.archive_btn.setFixedSize(32, 32)
        button.rename_btn.setStyleSheet("background: #23272e; border: 1.5px solid #1E88E5; border-radius: 12px; color: #e0e0e0;")
        button.rename_btn.setFixedSize(32, 32)
        button.delete_btn.setStyleSheet("background: #23272e; border: 1.5px solid #F44336; border-radius: 12px; color: #e0e0e0;")
        button.delete_btn.setFixedSize(32, 32)
        self.konusma_layout.addWidget(button)
        
    def clear_conversations(self):
        while self.konusma_layout.count():
            item = self.konusma_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
    def conversation_clicked(self, conversation):
        self.konusma_secildi.emit(conversation)
        
    def create_new_conversation_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Konuşma")
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        title_label = QLabel("Konuşma Başlığı:")
        title_input = QLineEdit()
        title_input.setPlaceholderText("Başlık girin...")
        
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("İptal")
        create_btn = QPushButton("Oluştur")
        
        cancel_btn.clicked.connect(dialog.reject)
        create_btn.clicked.connect(lambda: self.finish_create_conversation(title_input.text(), dialog))
        
        buttons.addWidget(cancel_btn)
        buttons.addWidget(create_btn)
        
        layout.addWidget(title_label)
        layout.addWidget(title_input)
        layout.addLayout(buttons)
        
        dialog.exec()
        
    def finish_create_conversation(self, title, dialog):
        if not title.strip():
            return
            
        conversation = self.parent().db.create_conversation(title)
        self.add_conversation_button(conversation)
        self.conversation_clicked(conversation)
        dialog.accept()
        
    def rename_conversation(self, conversation):
        dialog = QDialog(self)
        dialog.setWindowTitle("Konuşmayı Yeniden Adlandır")
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        title_label = QLabel("Yeni Başlık:")
        title_input = QLineEdit(conversation.title)
        
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("İptal")
        rename_btn = QPushButton("Yeniden Adlandır")
        
        cancel_btn.clicked.connect(dialog.reject)
        rename_btn.clicked.connect(lambda: self.finish_rename_conversation(conversation, title_input.text(), dialog))
        
        buttons.addWidget(cancel_btn)
        buttons.addWidget(rename_btn)
        
        layout.addWidget(title_label)
        layout.addWidget(title_input)
        layout.addLayout(buttons)
        
        dialog.exec()
        
    def finish_rename_conversation(self, conversation, new_title, dialog):
        if not new_title.strip():
            return
            
        conversation.title = new_title
        self.parent().db.update_conversation(conversation)
        self.load_conversations()
        dialog.accept()
        
    def delete_conversation(self, conversation):
        reply = QMessageBox.question(
            self,
            "Konuşmayı Sil",
            "Bu konuşmayı silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.parent().db.delete_conversation(conversation)
            self.load_conversations()
            
    def archive_conversation(self, conversation):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Konuşmayı Kaydet",
            f"{conversation.title}.txt",
            "Metin Dosyası (*.txt)"
        )
        
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Konuşma: {conversation.title}\n")
                f.write(f"Tarih: {conversation.created_at}\n\n")
                
                for message in conversation.messages:
                    sender = "Siz" if message.sender == "user" else "Yapay Zeka"
                    f.write(f"{sender}: {message.text}\n\n")
                    
    def archive_all_conversations(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Tüm Konuşmaları Kaydet",
            "konusmalar.txt",
            "Metin Dosyası (*.txt)"
        )
        
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                conversations = self.parent().db.get_conversations()
                for conversation in conversations:
                    f.write(f"Konuşma: {conversation.title}\n")
                    f.write(f"Tarih: {conversation.created_at}\n\n")
                    
                    for message in conversation.messages:
                        sender = "Siz" if message.sender == "user" else "Yapay Zeka"
                        f.write(f"{sender}: {message.text}\n\n")
                        
                    f.write("-" * 50 + "\n\n") 