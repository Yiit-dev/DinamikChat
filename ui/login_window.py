from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QStackedWidget, QMessageBox, QFrame, QProgressBar
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QRect, pyqtProperty
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor, QPainter, QRadialGradient, QBrush, QLinearGradient, QPainterPath
import json
import os
import math
import random
import time
import sys
import bcrypt
import logging
from database import User, get_db_session
from utils.email_utils import email_manager
from utils.animation_utils import AnimatableWidget
import validators
from database.models import UserManager, initialize_database

class AnimatedLogo(AnimatableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        self._logo_size = 160
        self._opacity = 0.0
        self._rotation = 0.0
        self._ring_rotation = [0.0, 0.0, 0.0]
        self._pulse_factor = 0.0
        self._hologram_factor = 0.0
        self._hologram_shift = 0.0
        self._grid_offset = 0.0
        
        self.start_wave_animation(3000)
        self.start_intro_animation()
        self.start_rotation_animation()
        self.start_pulse_animation()
        self.start_hologram_animation()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        pulse = 1.0 + 0.05 * abs(math.sin(self._pulse_factor * math.pi))
        
        if self._hologram_factor > 0.1:
            outer_glow = QRadialGradient(center_x, center_y, self._logo_size * 1.5)
            outer_glow.setColorAt(0, QColor(0, 180, 255, int(20 * self._opacity * self._hologram_factor)))
            outer_glow.setColorAt(0.5, QColor(0, 120, 200, int(10 * self._opacity * self._hologram_factor)))
            outer_glow.setColorAt(1, QColor(0, 60, 120, 0))
            
            painter.setBrush(QBrush(outer_glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(center_x - self._logo_size * 1.5), int(center_y - self._logo_size * 1.5), 
                               int(self._logo_size * 3), int(self._logo_size * 3))
            
            inner_glow = QRadialGradient(center_x, center_y, self._logo_size * 0.8)
            inner_glow.setColorAt(0, QColor(50, 200, 255, int(40 * self._opacity * self._hologram_factor)))
            inner_glow.setColorAt(1, QColor(0, 100, 200, 0))
            
            painter.setBrush(QBrush(inner_glow))
            painter.drawEllipse(int(center_x - self._logo_size * 0.8), int(center_y - self._logo_size * 0.8), 
                               int(self._logo_size * 1.6), int(self._logo_size * 1.6))
            
            if self._hologram_factor > 0.3:
                grid_color = QColor(0, 200, 255, int(50 * self._opacity * self._hologram_factor))
                painter.setPen(grid_color)
                
                grid_size = 15
                grid_area = int(self._logo_size * 1.2)
                grid_start_x = int(center_x - grid_area / 2)
                grid_start_y = int(center_y - grid_area / 2)
                
                offset_x = int(self._grid_offset * 10) % grid_size
                offset_y = int(self._grid_offset * 7) % grid_size
                
                for y in range(grid_start_y + offset_y, grid_start_y + grid_area, grid_size):
                    line_opacity = 0.3 + 0.7 * abs(math.sin((y * 0.05 + self._hologram_shift) * math.pi))
                    painter.setPen(QColor(0, 200, 255, int(40 * self._opacity * line_opacity * self._hologram_factor)))
                    painter.drawLine(grid_start_x, y, grid_start_x + grid_area, y)
                
                for x in range(grid_start_x + offset_x, grid_start_x + grid_area, grid_size):
                    line_opacity = 0.3 + 0.7 * abs(math.sin((x * 0.05 + self._hologram_shift) * math.pi))
                    painter.setPen(QColor(0, 200, 255, int(40 * self._opacity * line_opacity * self._hologram_factor)))
                    painter.drawLine(x, grid_start_y, x, grid_start_y + grid_area)
                
                persp_color = QColor(50, 220, 255, int(30 * self._opacity * self._hologram_factor))
                painter.setPen(persp_color)
                
                for i in range(-5, 6, 2):
                    start_x = grid_start_x
                    start_y = grid_start_y + grid_area // 2 + i * (grid_area // 10)
                    end_x = grid_start_x + grid_area
                    end_y = grid_start_y + grid_area // 2 - i * (grid_area // 10)
                    painter.drawLine(start_x, start_y, end_x, end_y)
        
        gradient = QRadialGradient(center_x, center_y, self._logo_size / 1.5)
        gradient.setColorAt(0, QColor(0, 170, 255, int(200 * self._opacity)))
        gradient.setColorAt(0.5, QColor(0, 100, 200, int(150 * self._opacity)))
        gradient.setColorAt(1, QColor(0, 60, 120, int(100 * self._opacity)))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        
        size = int(self._logo_size * pulse * (0.9 + 0.1 * self.glow_intensity))
        rect = QRect(int(center_x - size/2), int(center_y - size/2), size, size)
        painter.drawEllipse(rect)
        
        inner_size = int(size * 0.8)
        glow_intensity = 0.5 + 0.5 * self.glow_intensity
        inner_rect = QRect(int(center_x - inner_size/2), int(center_y - inner_size/2), inner_size, inner_size)
        painter.setPen(QColor(255, 255, 255, int(100 * self._opacity * glow_intensity)))
        painter.drawEllipse(inner_rect)
        
        rotation_speeds = [1.0, 1.5, 0.7]
        ring_colors = [
            QColor(0, 200, 255, int(70 * self._opacity * (0.8 + 0.2 * self.glow_intensity))),
            QColor(0, 170, 255, int(80 * self._opacity * (0.8 + 0.2 * self.glow_intensity))),
            QColor(100, 200, 255, int(60 * self._opacity * (0.8 + 0.2 * self.glow_intensity)))
        ]
        
        for i in range(3):
            angle = self._ring_rotation[i] + self.wave_factor * 5 * rotation_speeds[i]
            
            painter.save()
            painter.translate(int(center_x), int(center_y))
            painter.rotate(angle)
            
            ellipse_width = int(size * (1.2 + i * 0.1) * pulse)
            ellipse_height = int(size * (0.3 + i * 0.05) * pulse)
            
            painter.setPen(ring_colors[i])
            
            ring_rect = QRect(-ellipse_width//2, -ellipse_height//2, ellipse_width, ellipse_height)
            painter.drawEllipse(ring_rect)
            painter.restore()
        
        center_glow = QRadialGradient(center_x, center_y, size/5)
        glow_color = QColor(50, 170, 255, int(100 * self._opacity * glow_intensity))
        center_glow.setColorAt(0, glow_color)
        center_glow.setColorAt(1, QColor(50, 150, 255, 0))
        
        painter.setBrush(QBrush(center_glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRect(int(center_x - size/4), int(center_y - size/4), int(size/2), int(size/2)))
        
        painter.setFont(QFont("Arial", int(size/2.5), QFont.Weight.Bold))
        
        shadow_color = QColor(0, 50, 120, int(150 * self._opacity))
        painter.setPen(shadow_color)
        shadow_rect = QRect(int(center_x - size/2) + 2, int(center_y - size/2) + 2, size, size)
        painter.drawText(shadow_rect, Qt.AlignmentFlag.AlignCenter, "D")
        
        text_color = QColor(255, 255, 255, int(255 * self._opacity))
        
        if self._hologram_factor > 0.3:
            red_offset = self._hologram_factor * 3.0
            
            red_rect = QRect(int(center_x - size/2 - red_offset), 
                            int(center_y - size/2), size, size)
            painter.setPen(QColor(255, 50, 50, int(180 * self._opacity * self._hologram_factor)))
            painter.drawText(red_rect, Qt.AlignmentFlag.AlignCenter, "D")
            
            blue_rect = QRect(int(center_x - size/2 + red_offset), 
                            int(center_y - size/2), size, size)
            painter.setPen(QColor(50, 50, 255, int(180 * self._opacity * self._hologram_factor)))
            painter.drawText(blue_rect, Qt.AlignmentFlag.AlignCenter, "D")
        
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "D")
        
        if self._hologram_factor > 0.5:
            pixel_size = 3
            pixel_count = 40
            pixel_max_distance = size * 0.7
            
            painter.setPen(Qt.PenStyle.NoPen)
            
            for _ in range(pixel_count):
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(0, pixel_max_distance)
                px = center_x + math.cos(angle) * distance
                py = center_y + math.sin(angle) * distance

                pixel_opacity = random.uniform(0.5, 1.0) * self._hologram_factor
                pixel_color = QColor(100 + random.randint(0, 155), 
                                    200 + random.randint(0, 55), 
                                    255, 
                                    int(180 * pixel_opacity * self._opacity))
                
                painter.setBrush(pixel_color)
                painter.drawRect(int(px - pixel_size/2), int(py - pixel_size/2), 
                               pixel_size, pixel_size)

        if self._hologram_factor > 0.4:
            glitch_count = 4
            for _ in range(glitch_count):
                if random.random() < 0.3:
                    glitch_height = random.randint(2, 6)
                    glitch_width = random.randint(int(size * 0.3), int(size * 0.8))
                    glitch_x = center_x - glitch_width // 2
                    glitch_y = center_y - size // 2 + random.randint(0, size)
                    
                    glitch_color = QColor(150, 220, 255, int(100 * self._opacity * self._hologram_factor))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(glitch_color)
                    painter.drawRect(int(glitch_x), int(glitch_y), glitch_width, glitch_height)
    
    def start_intro_animation(self):
        self.opacity_anim = QPropertyAnimation(self, b"opacity")
        self.opacity_anim.setDuration(1200)
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.opacity_anim.start()
    
    def start_rotation_animation(self):
        self.ring_anim = []
        durations = [15000, 20000, 12000]
        
        for i in range(3):
            anim = QPropertyAnimation(self, f"ringRotation{i}".encode())
            anim.setDuration(durations[i])
            anim.setStartValue(0.0)
            anim.setEndValue(360.0)
            anim.setLoopCount(-1)
            self.ring_anim.append(anim)
            anim.start()
            
        self.rotation_anim = QPropertyAnimation(self, b"rotation")
        self.rotation_anim.setDuration(30000)
        self.rotation_anim.setStartValue(0.0)
        self.rotation_anim.setEndValue(360.0)
        self.rotation_anim.setLoopCount(-1)
        self.rotation_anim.start()
    
    def start_pulse_animation(self):
        self.pulse_anim = QPropertyAnimation(self, b"pulseFactor")
        self.pulse_anim.setDuration(2000)
        self.pulse_anim.setStartValue(0.0)
        self.pulse_anim.setEndValue(1.0)
        self.pulse_anim.setLoopCount(-1)
        self.pulse_anim.start()
    
    def start_hologram_animation(self):
        self.hologram_anim = QPropertyAnimation(self, b"hologramFactor")
        self.hologram_anim.setDuration(4000)
        self.hologram_anim.setStartValue(0.0)
        self.hologram_anim.setEndValue(1.0)
        self.hologram_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.hologram_anim.start()
        
        self.hologram_shift_anim = QPropertyAnimation(self, b"hologramShift")
        self.hologram_shift_anim.setDuration(3000)
        self.hologram_shift_anim.setStartValue(0.0)
        self.hologram_shift_anim.setEndValue(10.0)
        self.hologram_shift_anim.setLoopCount(-1)
        self.hologram_shift_anim.start()

        self.grid_anim = QPropertyAnimation(self, b"gridOffset")
        self.grid_anim.setDuration(5000)
        self.grid_anim.setStartValue(0.0)
        self.grid_anim.setEndValue(10.0)
        self.grid_anim.setLoopCount(-1)
        self.grid_anim.start()
    
    def get_opacity(self):
        return self._opacity
        
    def set_opacity(self, value):
        self._opacity = value
        self.update()
    
    def get_rotation(self):
        return self._rotation
        
    def set_rotation(self, value):
        self._rotation = value
        self.update()
    
    def get_ring_rotation0(self):
        return self._ring_rotation[0]
        
    def set_ring_rotation0(self, value):
        self._ring_rotation[0] = value
        self.update()
    
    def get_ring_rotation1(self):
        return self._ring_rotation[1]
        
    def set_ring_rotation1(self, value):
        self._ring_rotation[1] = value
        self.update()
        
    def get_ring_rotation2(self):
        return self._ring_rotation[2]
        
    def set_ring_rotation2(self, value):
        self._ring_rotation[2] = value
        self.update()
        
    def get_pulse_factor(self):
        return self._pulse_factor
        
    def set_pulse_factor(self, value):
        self._pulse_factor = value
        self.update()
    
    def get_hologram_factor(self):
        return self._hologram_factor
        
    def set_hologram_factor(self, value):
        self._hologram_factor = value
        self.update()
    
    def get_hologram_shift(self):
        return self._hologram_shift
        
    def set_hologram_shift(self, value):
        self._hologram_shift = value
        self.update()
    
    def get_grid_offset(self):
        return self._grid_offset
        
    def set_grid_offset(self, value):
        self._grid_offset = value
        self.update()
    
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    rotation = pyqtProperty(float, get_rotation, set_rotation)
    ringRotation0 = pyqtProperty(float, get_ring_rotation0, set_ring_rotation0)
    ringRotation1 = pyqtProperty(float, get_ring_rotation1, set_ring_rotation1)
    ringRotation2 = pyqtProperty(float, get_ring_rotation2, set_ring_rotation2)
    pulseFactor = pyqtProperty(float, get_pulse_factor, set_pulse_factor)
    hologramFactor = pyqtProperty(float, get_hologram_factor, set_hologram_factor)
    hologramShift = pyqtProperty(float, get_hologram_shift, set_hologram_shift)
    gridOffset = pyqtProperty(float, get_grid_offset, set_grid_offset)

class WaveAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedHeight(50)
        
        self._wave_offset = 0.0
        self._amplitude = 10.0
        self._frequency = 0.05
        self._speed = 0.05
        self._wave_count = 3
        self._wave_colors = [
            QColor(0, 120, 200, 80),
            QColor(0, 160, 230, 60),
            QColor(100, 180, 255, 40)
        ]
        
        self._last_frame_time = 0
        self._optimization_timer = QTimer(self)
        self._optimization_timer.timeout.connect(self.update_wave)
        self._optimization_timer.start(33)
        
        self.start_wave_animation()
    
    def update_wave(self):
        current_time = int(time.time() * 1000)
        if current_time - self._last_frame_time > 30:
            self._wave_offset += self._speed
            self.update()
            self._last_frame_time = current_time
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_y = height / 2
        
        for wave_idx in range(self._wave_count):
            path = QPainterPath()
            path.moveTo(0, center_y)
            
            freq_variation = 1.0 + wave_idx * 0.4
            ampl_variation = 1.0 - wave_idx * 0.2
            phase_offset = wave_idx * 1.5
            
            for x in range(0, width + 2, 4):
                y = center_y + math.sin((x * self._frequency * freq_variation) + self._wave_offset + phase_offset) * (self._amplitude * ampl_variation)
                path.lineTo(x, y)
            
            path.lineTo(width, height)
            path.lineTo(0, height)
            path.closeSubpath()
            
            gradient = QLinearGradient(0, center_y, 0, height)
            gradient.setColorAt(0, self._wave_colors[wave_idx])
            gradient.setColorAt(1, QColor(self._wave_colors[wave_idx].red(), 
                                         self._wave_colors[wave_idx].green(), 
                                         self._wave_colors[wave_idx].blue(), 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)
    
    def start_wave_animation(self):
        self.wave_timer = QTimer(self)
        self.wave_timer.timeout.connect(lambda: self.update())
        self.wave_timer.start(50)

class LoginWindow(QMainWindow):
    login_successful = pyqtSignal(User)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DinamikChat - Giriş")
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon("assets/icons/app_icon.png"))
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QHBoxLayout(main_widget)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(50, 50, 50, 50)
        left_layout.setSpacing(20)
        
        logo_label = QLabel()
        pixmap = QPixmap("assets/images/app_logo.png")
        logo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        
        app_name = QLabel("DinamikChat")
        app_name.setFont(QFont("Arial", 24, QFont.Bold))
        app_name.setAlignment(Qt.AlignCenter)
        
        app_desc = QLabel("Yapay zeka destekli gelişmiş sohbet uygulaması")
        app_desc.setFont(QFont("Arial", 12))
        app_desc.setWordWrap(True)
        app_desc.setAlignment(Qt.AlignCenter)
        
        left_layout.addWidget(logo_label)
        left_layout.addWidget(app_name)
        left_layout.addWidget(app_desc)
        left_layout.addStretch()
        
        right_panel = QWidget()
        right_panel.setObjectName("loginPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(50, 50, 50, 50)
        right_layout.setSpacing(20)
        
        login_title = QLabel("Giriş Yap")
        login_title.setFont(QFont("Arial", 20, QFont.Bold))
        login_title.setAlignment(Qt.AlignCenter)
        
        username_label = QLabel("Kullanıcı Adı:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı adınızı girin")
        self.username_input.setMinimumHeight(40)
        
        password_label = QLabel("Şifre:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Şifrenizi girin")
        self.password_input.setMinimumHeight(40)
        
        self.remember_checkbox = QCheckBox("Beni Hatırla")
        
        login_button = QPushButton("Giriş Yap")
        login_button.setMinimumHeight(50)
        login_button.setObjectName("primaryButton")
        login_button.clicked.connect(self.login)
        
        register_layout = QHBoxLayout()
        register_text = QLabel("Hesabınız yok mu?")
        register_button = QPushButton("Kayıt Ol")
        register_button.setObjectName("linkButton")
        register_button.clicked.connect(self.show_register_form)
        
        register_layout.addWidget(register_text)
        register_layout.addWidget(register_button)
        register_layout.setAlignment(Qt.AlignCenter)
        
        right_layout.addWidget(login_title)
        right_layout.addSpacing(20)
        right_layout.addWidget(username_label)
        right_layout.addWidget(self.username_input)
        right_layout.addSpacing(10)
        right_layout.addWidget(password_label)
        right_layout.addWidget(self.password_input)
        right_layout.addSpacing(10)
        right_layout.addWidget(self.remember_checkbox)
        right_layout.addSpacing(20)
        right_layout.addWidget(login_button)
        right_layout.addSpacing(10)
        right_layout.addLayout(register_layout)
        right_layout.addStretch()
        
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        
        layout.addWidget(left_panel, 1)
        layout.addWidget(separator)
        layout.addWidget(right_panel, 1)
        
        self.setup_styles()
        
        self.user_manager = UserManager()
        
        self.registerForm = None

    def setup_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QPushButton#primaryButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton#primaryButton:hover {
                background-color: #3a76d8;
            }
            QPushButton#linkButton {
                background-color: transparent;
                color: #4a86e8;
                border: none;
                text-decoration: underline;
                font-weight: bold;
            }
            QWidget#loginPanel {
                background-color: white;
                border-radius: 8px;
            }
        """)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Hata", "Kullanıcı adı ve şifre boş olamaz.")
            return
        
        try:
            user = self.user_manager.get_user_by_username(username)
            
            if user is None:
                QMessageBox.warning(self, "Hata", "Kullanıcı bulunamadı.")
                return
                
            encoded_password = password.encode('utf-8')
            hashed_password = user.password_hash.encode('utf-8')
            
            if bcrypt.checkpw(encoded_password, hashed_password):
                self.successful_login(user)
            else:
                QMessageBox.warning(self, "Hata", "Şifre yanlış.")
        
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Giriş işlemi sırasında bir hata oluştu: {str(e)}")

    def successful_login(self, user):
        from ui.main_window import MainWindow
        
        self.main_window = MainWindow(user)
        self.main_window.show()
        self.close()

    def show_register_form(self):
        from register_form import RegisterForm
        
        if self.registerForm is None:
            self.registerForm = RegisterForm()
            
        self.registerForm.show()
        self.hide()

class RegisterForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DinamikChat - Kayıt")
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon("assets/icons/app_icon.png"))
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QHBoxLayout(main_widget)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(50, 50, 50, 50)
        left_layout.setSpacing(20)
        
        logo_label = QLabel()
        pixmap = QPixmap("assets/images/app_logo.png")
        logo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        
        app_name = QLabel("DinamikChat")
        app_name.setFont(QFont("Arial", 24, QFont.Bold))
        app_name.setAlignment(Qt.AlignCenter)
        
        app_desc = QLabel("Yapay zeka destekli gelişmiş sohbet uygulaması")
        app_desc.setFont(QFont("Arial", 12))
        app_desc.setWordWrap(True)
        app_desc.setAlignment(Qt.AlignCenter)
        
        left_layout.addWidget(logo_label)
        left_layout.addWidget(app_name)
        left_layout.addWidget(app_desc)
        left_layout.addStretch()
        
        right_panel = QWidget()
        right_panel.setObjectName("registerPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(50, 50, 50, 50)
        right_layout.setSpacing(20)
        
        register_title = QLabel("Kayıt Ol")
        register_title.setFont(QFont("Arial", 20, QFont.Bold))
        register_title.setAlignment(Qt.AlignCenter)
        
        username_label = QLabel("Kullanıcı Adı:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı adınızı girin")
        self.username_input.setMinimumHeight(40)
        
        email_label = QLabel("E-posta:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-posta adresinizi girin")
        self.email_input.setMinimumHeight(40)
        
        password_label = QLabel("Şifre:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Şifrenizi girin")
        self.password_input.setMinimumHeight(40)
        
        confirm_password_label = QLabel("Şifreyi Doğrula:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Şifrenizi tekrar girin")
        self.confirm_password_input.setMinimumHeight(40)
        
        register_button = QPushButton("Kayıt Ol")
        register_button.setMinimumHeight(50)
        register_button.setObjectName("primaryButton")
        register_button.clicked.connect(self.register)
        
        login_layout = QHBoxLayout()
        login_text = QLabel("Zaten hesabınız var mı?")
        login_button = QPushButton("Giriş Yap")
        login_button.setObjectName("linkButton")
        login_button.clicked.connect(self.show_login_window)
        
        login_layout.addWidget(login_text)
        login_layout.addWidget(login_button)
        login_layout.setAlignment(Qt.AlignCenter)
        
        right_layout.addWidget(register_title)
        right_layout.addSpacing(20)
        right_layout.addWidget(username_label)
        right_layout.addWidget(self.username_input)
        right_layout.addSpacing(10)
        right_layout.addWidget(email_label)
        right_layout.addWidget(self.email_input)
        right_layout.addSpacing(10)
        right_layout.addWidget(password_label)
        right_layout.addWidget(self.password_input)
        right_layout.addSpacing(10)
        right_layout.addWidget(confirm_password_label)
        right_layout.addWidget(self.confirm_password_input)
        right_layout.addSpacing(20)
        right_layout.addWidget(register_button)
        right_layout.addSpacing(10)
        right_layout.addLayout(login_layout)
        right_layout.addStretch()
        
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        
        layout.addWidget(left_panel, 1)
        layout.addWidget(separator)
        layout.addWidget(right_panel, 1)
        
        self.setup_styles()
        
        self.user_manager = UserManager()
        
        self.login_window = None

    def setup_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QPushButton#primaryButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton#primaryButton:hover {
                background-color: #3a76d8;
            }
            QPushButton#linkButton {
                background-color: transparent;
                color: #4a86e8;
                border: none;
                text-decoration: underline;
                font-weight: bold;
            }
            QWidget#registerPanel {
                background-color: white;
                border-radius: 8px;
            }
        """)

    def register(self):
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not username or not email or not password or not confirm_password:
            QMessageBox.warning(self, "Hata", "Tüm alanları doldurun.")
            return
            
        if password != confirm_password:
            QMessageBox.warning(self, "Hata", "Şifreler eşleşmiyor.")
            return
        
        try:
            existing_user = self.user_manager.get_user_by_username(username)
            if existing_user:
                QMessageBox.warning(self, "Hata", "Bu kullanıcı adı zaten kullanılıyor.")
                return
                
            existing_email = self.user_manager.get_user_by_email(email)
            if existing_email:
                QMessageBox.warning(self, "Hata", "Bu e-posta adresi zaten kullanılıyor.")
                return
                
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_password.decode('utf-8'),
                is_active=True,
                is_admin=False
            )
            
            self.user_manager.add_user(new_user)
            
            QMessageBox.information(self, "Başarılı", "Kayıt başarıyla tamamlandı. Şimdi giriş yapabilirsiniz.")
            
            self.show_login_window()
            
        except Exception as e:
            logging.error(f"Registration error: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Kayıt işlemi sırasında bir hata oluştu: {str(e)}")

    def show_login_window(self):
        from ui.login_window import LoginWindow
        
        if self.login_window is None:
            self.login_window = LoginWindow()
            
        self.login_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        initialize_database()
        window = LoginWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        QMessageBox.critical(None, "Kritik Hata", f"Uygulama başlatılırken bir hata oluştu: {str(e)}")
        sys.exit(1) 