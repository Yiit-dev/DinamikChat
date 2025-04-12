from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QMenu, QFileDialog,QInputDialog, QMessageBox, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont
import json
import os
import datetime

from database import Conversation, get_db_session, Message
from utils.animation_utils import AnimationUtils

class ConversationButton(QPushButton):
    selected = pyqtSignal(Conversation)
    delete_requested = pyqtSignal(Conversation)
    rename_requested = pyqtSignal(Conversation)
    archive_requested = pyqtSignal(Conversation)
    
    def __init__(self, conversation, parent=None):
        super().__init__(parent)
        self.conversation = conversation
        self.setObjectName("conversationButton")
        self.setText(conversation.name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setCheckable(True)
        
        self.clicked.connect(self.handle_clicked)

        self.setWindowOpacity(0)
        self.fade_in()
    
    def fade_in(self):
        self.fade_animation = AnimationUtils.fade_animation(self, 0.0, 1.0, 300)
        self.fade_animation.start()
    
    def handle_clicked(self):
        self.selected.emit(self.conversation)
    
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        rename_action = menu.addAction("Yeniden Adlandır")
        archive_action = menu.addAction("Arşivle")
        delete_action = menu.addAction("Sil")
        
        action = menu.exec(self.mapToGlobal(event.pos()))
        
        if action == rename_action:
            self.rename_requested.emit(self.conversation)
        elif action == archive_action:
            self.archive_requested.emit(self.conversation)
        elif action == delete_action:
            self.delete_requested.emit(self.conversation)

class ConversationPanel(QWidget):
    conversation_selected = pyqtSignal(Conversation)
    toggle_panel = pyqtSignal(bool)
    
    def __init__(self, user, parent=None):
        super().__init__(parent)
        
        with open('settings.json', 'r', encoding='utf-8') as f:
            self.settings = json.load(f)
        
        self.theme = self.settings['ui']['theme']['dark']
        self.user = user
        self.conversations = []
        self.current_conversation = None
        self.conversation_buttons = {}
        self.is_expanded = True
        self.max_conversations = 10
        
        self.init_ui()
        self.load_conversations()
    
    def init_ui(self):
        self.setFixedWidth(250)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        header_frame = QFrame()
        header_frame.setObjectName("panelHeader")
        header_frame.setFixedHeight(50)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        title_label = QLabel("Sohbet Kanalları")
        title_label.setObjectName("panelTitle")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.toggle_button = QPushButton("◀")
        self.toggle_button.setObjectName("toggleButton")
        self.toggle_button.setFixedSize(30, 30)
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.clicked.connect(self.toggle_panel_visibility)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_button)

        new_chat_button = QPushButton("+ Yeni Sohbet")
        new_chat_button.setObjectName("newChatButton")
        new_chat_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_chat_button.clicked.connect(self.create_new_conversation)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.conversations_container = QWidget()
        self.conversations_layout = QVBoxLayout(self.conversations_container)
        self.conversations_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.conversations_layout.setContentsMargins(5, 5, 5, 5)
        self.conversations_layout.setSpacing(5)
        
        scroll_area.setWidget(self.conversations_container)

        main_layout.addWidget(header_frame)
        main_layout.addWidget(new_chat_button)
        main_layout.addWidget(scroll_area)
        
        self.apply_styles()
        
        self.start_appearance_animation()
    
    def start_appearance_animation(self):
        self.setWindowOpacity(0)
        self.fade_animation = AnimationUtils.fade_animation(self, 0.0, 1.0, 500)
        self.fade_animation.start()
    
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1A1A1A;
                color: #F0F0F0;
            }
            
            #panelHeader {
                background-color: #2A2A2A;
                border-bottom: 1px solid #3A3A3A;
            }
            
            #panelTitle {
                color: #E0E0E0;
                font-weight: bold;
            }
            
            #toggleButton {
                background-color: #00AAFF;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            
            #toggleButton:hover {
                background-color: #0088CC;
            }
            
            #newChatButton {
                background-color: #2A2A2A;
                color: #F0F0F0;
                border: 1px solid #3A3A3A;
                border-radius: 5px;
                padding: 8px;
                margin: 5px 10px;
            }
            
            #newChatButton:hover {
                background-color: #3A3A3A;
            }
            
            #conversationButton {
                background-color: #2A2A2A;
                color: #F0F0F0;
                border: none;
                border-radius: 5px;
                padding: 8px;
                text-align: left;
            }
            
            #conversationButton:hover {
                background-color: #3A3A3A;
            }
            
            #conversationButton:checked {
                background-color: #00AAFF;
                color: white;
            }
            
            QScrollArea {
                border: none;
            }
        """)
    
    def load_conversations(self):
        session = get_db_session()
        
        try:
            conversations = session.query(Conversation).filter_by(
                user_id=self.user.user_id,
                is_archived=False
            ).order_by(Conversation.created_at.desc()).all()
            
            self.conversations = conversations

            for button in self.conversation_buttons.values():
                self.conversations_layout.removeWidget(button)
                button.deleteLater()
            
            self.conversation_buttons = {}
            
            for conversation in conversations:
                self.add_conversation_button(conversation)
            
            if conversations and not self.current_conversation:
                self.select_conversation(conversations[0])
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sohbetler yüklenirken bir hata oluştu: {str(e)}")
        finally:
            session.close()
    
    def add_conversation_button(self, conversation):
        button = ConversationButton(conversation)
        button.selected.connect(self.select_conversation)
        button.delete_requested.connect(self.delete_conversation)
        button.rename_requested.connect(self.rename_conversation)
        button.archive_requested.connect(self.archive_conversation)
        
        self.conversations_layout.addWidget(button)
        self.conversation_buttons[conversation.conversation_id] = button
        
        if self.current_conversation and self.current_conversation.conversation_id == conversation.conversation_id:
            button.setChecked(True)
    
    def select_conversation(self, conversation):
        if self.current_conversation:
            if conversation.conversation_id == self.current_conversation.conversation_id:
                return
            
            if self.current_conversation.conversation_id in self.conversation_buttons:
                self.conversation_buttons[self.current_conversation.conversation_id].setChecked(False)
        
        self.current_conversation = conversation
        
        if conversation.conversation_id in self.conversation_buttons:
            self.conversation_buttons[conversation.conversation_id].setChecked(True)
        
        self.conversation_selected.emit(conversation)
    
    def create_new_conversation(self):
        if len(self.conversations) >= self.max_conversations:
            QMessageBox.warning(self, "Limit Aşıldı", f"Maksimum {self.max_conversations} sohbet kanalı oluşturabilirsiniz. Devam etmek için bazı sohbetleri arşivleyin veya silin.")
            return
        
        name, ok = QInputDialog.getText(self, "Yeni Sohbet", "Sohbet adı:")
        
        if ok and name:
            session = get_db_session()
            
            try:
                new_conversation = Conversation(
                    conversation_id=Conversation.generate_conversation_id(),
                    user_id=self.user.user_id,
                    name=name
                )
                
                session.add(new_conversation)
                session.commit()
                
                self.conversations.insert(0, new_conversation)
                self.add_conversation_button(new_conversation)
                
                self.select_conversation(new_conversation)
                
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Hata", f"Yeni sohbet oluşturulurken bir hata oluştu: {str(e)}")
            finally:
                session.close()
    
    def rename_conversation(self, conversation):
        name, ok = QInputDialog.getText(
            self, "Sohbeti Yeniden Adlandır", 
            "Yeni sohbet adı:", 
            text=conversation.name
        )
        
        if ok and name:
            session = get_db_session()
            
            try:
                db_conversation = session.query(Conversation).filter_by(
                    conversation_id=conversation.conversation_id
                ).first()
                
                if db_conversation:
                    db_conversation.name = name
                    session.commit()
                    
                    if conversation.conversation_id in self.conversation_buttons:
                        self.conversation_buttons[conversation.conversation_id].setText(name)
                    
                    if self.current_conversation and self.current_conversation.conversation_id == conversation.conversation_id:
                        self.current_conversation.name = name
                    
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Hata", f"Sohbet yeniden adlandırılırken bir hata oluştu: {str(e)}")
            finally:
                session.close()
    
    def delete_conversation(self, conversation):
        reply = QMessageBox.question(
            self, "Sohbeti Sil", 
            f"'{conversation.name}' sohbetini silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            
            try:
                db_conversation = session.query(Conversation).filter_by(
                    conversation_id=conversation.conversation_id
                ).first()
                
                if db_conversation:
                    session.delete(db_conversation)
                    session.commit()
                    
                    if conversation.conversation_id in self.conversation_buttons:
                        button = self.conversation_buttons[conversation.conversation_id]
                        
                        fade_out = AnimationUtils.fade_animation(button, 1.0, 0.0, 200)
                        fade_out.finished.connect(lambda: self.remove_button_after_animation(button, conversation.conversation_id))
                        fade_out.start()
                        
                    self.conversations = [c for c in self.conversations if c.conversation_id != conversation.conversation_id]
                    
                    if self.current_conversation and self.current_conversation.conversation_id == conversation.conversation_id:
                        if self.conversations:
                            self.select_conversation(self.conversations[0])
                        else:
                            self.current_conversation = None
                            self.conversation_selected.emit(None)
                    
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Hata", f"Sohbet silinirken bir hata oluştu: {str(e)}")
            finally:
                session.close()
    
    def remove_button_after_animation(self, button, conversation_id):
        self.conversations_layout.removeWidget(button)
        button.deleteLater()
        if conversation_id in self.conversation_buttons:
            del self.conversation_buttons[conversation_id]
    
    def archive_conversation(self, conversation):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Sohbeti Arşivle", 
            f"{conversation.name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Metin Dosyaları (*.txt)"
        )
        
        if not file_path:
            return
        
        session = get_db_session()
        
        try:
            messages = session.query(Message).filter_by(
                conversation_id=conversation.conversation_id
            ).order_by(Message.message_date).all()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Sohbet: {conversation.name}\n")
                f.write(f"Tarih: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for message in messages:
                    date_str = message.message_date.strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"[{date_str}] Kullanıcı: {message.message_content}\n")
                    if message.response_message:
                        f.write(f"[{date_str}] DinamikChat: {message.response_message}\n")
                    f.write("\n")
            
            db_conversation = session.query(Conversation).filter_by(
                conversation_id=conversation.conversation_id
            ).first()
            
            if db_conversation:
                db_conversation.is_archived = True
                session.commit()
                
                if conversation.conversation_id in self.conversation_buttons:
                    button = self.conversation_buttons[conversation.conversation_id]
                    fade_out = AnimationUtils.fade_animation(button, 1.0, 0.0, 300)
                    fade_out.finished.connect(lambda: self.remove_button_after_animation(button, conversation.conversation_id))
                    fade_out.start()
                
                self.conversations = [c for c in self.conversations if c.conversation_id != conversation.conversation_id]
                
                if self.current_conversation and self.current_conversation.conversation_id == conversation.conversation_id:
                    if self.conversations:
                        self.select_conversation(self.conversations[0])
                    else:
                        self.current_conversation = None
                        self.conversation_selected.emit(None)
                
                QMessageBox.information(self, "Başarılı", f"Sohbet başarıyla arşivlendi ve kaydedildi: {file_path}")
                
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Hata", f"Sohbet arşivlenirken bir hata oluştu: {str(e)}")
        finally:
            session.close()
    
    def toggle_panel_visibility(self):
        self.is_expanded = not self.is_expanded
        
        animation, is_expanding = AnimationUtils.panel_toggle_animation(
            self, 250, 50, 300,
            lambda: self.toggle_panel.emit(is_expanding)
        )
        
        animation.valueChanged.connect(
            lambda val: self.toggle_button.setText("◀" if val > 150 else "▶")
        )
        
        animation.start()

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.setFixedWidth(250)
            self.toggle_button.setIcon(QIcon("assets/icons/chevron_left.svg"))
            self.conversations_layout.setVisible(True)
            self.toggle_button.setVisible(True)
        else:
            self.setFixedWidth(50)
            self.toggle_button.setIcon(QIcon("assets/icons/chevron_right.svg"))
            self.conversations_layout.setVisible(False)
            self.toggle_button.setVisible(True)
        
        self.toggle_panel.emit(self.is_expanded)

    def update_theme(self, theme):

        self.theme = theme
        
        self.setStyleSheet(f"""
            ConversationPanel {{
                background-color: {self.theme['secondary']};
                border-right: 1px solid {self.theme['border']};
            }}
            
            QLabel {{
                color: {self.theme['foreground']};
            }}
            
            #panelTitle {{
                font-weight: bold;
                font-size: 16px;
                color: {self.theme['foreground']};
            }}
            
            #toggleButton, #newChatButton {{
                background-color: {self.theme['secondary']};
                border: none;
                border-radius: 15px;
            }}
            
            #toggleButton:hover, #newChatButton:hover {{
                background-color: {self.theme['hover']};
            }}
            
            QListWidget {{
                background-color: {self.theme['secondary']};
                border: none;
                color: {self.theme['foreground']};
                selection-background-color: {self.theme['accent']};
                selection-color: white;
            }}
            
            QListWidget::item {{
                padding: 8px;
                border-radius: 5px;
            }}
            
            QListWidget::item:hover {{
                background-color: {self.theme['hover']};
            }}
            
            QMenu {{
                background-color: {self.theme['secondary']};
                color: {self.theme['foreground']};
                border: 1px solid {self.theme['border']};
            }}
            
            QMenu::item:selected {{
                background-color: {self.theme['accent']};
                color: white;
            }}
        """) 