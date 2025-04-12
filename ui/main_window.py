from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                            QPushButton, QLabel, QFrame, QApplication, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QClipboard, QAction

import json
import os

from ui.chat_panel import ChatPanel
from ui.model_viewer import ModelViewer
from ui.conversation_panel import ConversationPanel
from database import User, Message, get_db_session
from utils.openai_utils import chatgpt_manager
from utils.model_utils import model_manager

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        
        self.user = user
        
        with open('settings.json', 'r', encoding='utf-8') as f:
            self.settings = json.load(f)
        
        self.theme = self.settings['ui']['theme']['dark']
        self.app_name = self.settings['app_name']
        
        self.setWindowTitle(self.app_name)
        self.resize(1200, 800)
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_panel = QFrame()
        top_panel.setObjectName("topPanel")
        top_panel.setFixedHeight(50)
        
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(10, 0, 10, 0)
        
        app_name_label = QLabel(self.app_name)
        app_name_label.setObjectName("appNameLabel")
        app_name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        user_button = QPushButton(f"{self.user.first_name} {self.user.last_name}")
        user_button.setObjectName("userButton")
        user_button.setCursor(Qt.CursorShape.PointingHandCursor)
        user_button.clicked.connect(self.show_user_menu)
        
        mode_frame = QFrame()
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(5)
        
        self.theme_button = QPushButton()
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_button.setFixedSize(36, 36)
        self.theme_button.clicked.connect(self.toggle_theme)
        self.current_theme_name = 'dark'
        self.update_theme_button_icon()
        
        self.normal_mode_button = QPushButton("Normal")
        self.normal_mode_button.setObjectName("modeButton")
        self.normal_mode_button.setCheckable(True)
        self.normal_mode_button.setChecked(True)
        self.normal_mode_button.clicked.connect(lambda: self.set_mode("normal"))
        
        self.literary_mode_button = QPushButton("Edebi")
        self.literary_mode_button.setObjectName("modeButton")
        self.literary_mode_button.setCheckable(True)
        self.literary_mode_button.clicked.connect(lambda: self.set_mode("literary"))
        
        self.educational_mode_button = QPushButton("Öğretici")
        self.educational_mode_button.setObjectName("modeButton")
        self.educational_mode_button.setCheckable(True)
        self.educational_mode_button.clicked.connect(lambda: self.set_mode("educational"))
        
        self.technical_mode_button = QPushButton("Teknik")
        self.technical_mode_button.setObjectName("modeButton")
        self.technical_mode_button.setCheckable(True)
        self.technical_mode_button.clicked.connect(lambda: self.set_mode("technical"))
        
        self.conversational_mode_button = QPushButton("Sohbet")
        self.conversational_mode_button.setObjectName("modeButton")
        self.conversational_mode_button.setCheckable(True)
        self.conversational_mode_button.clicked.connect(lambda: self.set_mode("conversational"))
        
        self.reason_button = QPushButton()
        self.reason_button.setObjectName("featureButton")
        self.reason_button.setCheckable(True)
        self.reason_button.setToolTip("Akıl Yürütme")
        self.reason_button.setIcon(QIcon("assets/icons/reason.svg"))
        self.reason_button.setIconSize(QSize(18, 18))
        self.reason_button.clicked.connect(self.toggle_reason)
        
        self.web_search_button = QPushButton()
        self.web_search_button.setObjectName("featureButton")
        self.web_search_button.setCheckable(True)
        self.web_search_button.setToolTip("Web Arama")
        self.web_search_button.setIcon(QIcon("assets/icons/web_search.svg"))
        self.web_search_button.setIconSize(QSize(18, 18))
        self.web_search_button.clicked.connect(self.toggle_web_search)
        
        self.copy_button = QPushButton()
        self.copy_button.setObjectName("featureButton")
        self.copy_button.setToolTip("Kopyala")
        self.copy_button.setIcon(QIcon("assets/icons/copy.svg"))
        self.copy_button.setIconSize(QSize(18, 18))
        self.copy_button.clicked.connect(self.copy_last_message)
        
        mode_layout.addWidget(self.theme_button)
        mode_layout.addWidget(self.normal_mode_button)
        mode_layout.addWidget(self.literary_mode_button)
        mode_layout.addWidget(self.educational_mode_button)
        mode_layout.addWidget(self.technical_mode_button)
        mode_layout.addWidget(self.conversational_mode_button)
        mode_layout.addWidget(self.reason_button)
        mode_layout.addWidget(self.web_search_button)
        mode_layout.addWidget(self.copy_button)
        
        top_layout.addWidget(app_name_label)
        top_layout.addStretch()
        top_layout.addWidget(user_button)
        top_layout.addStretch()
        top_layout.addWidget(mode_frame)
        
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.conversation_panel = ConversationPanel(self.user)
        self.conversation_panel.conversation_selected.connect(self.load_conversation)
        self.conversation_panel.toggle_panel.connect(self.handle_panel_toggle)
        
        self.model_viewer = ModelViewer()
        self.model_viewer.animation_finished.connect(self.handle_animation_finished)
        
        model_data = model_manager.get_model_data()
        if model_data:
            self.model_viewer.set_model_data(model_data)
        else:
            QMessageBox.warning(self, "Model Yükleme Hatası", "3D model yüklenemedi.")
        
        self.chat_panel = ChatPanel()
        self.chat_panel.send_message.connect(self.handle_user_message)
        
        content_layout.addWidget(self.conversation_panel)
        content_layout.addWidget(self.model_viewer, 1)
        content_layout.addWidget(self.chat_panel, 1)
        
        main_layout.addWidget(top_panel)
        main_layout.addWidget(content_widget, 1)
        
        self.apply_styles()
        
        self.setCentralWidget(central_widget)
        
        QTimer.singleShot(100, self.initialize_conversation)
    
    def apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {self.theme['background']};
                color: {self.theme['foreground']};
                font-family: 'Segoe UI', Arial;
            }}
            
            #topPanel {{
                background-color: {self.theme['secondary']};
                border-bottom: 1px solid {self.theme['border']};
            }}
            
            #appNameLabel {{
                color: {self.theme['accent']};
                font-weight: bold;
            }}
            
            #userButton {{
                background-color: {self.theme['secondary']};
                color: {self.theme['foreground']};
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }}
            
            #userButton:hover {{
                background-color: {self.theme['hover']};
            }}
            
            #modeButton {{
                background-color: {self.theme['secondary']};
                color: {self.theme['foreground']};
                border: 1px solid {self.theme['border']};
                border-radius: 5px;
                padding: 5px 10px;
                min-width: 80px;
            }}
            
            #featureButton, #themeButton {{
                background-color: {self.theme['secondary']};
                color: {self.theme['foreground']};
                border: 1px solid {self.theme['border']};
                border-radius: 5px;
                padding: 5px;
                min-width: 36px;
                min-height: 36px;
            }}
            
            #modeButton:hover, #featureButton:hover, #themeButton:hover {{
                background-color: {self.theme['hover']};
            }}
            
            #modeButton:checked, #featureButton:checked {{
                background-color: {self.theme['accent']};
                color: white;
            }}
        """)
    
    def show_user_menu(self):
        menu = QMenu(self)
        
        profile_action = menu.addAction("Profil")
        logout_action = menu.addAction("Çıkış Yap")
        
        action = menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
        
        if action == profile_action:
            self.show_profile()
        elif action == logout_action:
            self.logout()
    
    def show_profile(self):
        QMessageBox.information(self, "Profil", "Profil özelliği henüz uygulanmadı.")
    
    def logout(self):
        reply = QMessageBox.question(
            self, "Çıkış", 
            "Çıkış yapmak istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
    
    def set_mode(self, mode):
        mode_buttons = {
            "normal": self.normal_mode_button,
            "literary": self.literary_mode_button,
            "educational": self.educational_mode_button,
            "technical": self.technical_mode_button,
            "conversational": self.conversational_mode_button
        }
        
        for button_mode, button in mode_buttons.items():
            button.setChecked(button_mode == mode)
        
        chat_mode = self.settings['ui']['modes'].get(mode, "")
        chatgpt_manager.set_response_mode(chat_mode)
        
        print(f"Mod değiştirildi: {mode} - {chat_mode}")
        
        self.chat_panel.show_info_message(f"Mod değiştirildi: {mode.capitalize()}")
    
    def toggle_theme(self):
        if self.current_theme_name == 'dark':
            self.current_theme_name = 'light'
            self.theme = self.settings['ui']['theme']['light']
        else:
            self.current_theme_name = 'dark'
            self.theme = self.settings['ui']['theme']['dark']
        
        self.update_theme_button_icon()
        
        self.apply_styles()
        
        self.conversation_panel.update_theme(self.theme)
        self.chat_panel.update_theme(self.theme)
    
    def update_theme_button_icon(self):
        # Tema düğmesi ikonunu ayarla
        if self.current_theme_name == 'dark':
            self.theme_button.setToolTip("Açık Tema")
            self.theme_button.setText("☀️")
        else:
            self.theme_button.setToolTip("Koyu Tema")
            self.theme_button.setText("🌓")
    
    def toggle_reason(self):
        is_enabled = chatgpt_manager.toggle_reason()
        self.reason_button.setChecked(is_enabled)
    
    def toggle_web_search(self):
        is_enabled = chatgpt_manager.toggle_web_search()
        self.web_search_button.setChecked(is_enabled)
    
    def handle_panel_toggle(self, is_expanded):
        if not is_expanded:
            self.model_viewer.setMinimumWidth(500)
        else:
            self.model_viewer.setMinimumWidth(300)
    
    def initialize_conversation(self):
        if not self.conversation_panel.current_conversation:
            self.chat_panel.add_message(
                "Lütfen bir sohbet kanalı seçin ya da oluşturun.", 
                is_user=False
            )
    
    def load_conversation(self, conversation):
        if not conversation:
            self.chat_panel.messages_layout.clear()
            self.chat_panel.add_message(
                "Lütfen bir sohbet kanalı seçin ya da oluşturun.",
                is_user=False
            )
            return
        
        for i in reversed(range(self.chat_panel.messages_layout.count())):
            item = self.chat_panel.messages_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        session = get_db_session()
        
        try:
            messages = session.query(Message).filter_by(
                conversation_id=conversation.conversation_id
            ).order_by(Message.message_date).all()
            
            if not messages:
                self.chat_panel.add_message(
                    f"Merhaba {self.user.first_name}, yeni sohbete hoş geldiniz!",
                    is_user=False
                )
            else:
                for message in messages:
                    self.chat_panel.add_message(message.message_content, is_user=True)
                    if message.response_message:
                        self.chat_panel.add_message(message.response_message, is_user=False)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Mesajlar yüklenirken bir hata oluştu: {str(e)}")
        finally:
            session.close()
    
    def handle_user_message(self, message):
        if not self.conversation_panel.current_conversation:
            QMessageBox.warning(self, "Hata", "Lütfen önce bir sohbet kanalı seçin veya oluşturun.")
            return
        
        conversation_id = self.conversation_panel.current_conversation.conversation_id
        
        session = get_db_session()
        
        try:
            new_message = Message(
                message_id=Message.generate_message_id(),
                conversation_id=conversation_id,
                message_content=message
            )
            
            session.add(new_message)
            session.commit()
            
            self.get_ai_response(new_message)
            
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Hata", f"Mesaj gönderilirken bir hata oluştu: {str(e)}")
        finally:
            session.close()
    
    def get_ai_response(self, message):
        def handle_response(response):
            session = get_db_session()
            
            try:
                db_message = session.query(Message).filter_by(
                    message_id=message.message_id
                ).first()
                
                if db_message:
                    db_message.response_message = response
                    session.commit()
                
                self.chat_panel.add_message(response, is_user=False)
                
                duration_ms = len(response) * 50
                frames = model_manager.calculate_mouth_animation_frames(response, duration_ms)
                if frames:
                    self.model_viewer.start_animation(frames)
                
                model_manager.animate_mouth_for_speech(response)
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"AI yanıtı işlenirken bir hata oluştu: {str(e)}")
            finally:
                session.close()
        
        chatgpt_manager.get_response(message.message_content, handle_response)
    
    def handle_animation_finished(self):
        pass 
    
    def copy_last_message(self):
        last_message = self.chat_panel.get_last_ai_message()
        if last_message:
            clipboard = QApplication.clipboard()
            clipboard.setText(last_message)
            self.statusBar().showMessage("Mesaj kopyalandı", 2000) 