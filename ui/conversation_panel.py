from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QHBoxLayout, QMenu, QLineEdit, QDialog, QSizePolicy, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QIcon, QFont, QAction, QColor, QPainter, QPainterPath

import datetime
from database import Conversation, get_db_session

class ConversationButton(QPushButton):
    def __init__(self, conversation, parent=None):
        super().__init__(parent)
        self.conversation = conversation
        self.setObjectName("conversationButton")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 10, 8)
        layout.setSpacing(10)
        
        self.icon_label = QLabel()
        self.icon_label.setObjectName("channelIcon")
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        first_letter = self.conversation.name[0].upper()
        self.icon_label.setText(first_letter)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
 
        title_label = QLabel(self.conversation.name)
        title_label.setObjectName("channelTitle")
        title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        date_str = "Bugün" if datetime.date.today() == self.conversation.created_at.date() else self.conversation.created_at.strftime("%d/%m/%Y")
        date_label = QLabel(date_str)
        date_label.setObjectName("channelDate")
        date_label.setFont(QFont("Arial", 9))
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(date_label)

        actions_container = QWidget()
        actions_container.setFixedWidth(90)
        actions_container.setObjectName("actionButtonsContainer")
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        actions_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.rename_btn = QPushButton()
        self.rename_btn.setObjectName("actionButton")
        self.rename_btn.setIcon(QIcon("assets/icons/edit_icon.png"))
        self.rename_btn.setIconSize(QSize(14, 14))
        self.rename_btn.setFixedSize(24, 24)
        self.rename_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rename_btn.setToolTip("Yeniden Adlandır")
        self.rename_btn.setProperty("action", "rename")

        self.archive_btn = QPushButton()
        self.archive_btn.setObjectName("actionButton")
        self.archive_btn.setIcon(QIcon("assets/icons/archive_icon.png"))
        self.archive_btn.setIconSize(QSize(14, 14))
        self.archive_btn.setFixedSize(24, 24)
        self.archive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.archive_btn.setToolTip("Arşivle")
        self.archive_btn.setProperty("action", "archive")

        self.delete_btn = QPushButton()
        self.delete_btn.setObjectName("actionButton")
        self.delete_btn.setIcon(QIcon("assets/icons/delete_icon.png"))
        self.delete_btn.setIconSize(QSize(14, 14))
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setToolTip("Sil")
        self.delete_btn.setProperty("action", "delete")
        
        actions_layout.addWidget(self.rename_btn)
        actions_layout.addWidget(self.archive_btn)
        actions_layout.addWidget(self.delete_btn)
        
        actions_container.setVisible(False)
        
        layout.addWidget(self.icon_label)
        layout.addLayout(content_layout, 1)
        layout.addWidget(actions_container)
        
        self.actions_container = actions_container
    
    def enterEvent(self, event):
        self.actions_container.setVisible(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.actions_container.setVisible(False)
        super().leaveEvent(event)

class ConversationPanel(QWidget):
    conversation_selected = pyqtSignal(object)
    
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.buttons = []
        self.selected_conversation = None
        
        self.init_ui()
        self.load_conversations()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header_container = QWidget()
        header_container.setFixedHeight(40)
        header_container.setObjectName("headerContainer")
        
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        title_label = QLabel("Sohbet Kanalları")
        title_label.setObjectName("panelTitle")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        add_btn = QPushButton()
        add_btn.setObjectName("addButton")
        add_btn.setIcon(QIcon("assets/icons/add_icon.png"))
        add_btn.setIconSize(QSize(16, 16))
        add_btn.setFixedSize(28, 28)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setToolTip("Yeni Kanal Ekle")
        add_btn.clicked.connect(self.create_new_conversation_dialog)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_btn)

        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        scrollArea.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.content_widget = QWidget()
        self.content_widget.setObjectName("conversationContainer")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 5)
        self.content_layout.setSpacing(1)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scrollArea.setWidget(self.content_widget)

        layout.addWidget(header_container)
        layout.addWidget(scrollArea, 1)

        self.setStyleSheet("""
            #conversationContainer {
                background-color: transparent;
            }
            
            #headerContainer {
                background-color: transparent;
                border-bottom: 1px solid #3E3E3E;
            }
            
            #panelTitle {
                color: #FFFFFF;
                font-weight: bold;
            }
            
            #addButton {
                background-color: #3A3A3A;
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                padding: 2px;
            }
            
            #addButton:hover {
                background-color: #1E88E5;
            }
            
            #addButton:pressed {
                background-color: #1976D2;
            }
            
            #conversationButton {
                background-color: transparent;
                border: none;
                border-radius: 0px;
                text-align: left;
                margin: 0px;
                padding: 0px;
            }
            
            #conversationButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
            
            #conversationButton:checked {
                background-color: rgba(30, 136, 229, 0.2);
                border-left: 3px solid #1E88E5;
            }
            
            #channelIcon {
                background-color: #1976D2;
                border-radius: 16px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            
            #conversationButton:checked #channelIcon {
                background-color: #1E88E5;
                color: white;
            }
            
            #channelTitle {
                color: #FFFFFF;
                font-weight: bold;
            }
            
            #channelDate {
                color: #AAAAAA;
                font-size: 9pt;
            }
            
            #actionButtonsContainer {
                background-color: transparent;
            }
            
            #actionButton {
                background-color: #3A3A3A;
                border: none;
                border-radius: 12px;
                padding: 2px;
            }
            
            #actionButton:hover {
                background-color: #1E88E5;
            }
            
            #actionButton[action="delete"]:hover {
                background-color: #F44336;
            }
        """)
    
    def load_conversations(self):
        session = get_db_session()
        conversations = session.query(Conversation).filter_by(user_id=self.user.user_id).order_by(Conversation.created_at.desc()).all()
        session.close()
        
        self.clear_conversations()
        
        for conversation in conversations:
            self.add_conversation_button(conversation)
        
        if self.buttons and conversations:
            self.select_conversation(conversations[0])
    
    def add_conversation_button(self, conversation):
        button = ConversationButton(conversation)
        button.clicked.connect(lambda checked, c=conversation: self.conversation_clicked(c))
        button.rename_btn.clicked.connect(lambda: self.rename_conversation(conversation))
        button.archive_btn.clicked.connect(lambda: self.archive_conversation(conversation))
        button.delete_btn.clicked.connect(lambda: self.delete_conversation(conversation))
        
        self.content_layout.addWidget(button)
        self.buttons.append(button)
        
        return button
    
    def clear_conversations(self):
        self.buttons = []
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
    
    def conversation_clicked(self, conversation):
        self.select_conversation(conversation)
        self.conversation_selected.emit(conversation)
    
    def select_conversation(self, conversation):
        self.selected_conversation = conversation
        
        for button in self.buttons:
            button.setChecked(button.conversation == conversation)
    
    def archive_conversation(self, conversation):
        confirm_dialog = QMessageBox()
        confirm_dialog.setWindowTitle("Arşivleme Onayı")
        confirm_dialog.setText(f"{conversation.name} kanalı arşivlenecek. Onaylıyor musunuz?")
        confirm_dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm_dialog.setDefaultButton(QMessageBox.StandardButton.No)
        
        if confirm_dialog.exec() == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            db_conversation = session.query(Conversation).filter_by(conversation_id=conversation.conversation_id).first()
            
            if db_conversation:
                db_conversation.is_archived = True
                session.commit()

                self.load_conversations()

                if self.selected_conversation and self.selected_conversation.conversation_id == conversation.conversation_id:
                    remaining_conversations = session.query(Conversation).filter_by(
                        user_id=self.user.user_id, 
                        is_archived=False
                    ).all()
                    
                    if remaining_conversations:
                        self.select_conversation(remaining_conversations[0])
                        self.conversation_selected.emit(remaining_conversations[0])
                    else:
                        self.selected_conversation = None
                        self.conversation_selected.emit(None)
            
            session.close()
    
    def create_new_conversation_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Sohbet")
        dialog.setFixedSize(400, 150)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1F2937;
            }
            
            QLabel {
                color: #E6EDF3;
                font-size: 12px;
            }
            
            QLineEdit {
                background-color: #0D1117;
                color: #E6EDF3;
                border: 1px solid #30363D;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
            }
            
            QLineEdit:focus {
                border: 1px solid #3182CE;
            }
            
            QPushButton {
                background-color: #3182CE;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #4299E1;
            }
            
            QPushButton#cancelButton {
                background-color: #2D3748;
                color: #E6EDF3;
                border: 1px solid #4A5568;
            }
            
            QPushButton#cancelButton:hover {
                background-color: #4A5568;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        name_label = QLabel("Sohbet Adı:")
        name_input = QLineEdit()
        name_input.setText(f"Yeni Sohbet {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        name_input.selectAll()
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        cancel_button = QPushButton("İptal")
        cancel_button.setObjectName("cancelButton")
        
        create_button = QPushButton("Oluştur")
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(create_button)
        
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        layout.addLayout(button_layout)
        
        cancel_button.clicked.connect(dialog.reject)
        create_button.clicked.connect(lambda: self.finish_create_conversation(name_input.text(), dialog))
        
        dialog.exec()
    
    def finish_create_conversation(self, name, dialog):
        if name.strip():
            new_conversation = self.create_new_conversation(name)
            if new_conversation:
                self.select_conversation(new_conversation)
                self.conversation_selected.emit(new_conversation)
            dialog.accept()
        else:
            name_input.setFocus()
    
    def create_new_conversation(self, name):
        session = get_db_session()
        
        new_conversation = Conversation(
            conversation_id=Conversation.generate_conversation_id(),
            user_id=self.user.user_id,
            name=name
        )
        
        session.add(new_conversation)
        session.commit()
        
        button = self.add_conversation_button(new_conversation)

        animation = QPropertyAnimation(button, b"maximumHeight")
        animation.setDuration(300)
        animation.setStartValue(0)
        animation.setEndValue(60)
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        animation.start()
        
        session.close()
        return new_conversation
    
    def rename_conversation(self, conversation):
        dialog = QDialog(self)
        dialog.setWindowTitle("Sohbeti Yeniden Adlandır")
        dialog.setFixedSize(400, 150)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1F2937;
            }
            
            QLabel {
                color: #E6EDF3;
                font-size: 12px;
            }
            
            QLineEdit {
                background-color: #0D1117;
                color: #E6EDF3;
                border: 1px solid #30363D;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
            }
            
            QLineEdit:focus {
                border: 1px solid #3182CE;
            }
            
            QPushButton {
                background-color: #3182CE;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #4299E1;
            }
            
            QPushButton#cancelButton {
                background-color: #2D3748;
                color: #E6EDF3;
                border: 1px solid #4A5568;
            }
            
            QPushButton#cancelButton:hover {
                background-color: #4A5568;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        name_label = QLabel("Yeni İsim:")
        name_input = QLineEdit()
        name_input.setText(conversation.name)
        name_input.selectAll()
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        cancel_button = QPushButton("İptal")
        cancel_button.setObjectName("cancelButton")
        
        save_button = QPushButton("Kaydet")
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        layout.addLayout(button_layout)
        
        cancel_button.clicked.connect(dialog.reject)
        save_button.clicked.connect(lambda: self.finish_rename_conversation(conversation, name_input.text(), dialog))
        
        dialog.exec()
    
    def finish_rename_conversation(self, conversation, new_name, dialog):
        if new_name.strip():
            session = get_db_session()
            conv = session.query(Conversation).filter_by(conversation_id=conversation.conversation_id).first()
            if conv:
                conv.name = new_name
                session.commit()

                self.load_conversations()
                self.select_conversation(conv)
            
            session.close()
            dialog.accept()
        else:
            name_input.setFocus()
    
    def delete_conversation(self, conversation):
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Sohbeti Sil",
            f"'{conversation.name}' sohbetini silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            conv = session.query(Conversation).filter_by(conversation_id=conversation.conversation_id).first()
            
            if conv:
                session.delete(conv)
                session.commit()
                
                is_selected = (self.selected_conversation == conversation)
                self.load_conversations()

                if is_selected and self.buttons:
                    self.conversation_clicked(self.buttons[0].conversation)
                elif is_selected:
                    self.conversation_selected.emit(None)
            
            session.close()
    
    def share_conversation(self, conversation):
        from PyQt6.QtWidgets import QMessageBox
        
        QMessageBox.information(
            self,
            "Paylaşım",
            "Sohbet paylaşım özelliği henüz mevcut değil.",
            QMessageBox.StandardButton.Ok
        ) 