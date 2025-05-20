from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, QApplication, QMenu, QMessageBox, QToolButton, QCheckBox, QSplitter, QStackedWidget, QTextEdit, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect, QProgressBar, QLineEdit, QListWidget, QListWidgetItem, QComboBox
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QEvent, QByteArray, QRect, QSettings
from PyQt6.QtGui import QIcon, QFont, QMovie, QAction, QPixmap, QKeySequence, QShortcut, QColor, QPalette, QPainter, QPainterPath, QPolygon, QLinearGradient, QBrush, QPen, QImage, QFontDatabase, QCursor

import json
import os
import datetime
import tempfile

from ui.chat_panel import ChatPanel
from ui.conversation_panel import ConversationPanel
from database import User, Message, Conversation, get_db_session, Database
from utils.openai_utils import chatgpt_manager

class PanelCollapseButton(QPushButton):
    def __init__(self, direction, parent=None):
        super().__init__(parent)
        self.direction = direction
        self.is_collapsed = False
        self.setFixedSize(20, 60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("collapseButton")
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.underMouse():
            painter.setBrush(QColor(80, 80, 80, 200))
        else:
            painter.setBrush(QColor(70, 70, 70, 180))
        
        painter.setPen(Qt.PenStyle.NoPen)
        
        triangle_width = 10
        triangle_height = 14
        
        x = (self.width() - triangle_width) // 2
        y = (self.height() - triangle_height) // 2
        
        if self.direction == "left":
            if self.is_collapsed:
                points = [
                    QPoint(x + triangle_width, y),
                    QPoint(x, y + triangle_height // 2),
                    QPoint(x + triangle_width, y + triangle_height)
                ]
            else:
                points = [
                    QPoint(x, y),
                    QPoint(x + triangle_width, y + triangle_height // 2),
                    QPoint(x, y + triangle_height)
                ]
        else:
            if self.is_collapsed:
                points = [
                    QPoint(x, y),
                    QPoint(x + triangle_width, y + triangle_height // 2),
                    QPoint(x, y + triangle_height)
                ]
            else:
                points = [
                    QPoint(x + triangle_width, y),
                    QPoint(x, y + triangle_height // 2),
                    QPoint(x + triangle_width, y + triangle_height)
                ]
        
        path = QPainterPath()
        polygon = QPolygon(points)
        path.addPolygon(polygon)
        painter.fillPath(path, QColor("#FFFFFF"))

class CustomMenu(QMenu):
    def __init__(self, parent=None, is_dark=True):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("customMenu")
        self.is_dark = is_dark
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.is_dark:
            background = QColor(45, 45, 45, 245)
            border = QColor(70, 70, 70)
        else:
            background = QColor(245, 245, 245, 245)
            border = QColor(220, 220, 220)
        
        painter.setPen(border)
        painter.setBrush(background)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)

class MenuButton(QPushButton):
    def __init__(self, text, parent=None, is_active=False):
        super().__init__(text, parent)
        self.is_active = is_active
        self.setObjectName("menuButton")
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if is_active:
            self.setObjectName("activeMenuButton")
            
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self.is_active:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            width = self.width()
            height = self.height()
            triangle_width = 8
            triangle_height = 4
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255))
            
            x = width - 20
            y = (height - triangle_height) // 2
            
            points = [
                QPoint(x, y + triangle_height),
                QPoint(x + triangle_width // 2, y),
                QPoint(x + triangle_width, y + triangle_height)
            ]
            
            painter.drawPolygon(points)

class GifPlayer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setObjectName("gifPlayer")
        
        self.movie = QMovie("assets/animations/ai_animation.gif")
        self.setMovie(self.movie)
        self.movie.start()
    
    def resizeEvent(self, event):
        self.movie.setScaledSize(QSize(int(self.width() * 0.8), int(self.height() * 0.8)))
        super().resizeEvent(event)

class GradientWaveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
        self.phase = 0
    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0, QColor(30, 40, 60))
        grad.setColorAt(1, QColor(20, 30, 50))
        painter.fillRect(rect, QBrush(grad))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color1 = QColor(0, 120, 255, 80)
        color2 = QColor(0, 200, 255, 60)
        w, h = rect.width(), rect.height()
        for i in range(3):
            path = QPainter.Path()
            amp = 30 + i*10
            freq = 2 + i
            phase = self.phase + i*30
            path.moveTo(0, h//2)
            for x in range(0, w+1, 5):
                y = h//2 + amp * (0.5*i+1) * __import__('math').sin((x+phase)/w*3.14*freq)
                path.lineTo(x, y)
            painter.setPen(QColor(color1 if i%2==0 else color2))
            painter.drawPath(path)
        self.phase += 4

class TemaYoneticisi:
    def __init__(self):
        self.ayarlar = QSettings("AiChatApp", "TemaAyarlari")
        self.temalar = {
            "acik": {
                "arka_plan": "#FFFFFF",
                "panel": "#FFFFFF",
                "panel_sekonder": "#F8F8F8",
                "buton": "#F5F5F5",
                "buton_hover": "#E8E8E8",
                "buton_pressed": "#D8D8D8",
                "buton_aktif": "#0078D4",
                "vurgu": "#0078D4",
                "vurgu_hover": "#006CBE",
                "vurgu_pressed": "#0060A8",
                "metin": "#000000",
                "metin_ikincil": "#444444",
                "kenar": "#E0E0E0",
                "hata": "#D83B01",
                "basari": "#107C10",
                "kullanici_mesaj": "#E7F5FF",
                "yapay_zeka_mesaj": "#F8F8F8",
                "golge": "rgba(0, 0, 0, 0.05)"
            },
            "koyu": {
                "arka_plan": "#121212",
                "panel": "#1E1E1E",
                "panel_sekonder": "#252525",
                "buton": "#2D2D2D",
                "buton_hover": "#3E3E3E",
                "buton_pressed": "#4E4E4E",
                "buton_aktif": "#60CDFF",
                "vurgu": "#60CDFF",
                "vurgu_hover": "#4DBFFF",
                "vurgu_pressed": "#3AB0FF",
                "metin": "#FFFFFF",
                "metin_ikincil": "#AAAAAA",
                "kenar": "#333333",
                "hata": "#F85858",
                "basari": "#6CCB5F",
                "kullanici_mesaj": "#1F2B3E",
                "yapay_zeka_mesaj": "#252525",
                "golge": "rgba(0, 0, 0, 0.3)"
            }
        }
        
        try:
            with open("ayarlar.json", "r", encoding="utf-8") as f:
                ayarlar = json.load(f)
                varsayilan_tema = ayarlar.get("sistem", {}).get("tema", "koyu")
                self.aktif_tema = self.ayarlar.value("tema", varsayilan_tema)
        except Exception:
            self.aktif_tema = "koyu"
    
    def tema_degistir(self, tema_adi):
        if tema_adi in self.temalar:
            self.aktif_tema = tema_adi
            self.ayarlar.setValue("tema", tema_adi)
            return True
        return False
    
    def renkleri_al(self):
        return self.temalar[self.aktif_tema]
    
    def css_degiskenler(self):
        renkler = self.renkleri_al()
        css = f"""
            * {{
                font-family: 'Segoe UI', sans-serif;
            }}
            
            #AnaForm {{
                background-color: {renkler['arka_plan']};
                color: {renkler['metin']};
            }}
            
            QWidget {{
                background-color: transparent;
                color: {renkler['metin']};
            }}
            
            QFrame#icerikAlani {{
                background-color: {renkler['panel']};
                border-radius: 12px;
                border: 1px solid {renkler['kenar']};
            }}
            
            QLineEdit, QTextEdit {{
                background-color: {renkler['panel_sekonder']};
                color: {renkler['metin']};
                border: 1px solid {renkler['kenar']};
                border-radius: 8px;
                padding: 8px;
                selection-background-color: {renkler['vurgu']};
                selection-color: white;
            }}
            
            QPushButton {{
                background-color: {renkler['buton']};
                color: {renkler['metin']};
                border: 1px solid {renkler['kenar']};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {renkler['buton_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {renkler['vurgu']};
                color: white;
            }}
            
            QPushButton:checked {{
                background-color: {renkler['vurgu']};
                color: white;
                font-weight: bold;
            }}
            
            QToolButton {{
                background-color: {renkler['buton']};
                border: 1px solid {renkler['kenar']};
                border-radius: 8px;
                padding: 3px;
            }}
            
            QToolButton:hover {{
                background-color: {renkler['buton_hover']};
            }}
            
            QToolButton:pressed {{
                background-color: {renkler['vurgu']};
            }}
            
            QScrollArea, QScrollBar {{
                background-color: transparent;
                border: none;
            }}
            
            QScrollBar:vertical {{
                background-color: transparent;
                width: 14px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {renkler['buton']};
                min-height: 20px;
                border-radius: 7px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {renkler['buton_hover']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background-color: transparent;
                height: 0px;
                width: 0px;
            }}
            
            QMenu {{
                background-color: {renkler['panel']};
                border: 1px solid {renkler['kenar']};
                border-radius: 8px;
                padding: 5px;
            }}
            
            QMenu::item {{
                background-color: transparent;
                padding: 6px 25px 6px 20px;
                border-radius: 4px;
                margin: 2px;
            }}
            
            QMenu::item:selected {{
                background-color: {renkler['buton_hover']};
            }}
            
            QMenu::separator {{
                height: 1px;
                background-color: {renkler['kenar']};
                margin: 5px 10px;
            }}
            
            QLabel {{
                color: {renkler['metin']};
            }}
            
            QMessageBox {{
                background-color: {renkler['panel']};
            }}
            
            QMessageBox QPushButton {{
                min-width: 80px;
                min-height: 30px;
            }}
            
            QSplitter::handle {{
                background-color: {renkler['kenar']};
            }}
            
            QSplitter::handle:horizontal {{
                width: 1px;
            }}
            
            QSplitter::handle:vertical {{
                height: 1px;
            }}
            
            QToolTip {{
                background-color: {renkler['panel']};
                color: {renkler['metin']};
                border: 1px solid {renkler['kenar']};
                border-radius: 4px;
                padding: 5px;
            }}
        """
        return css

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.db = Database()
        self.tema_yoneticisi = TemaYoneticisi()
        self.setWindowTitle("DinamikChat")
        self.setMinimumSize(1200, 800)
        self.setObjectName("AnaForm")
        
        self.init_ui()
        self.tema_uygula()
    
    def tema_uygula(self):
        self.setStyleSheet(self.tema_yoneticisi.css_degiskenler())
    
    def tema_degistir(self):
        yeni_tema = "acik" if self.tema_yoneticisi.aktif_tema == "koyu" else "koyu"
        if self.tema_yoneticisi.tema_degistir(yeni_tema):
            self.tema_uygula()
    
    def init_ui(self):
        central_widget = QWidget()
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.create_top_panel()
        
        self.content_container = QWidget()
        content_layout = QHBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setHandleWidth(2)
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.setObjectName("contentSplitter")
        
        self.left_panel = QWidget()
        self.left_panel.setObjectName("leftPanel")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        self.conversation_panel = ConversationPanel(self, self.tema_yoneticisi)
        self.conversation_panel.konusma_secildi.connect(self.load_conversation)
        left_layout.addWidget(self.conversation_panel)
        
        self.left_collapse_button = PanelCollapseButton("left")
        self.left_collapse_button.clicked.connect(self.toggle_left_panel)
        
        self.center_area = QWidget()
        self.center_area.setObjectName("centerArea")
        center_layout = QVBoxLayout(self.center_area)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        
        self.gif_player = GifPlayer()
        model_title = QLabel("Yapay Zeka Modeli")
        model_title.setObjectName("modelTitle")
        model_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        center_panel = QVBoxLayout()
        center_panel.setContentsMargins(0, 0, 0, 0)
        center_panel.setSpacing(20)
        center_panel.addWidget(model_title)
        center_panel.addWidget(self.gif_player, alignment=Qt.AlignmentFlag.AlignCenter)
        center_layout.addLayout(center_panel)
        
        self.right_panel = QWidget()
        self.right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        self.chat_panel = ChatPanel(self, self.tema_yoneticisi)
        self.chat_panel.mesaj_gonderildi.connect(self.handle_user_message)
        self.chat_panel.ses_kaydi_bitti.connect(self.handle_voice_recording)
        right_layout.addWidget(self.chat_panel)
        
        self.right_collapse_button = PanelCollapseButton("right")
        self.right_collapse_button.clicked.connect(self.toggle_right_panel)
        
        self.content_splitter.addWidget(self.left_panel)
        self.content_splitter.addWidget(self.center_area)
        self.content_splitter.addWidget(self.right_panel)
        
        content_layout.addWidget(self.content_splitter)
        self.content_splitter.setSizes([220, 500, 500])
        
        self.main_layout.addWidget(self.content_container)
        self.setCentralWidget(central_widget)
    
    def create_top_panel(self):
        self.top_panel = QFrame()
        self.top_panel.setObjectName("topPanel")
        self.top_panel.setFixedHeight(60)
        
        top_layout = QHBoxLayout(self.top_panel)
        top_layout.setContentsMargins(15, 5, 15, 5)
        
        left_panel = QFrame()
        left_layout = QHBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        add_channel_btn = QPushButton()
        add_channel_btn.setObjectName("addChannelButton")
        add_channel_btn.setText("+")
        add_channel_btn.setFixedSize(40, 40)
        add_channel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_channel_btn.setToolTip("Yeni Kanal Ekle")
        add_channel_btn.clicked.connect(self.create_new_conversation)
        left_layout.addWidget(add_channel_btn)
        
        center_panel = QFrame()
        center_layout = QHBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(16)
        
        self.admin_btn = MenuButton("ADMİN")
        self.admin_btn.setFixedHeight(36)
        self.admin_btn.setFixedWidth(100)
        self.admin_btn.clicked.connect(self.show_admin_menu)
        
        self.modes_widget = QStackedWidget()
        normal_widget = QWidget()
        normal_layout = QHBoxLayout(normal_widget)
        normal_layout.setContentsMargins(0, 0, 0, 0)
        normal_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.normal_btn = MenuButton("Normal", is_active=True)
        self.normal_btn.setFixedHeight(36)
        self.normal_btn.setFixedWidth(100)
        self.normal_btn.clicked.connect(self.show_modes_menu)
        normal_layout.addWidget(self.normal_btn)
        
        self.modes_widget.addWidget(normal_widget)
        
        center_layout.addWidget(self.admin_btn)
        center_layout.addWidget(self.modes_widget)
        
        right_panel = QFrame()
        right_layout = QHBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(20)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.thinking_cb = QCheckBox("Detaylı\nDüşünme")
        self.thinking_cb.setObjectName("controlCheckbox")
        
        self.web_search_cb = QCheckBox("Web\nArama")
        self.web_search_cb.setObjectName("controlCheckbox")
        
        right_layout.addWidget(self.thinking_cb)
        right_layout.addWidget(self.web_search_cb)
        
        top_layout.addWidget(left_panel)
        top_layout.addWidget(center_panel)
        top_layout.addWidget(right_panel)
        
        self.main_layout.addWidget(self.top_panel)
    
    def toggle_left_panel(self):
        self.left_collapse_button.is_collapsed = not self.left_collapse_button.is_collapsed
        sizes = self.content_splitter.sizes()
        
        if self.left_collapse_button.is_collapsed:
            self.old_left_size = sizes[0]
            sizes[1] += sizes[0]
            sizes[0] = 0
        else:
            width_to_use = min(220, sizes[1] // 3)
            sizes[1] -= width_to_use
            sizes[0] = width_to_use
        
        self.content_splitter.setSizes(sizes)
    
    def toggle_right_panel(self):
        self.right_collapse_button.is_collapsed = not self.right_collapse_button.is_collapsed
        sizes = self.content_splitter.sizes()
        
        if self.right_collapse_button.is_collapsed:
            self.old_right_size = sizes[2]
            sizes[1] += sizes[2]
            sizes[2] = 0
        else:
            width_to_use = min(350, sizes[1] // 2)
            sizes[1] -= width_to_use
            sizes[2] = width_to_use
        
        self.content_splitter.setSizes(sizes)
    
    def show_modes_menu(self):
        modes_menu = CustomMenu(self, is_dark=self.tema_yoneticisi.aktif_tema == "koyu")
        modes_menu.setObjectName("customMenu")
        modes_menu.setMinimumWidth(200)
        
        normal_action = QAction("Normal", modes_menu)
        normal_action.setCheckable(True)
        normal_action.setChecked(True)
        modes_menu.addAction(normal_action)
        
        edebi_action = QAction("Edebi", modes_menu)
        edebi_action.setCheckable(True)
        modes_menu.addAction(edebi_action)
        
        ogretici_action = QAction("Öğretici", modes_menu)
        ogretici_action.setCheckable(True)
        modes_menu.addAction(ogretici_action)
        
        uzman_action = QAction("Uzman", modes_menu)
        uzman_action.setCheckable(True)
        modes_menu.addAction(uzman_action)
        
        teknik_action = QAction("Teknik", modes_menu)
        teknik_action.setCheckable(True)
        modes_menu.addAction(teknik_action)
        
        pos = self.normal_btn.mapToGlobal(QPoint(0, self.normal_btn.height()))
        action = modes_menu.exec(pos)
        
        if action:
            self.normal_btn.setText(action.text())
    
    def show_admin_menu(self):
        admin_menu = CustomMenu(self, is_dark=self.tema_yoneticisi.aktif_tema == "koyu")
        admin_menu.setObjectName("customMenu")
        admin_menu.setMinimumWidth(200)
        
        oturum_kapat = QAction("Oturumu Kapat", admin_menu)
        admin_menu.addAction(oturum_kapat)
        
        ayarlar = QAction("Ayarlar", admin_menu)
        admin_menu.addAction(ayarlar)
        
        admin_menu.addSeparator()
        
        tema_menu = QMenu("Tema", admin_menu)
        tema_menu.setObjectName("customMenu")
        
        koyu_tema = QAction("Koyu Tema", tema_menu)
        koyu_tema.setCheckable(True)
        koyu_tema.setChecked(self.tema_yoneticisi.aktif_tema == "koyu")
        
        acik_tema = QAction("Açık Tema", tema_menu)
        acik_tema.setCheckable(True)
        acik_tema.setChecked(self.tema_yoneticisi.aktif_tema == "acik")
        
        tema_menu.addAction(koyu_tema)
        tema_menu.addAction(acik_tema)
        admin_menu.addMenu(tema_menu)
        
        pos = self.admin_btn.mapToGlobal(QPoint(0, self.admin_btn.height()))
        action = admin_menu.exec(pos)
        
        if action == oturum_kapat:
            self.logout()
        elif action == ayarlar:
            self.show_settings()
        elif action == koyu_tema:
            self.tema_yoneticisi.tema_degistir("koyu")
            self.tema_uygula()
        elif action == acik_tema:
            self.tema_yoneticisi.tema_degistir("acik")
            self.tema_uygula()
    
    def show_settings(self):
        QMessageBox.information(self, "Ayarlar", "Ayarlar sayfası henüz mevcut değil.")
    
    def logout(self):
        reply = QMessageBox.question(
            self, "Oturumu Kapat", "Oturumu kapatmak istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QApplication.quit()
    
    def create_new_conversation(self):
        conversation_name = f"Yeni Sohbet {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
        new_conversation = self.conversation_panel.create_new_conversation(conversation_name)
        if new_conversation:
            self.conversation_panel.select_conversation(new_conversation)
    
    def load_conversation(self, conversation):
        if conversation is None:
            return
        
        self.current_conversation = conversation
        
        session = get_db_session()
        messages = session.query(Message).filter(Message.conversation_id == conversation.conversation_id).order_by(Message.message_date).all()
        self.chat_panel.clear_messages()
        
        for message in messages:
            self.chat_panel.add_user_message(message.message_content)
            if message.response_message:
                self.chat_panel.add_ai_message(message.response_message)
        
        session.close()
        self.chat_panel.scroll_to_bottom()
    
    def handle_user_message(self, message):
        if not message.strip():
            return
            
        self.chat_panel.add_user_message(message)
        
        if not self.current_conversation:
            conversation_name = f"Yeni Sohbet {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
            self.current_conversation = self.conversation_panel.create_new_conversation(conversation_name)
            if not self.current_conversation:
                return
        
        session = get_db_session()
        new_message = Message(
            message_id=Message.generate_message_id(),
            conversation_id=self.current_conversation.conversation_id,
            message_content=message
        )
        
        session.add(new_message)
        session.commit()
        
        self.get_ai_response(new_message)
        session.close()
    
    def get_ai_response(self, message):
        def handle_response(response):
            self.chat_panel.add_ai_message(response)
            
            session = get_db_session()
            db_message = session.query(Message).filter_by(message_id=message.message_id).first()
            if db_message:
                db_message.response_message = response
                session.commit()
            session.close()
        
        chatgpt_manager.get_response(message.message_content, handle_response)
    
    def handle_voice_recording(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return
            
        self.chat_panel.add_user_message("[Sesli Mesaj]")
        
        if not self.current_conversation:
            conversation_name = f"Yeni Sohbet {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
            self.current_conversation = self.conversation_panel.create_new_conversation(conversation_name)
            if not self.current_conversation:
                return
        
        session = get_db_session()
        new_message = Message(
            message_id=Message.generate_message_id(),
            conversation_id=self.current_conversation.conversation_id,
            message_content="[Sesli Mesaj]"
        )
        
        session.add(new_message)
        session.commit()
        
        QMessageBox.information(self, "Ses Kaydı", "Ses kaydı alındı. (Bu özellik henüz tam olarak çalışmıyor)")
        
        response = "Sesli mesaj özelliği şu anda geliştirme aşamasındadır. Yakında sesli mesajlar da anlaşılacak."
        self.chat_panel.add_ai_message(response)
        
        db_message = session.query(Message).filter_by(message_id=new_message.message_id).first()
        if db_message:
            db_message.response_message = response
            session.commit()
        
        session.close()
        
        try:
            os.remove(file_path)
        except:
            pass
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Çıkış", "Uygulamadan çıkmak istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore() 