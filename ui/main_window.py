from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, QApplication, QMenu, QMessageBox, QToolButton, QCheckBox, QSplitter, QStackedWidget, QTextEdit, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QEvent, QByteArray, QRect
from PyQt6.QtGui import QIcon, QFont, QMovie, QAction, QPixmap, QKeySequence, QShortcut, QColor, QPalette, QPainter, QPainterPath, QPolygon

import json
import os
import datetime

from ui.chat_panel import ChatPanel
from ui.conversation_panel import ConversationPanel
from database import User, Message, Conversation, get_db_session
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

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        
        self.user = user
        
        with open('settings.json', 'r', encoding='utf-8') as f:
            self.settings = json.load(f)
        
        self.is_dark_theme = True
        self.current_theme = "dark"
        self.theme = self.settings['ui']['theme']['dark']
        self.light_theme = self.settings['ui']['theme']['light']
        self.app_name = self.settings['app_name']
        
        self.setWindowTitle(self.app_name)
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)
        
        self.current_conversation = None
        self.create_ui()
        self.setup_shortcuts()
        
        QTimer.singleShot(300, self.initialize_conversation)
    
    def create_ui(self):
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
        self.content_splitter.setHandleWidth(1)
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.setObjectName("contentSplitter")
        
        self.left_panel = QWidget()
        self.left_panel.setObjectName("leftPanel")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        self.conversation_panel = ConversationPanel(self.user)
        self.conversation_panel.conversation_selected.connect(self.load_conversation)
        
        left_layout.addWidget(self.conversation_panel)
        
        self.left_collapse_button = PanelCollapseButton("left")
        self.left_collapse_button.clicked.connect(self.toggle_left_panel)
        
        self.center_area = QWidget()
        self.center_area.setObjectName("centerArea")
        center_layout = QVBoxLayout(self.center_area)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        
        center_content = QHBoxLayout()
        center_content.setContentsMargins(0, 0, 0, 0)
        center_content.setSpacing(0)
        
        self.gif_player = GifPlayer()
        
        model_title = QLabel("Yapay Zeka Modeli")
        model_title.setObjectName("modelTitle")
        model_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        center_panel = QVBoxLayout()
        center_panel.addWidget(model_title)
        center_panel.addWidget(self.gif_player)
        
        center_layout.addLayout(center_panel)
        
        self.right_panel = QWidget()
        self.right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        self.chat_panel = ChatPanel()
        self.chat_panel.send_message.connect(self.handle_user_message)
        
        right_layout.addWidget(self.chat_panel)
        
        self.right_collapse_button = PanelCollapseButton("right")
        self.right_collapse_button.clicked.connect(self.toggle_right_panel)
        
        self.content_splitter.addWidget(self.left_panel)
        self.content_splitter.addWidget(self.center_area)
        self.content_splitter.addWidget(self.right_panel)
        
        content_layout.addWidget(self.content_splitter)
        
        self.content_splitter.setSizes([180, 450, 500])
        
        self.main_layout.addWidget(self.content_container)
        
        self.apply_styles()
        
        self.setCentralWidget(central_widget)
        
        self.installEventFilter(self)
    
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
        
        channel_container = QWidget()
        channel_layout = QHBoxLayout(channel_container)
        channel_layout.setContentsMargins(0, 0, 0, 0)
        channel_layout.setSpacing(5)
        channel_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.channels_cb = QCheckBox("Sohbet Kanalları")
        self.channels_cb.setObjectName("controlCheckbox")
        self.channels_cb.setChecked(True)
        self.channels_cb.stateChanged.connect(self.toggle_channels_panel)
        
        add_channel_btn = QPushButton()
        add_channel_btn.setObjectName("addChannelButton")
        add_channel_btn.setIcon(QIcon("assets/icons/add_icon.png"))
        add_channel_btn.setIconSize(QSize(14, 14))
        add_channel_btn.setFixedSize(24, 24)
        add_channel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_channel_btn.setToolTip("Yeni Kanal Ekle")
        add_channel_btn.clicked.connect(self.create_new_conversation)
        
        channel_layout.addWidget(self.channels_cb)
        channel_layout.addWidget(add_channel_btn)
        
        left_layout.addWidget(channel_container)
        
        center_panel = QFrame()
        center_layout = QHBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(16)
        
        self.admin_btn = MenuButton("ADMİN")
        self.admin_btn.clicked.connect(self.show_admin_menu)
        
        self.modes_widget = QStackedWidget()
        
        normal_widget = QWidget()
        normal_layout = QHBoxLayout(normal_widget)
        normal_layout.setContentsMargins(0, 0, 0, 0)
        normal_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.normal_btn = MenuButton("Normal", is_active=True)
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
            width_to_use = min(180, sizes[1] // 3)
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
    
    def setup_shortcuts(self):
        self.enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        self.enter_shortcut.activated.connect(self.send_message_shortcut)
        
        self.new_chat_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self.new_chat_shortcut.activated.connect(self.create_new_conversation)
        
        self.quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.quit_shortcut.activated.connect(self.close)
    
    def send_message_shortcut(self):
        if self.chat_panel.message_input.hasFocus():
            self.chat_panel.send_user_message()
    
    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress and source == self.chat_panel.message_input:
            if event.key() == Qt.Key.Key_Return:
                if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                    self.chat_panel.message_input.insertPlainText("\n")
                    return True
                elif event.modifiers() == Qt.KeyboardModifier.NoModifier:
                    self.chat_panel.send_user_message()
                    return True
        
        return super().eventFilter(source, event)
    
    def create_new_conversation(self):
        conversation_name = f"Yeni Sohbet {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
        new_conversation = self.conversation_panel.create_new_conversation(conversation_name)
        if new_conversation:
            self.conversation_panel.select_conversation(new_conversation)
    
    def show_modes_menu(self):
        modes_menu = CustomMenu(self, is_dark=self.is_dark_theme)
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
    
    def apply_styles(self):
        if self.is_dark_theme:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
    
    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            
            #topPanel {
                background-color: #252526;
                border-bottom: 1px solid #3E3E3E;
            }
            
            #controlCheckbox {
                color: #FFFFFF;
                spacing: 5px;
                padding: 3px;
                min-height: 40px;
                font-weight: bold;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #555555;
            }
            
            QCheckBox::indicator:unchecked {
                background-color: #3A3A3A;
            }
            
            QCheckBox::indicator:checked {
                background-color: #1E88E5;
                border: 1px solid #1E88E5;
            }
            
            #addChannelButton {
                background-color: #3A3A3A;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 2px;
            }
            
            #addChannelButton:hover {
                background-color: #1E88E5;
            }
            
            #addChannelButton:pressed {
                background-color: #1976D2;
            }
            
            #menuButton {
                background-color: #3A3A3A;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 15px;
                min-width: 150px;
                min-height: 36px;
                padding: 5px 15px;
                font-weight: bold;
                text-align: center;
            }
            
            #menuButton:hover {
                background-color: #4E4E4E;
            }
            
            #menuButton:pressed {
                background-color: #383838;
            }
            
            #activeMenuButton {
                background-color: #3A3A3A;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 15px;
                min-width: 150px;
                min-height: 36px;
                padding: 5px 15px;
                font-weight: bold;
                text-align: center;
            }
            
            #contentSplitter {
                background-color: #1E1E1E;
            }
            
            QSplitter::handle {
                background-color: #3E3E3E;
            }
            
            #leftPanel {
                background-color: #252526;
                border-right: 1px solid #3E3E3E;
            }
            
            #centerArea {
                background-color: #252526;
                border-right: 1px solid #3E3E3E;
            }
            
            #rightPanel {
                background-color: #252526;
            }
            
            #gifPlayer {
                background-color: #1E1E1E;
                border-radius: 10px;
                margin: 10px;
            }
            
            #customMenu {
                background-color: transparent;
                border: none;
                padding: 8px;
            }
            
            #customMenu::item {
                background-color: transparent;
                color: #FFFFFF;
                padding: 8px 20px;
                border-radius: 8px;
                margin: 2px 5px;
                font-weight: bold;
            }
            
            #customMenu::item:selected {
                background-color: #1E88E5;
            }
            
            #customMenu::item:checked {
                background-color: #1976D2;
            }
            
            #collapseButton {
                background-color: transparent;
                border: none;
            }
            
            #modelTitle {
                color: #AAAAAA;
                font-size: 12px;
                padding: 8px;
                font-weight: bold;
            }
            
            QMessageBox {
                background-color: #252526;
            }
            
            QPushButton {
                background-color: #3A3A3A;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
            }
            
            QPushButton:hover {
                background-color: #4E4E4E;
            }
            
            QPushButton:pressed {
                background-color: #383838;
            }
            
            QScrollBar:vertical {
                background: #1E1E1E;
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background: #3A3A3A;
                min-height: 30px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #1E88E5;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
    
    def apply_light_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #F5F5F5;
                color: #333333;
            }
            
            #topPanel {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E0E0E0;
            }
            
            #controlCheckbox {
                color: #333333;
                spacing: 5px;
                padding: 3px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #BDBDBD;
            }
            
            QCheckBox::indicator:unchecked {
                background-color: #FFFFFF;
            }
            
            QCheckBox::indicator:checked {
                background-color: #1976D2;
                border: 1px solid #1976D2;
            }
            
            #addChannelButton {
                background-color: #E0E0E0;
                color: #333333;
                border: none;
                border-radius: 12px;
                padding: 2px;
            }
            
            #addChannelButton:hover {
                background-color: #1E88E5;
                color: #FFFFFF;
            }
            
            #addChannelButton:pressed {
                background-color: #1976D2;
                color: #FFFFFF;
            }
            
            #menuButton {
                background-color: #E0E0E0;
                color: #333333;
                border: 1px solid #BDBDBD;
                border-radius: 15px;
                min-width: 150px;
                min-height: 32px;
                padding: 5px 15px;
                font-weight: bold;
                text-align: center;
            }
            
            #menuButton:hover {
                background-color: #EEEEEE;
            }
            
            #menuButton:pressed {
                background-color: #BDBDBD;
            }
            
            #activeMenuButton {
                background-color: #E0E0E0;
                color: #333333;
                border: 1px solid #BDBDBD;
                border-radius: 15px;
                min-width: 150px;
                min-height: 32px;
                padding: 5px 15px;
                font-weight: bold;
                text-align: center;
            }
            
            #contentSplitter {
                background-color: #F5F5F5;
            }
            
            QSplitter::handle {
                background-color: #E0E0E0;
            }
            
            #leftPanel {
                background-color: #FFFFFF;
                border-right: 1px solid #E0E0E0;
            }
            
            #centerArea {
                background-color: #FFFFFF;
                border-right: 1px solid #E0E0E0;
            }
            
            #rightPanel {
                background-color: #FFFFFF;
            }
            
            #gifPlayer {
                background-color: #F5F5F5;
                border-radius: 10px;
            }
            
            #customMenu {
                background-color: transparent;
                border: none;
                padding: 8px;
            }
            
            #customMenu::item {
                background-color: transparent;
                color: #333333;
                padding: 8px 20px;
                border-radius: 8px;
                margin: 2px 5px;
                font-weight: bold;
            }
            
            #customMenu::item:selected {
                background-color: #1E88E5;
                color: #FFFFFF;
            }
            
            #customMenu::item:checked {
                background-color: #1976D2;
                color: #FFFFFF;
            }
            
            #collapseButton {
                background-color: transparent;
                border: none;
            }
            
            #modelTitle {
                color: #757575;
                font-size: 12px;
                padding: 5px;
            }
            
            QMessageBox {
                background-color: #FFFFFF;
            }
            
            QPushButton {
                background-color: #E0E0E0;
                color: #333333;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
            }
            
            QPushButton:hover {
                background-color: #EEEEEE;
            }
            
            QPushButton:pressed {
                background-color: #BDBDBD;
            }
            
            QScrollBar:vertical {
                background: #F5F5F5;
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background: #BDBDBD;
                min-height: 30px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #1976D2;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
    
    def show_admin_menu(self):
        admin_menu = CustomMenu(self, is_dark=self.is_dark_theme)
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
        koyu_tema.setChecked(self.is_dark_theme)
        
        acik_tema = QAction("Açık Tema", tema_menu)
        acik_tema.setCheckable(True)
        acik_tema.setChecked(not self.is_dark_theme)
        
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
            self.is_dark_theme = True
            self.current_theme = "dark"
            self.theme = self.settings['ui']['theme']['dark']
            self.apply_dark_theme()
            self.chat_panel.update_theme(self.theme)
        elif action == acik_tema:
            self.is_dark_theme = False
            self.current_theme = "light"
            self.theme = self.settings['ui']['theme']['light']
            self.apply_light_theme()
            self.chat_panel.update_theme(self.theme)
    
    def toggle_channels_panel(self, state):
        self.left_panel.setVisible(state)
        if state:
            sizes = self.content_splitter.sizes()
            if sizes[0] < 100:
                sizes[0] = 180
                sizes[1] -= 90
                sizes[2] -= 90
                self.content_splitter.setSizes(sizes)
        else:
            sizes = self.content_splitter.sizes()
            sizes[1] += sizes[0] // 2
            sizes[2] += sizes[0] // 2
            sizes[0] = 0
            self.content_splitter.setSizes(sizes)
    
    def show_settings(self):
        QMessageBox.information(self, "Ayarlar", "Ayarlar sayfası henüz mevcut değil.")
    
    def logout(self):
        reply = QMessageBox.question(
            self, "Oturumu Kapat", "Oturumu kapatmak istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QApplication.quit()
    
    def initialize_conversation(self):
        session = get_db_session()
        conversations = session.query(Conversation).filter(Conversation.user_id == self.user.user_id).all()
        session.close()
        
        if conversations:
            self.conversation_panel.select_conversation(conversations[0])
        else:
            self.create_new_conversation()
    
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
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Çıkış", "Uygulamadan çıkmak istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore() 