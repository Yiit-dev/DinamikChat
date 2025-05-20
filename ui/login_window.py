from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QStackedWidget, QMessageBox, QFrame, QProgressBar
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QRect, pyqtProperty
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor, QPainter, QRadialGradient, QBrush, QLinearGradient, QPainterPath
import json
import os
import math
import random
import time

from database import User, get_db_session
from utils.email_utils import email_manager
from utils.animation_utils import AnimatableWidget
import validators

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
        
        with open('settings.json', 'r', encoding='utf-8') as f:
            self.settings = json.load(f)
        
        self.app_name = self.settings['app_name']
        self.is_dark_theme = True
        self.theme = self.settings['ui']['theme']['dark']
        self.pending_verification_user = None
        
        self.setWindowTitle(self.app_name)
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        
        self.setWindowIcon(QIcon("assets/icons/app_icon.svg"))
        
        self.init_ui()
        self.apply_styles()
        
        self.login_successful.connect(self.on_login_successful)
        
        self.start_intro_animation()
    
    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.logo_widget = AnimatedLogo()
        self.logo_widget.setFixedHeight(200)
        
        login_panel = QWidget()
        login_panel.setObjectName("loginPanel")
        login_layout = QVBoxLayout(login_panel)
        login_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.stacked_widget = QStackedWidget()
        
        def update_logo_visibility(index):
            if index == 0:
                self.logo_widget.setVisible(True)
            else:
                self.logo_widget.setVisible(False)
        
        self.stacked_widget.currentChanged.connect(update_logo_visibility)
        
        login_widget = QWidget()
        login_widget_layout = QVBoxLayout(login_widget)
        login_widget_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        login_title = QLabel("Giriş Yap")
        login_title.setFont(QFont("Arial", 20))
        login_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_layout = QVBoxLayout(form_frame)
        
        self.login_email_input = QLineEdit()
        self.login_email_input.setPlaceholderText("Kullanıcı Adı veya E-posta")
        self.login_email_input.setMinimumHeight(40)
        
        self.password_toggle_style = """
            QPushButton {
                border: none;
                background-color: transparent;
                color: %s;
            }
            QPushButton:hover {
                color: %s;
            }
        """ % (self.theme['foreground'], self.theme['accent'])
        
        self.password_strength_style = """
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: %s;
                width: 10px;
                margin: 0px;
            }
        """
        
        password_container = QWidget()
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(0)
        
        self.login_password_input = QLineEdit()
        self.login_password_input.setPlaceholderText("Parola")
        self.login_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password_input.setMinimumHeight(40)
        
        self.login_password_toggle = QPushButton()
        self.login_password_toggle.setIcon(QIcon("assets/icons/eye-slash.svg"))
        self.login_password_toggle.setFixedSize(40, 40)
        self.login_password_toggle.setStyleSheet(self.password_toggle_style)
        self.login_password_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_password_toggle.clicked.connect(self.toggle_login_password_visibility)
        
        password_layout.addWidget(self.login_password_input)
        password_layout.addWidget(self.login_password_toggle)
        
        login_button = QPushButton("Giriş Yap")
        login_button.setMinimumHeight(40)
        login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_button.clicked.connect(self.handle_login)
        
        forgot_password_button = QPushButton("Şifremi Unuttum")
        forgot_password_button.setObjectName("linkButton")
        forgot_password_button.setCursor(Qt.CursorShape.PointingHandCursor)
        forgot_password_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        
        register_button = QPushButton("Hesabınız yok mu? Kaydolun")
        register_button.setObjectName("linkButton")
        register_button.setCursor(Qt.CursorShape.PointingHandCursor)
        register_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        form_layout.addWidget(self.login_email_input)
        form_layout.addWidget(password_container)
        form_layout.addWidget(login_button)
        form_layout.addWidget(forgot_password_button, alignment=Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(register_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        login_widget_layout.addWidget(login_title)
        login_widget_layout.addWidget(form_frame)
        
        register_widget = QWidget()
        register_layout = QVBoxLayout(register_widget)
        register_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        register_title = QLabel("Kayıt Ol")
        register_title.setFont(QFont("Arial", 20))
        register_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        register_form_frame = QFrame()
        register_form_frame.setObjectName("formFrame")
        register_form_layout = QVBoxLayout(register_form_frame)
        register_form_layout.setSpacing(12)
        
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Kullanıcı Adı")
        self.register_username.setMinimumHeight(40)
        
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("E-posta")
        self.register_email.setMinimumHeight(40)
        
        register_password_container = QWidget()
        register_password_layout = QHBoxLayout(register_password_container)
        register_password_layout.setContentsMargins(0, 0, 0, 0)
        register_password_layout.setSpacing(0)
        
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("Parola")
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_password.setMinimumHeight(40)
        self.register_password.textChanged.connect(self.check_password_strength)
        
        self.register_password_toggle = QPushButton()
        self.register_password_toggle.setIcon(QIcon("assets/icons/eye-slash.svg"))
        self.register_password_toggle.setFixedSize(40, 40)
        self.register_password_toggle.setStyleSheet(self.password_toggle_style)
        self.register_password_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_password_toggle.clicked.connect(self.toggle_register_password_visibility)
        
        register_password_layout.addWidget(self.register_password)
        register_password_layout.addWidget(self.register_password_toggle)
        
        self.password_strength_bar = QProgressBar()
        self.password_strength_bar.setRange(0, 100)
        self.password_strength_bar.setValue(0)
        self.password_strength_bar.setFixedHeight(5)
        self.password_strength_bar.setTextVisible(False)
        self.password_strength_label = QLabel("Şifre Gücü: Zayıf")
        self.password_strength_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.password_requirements = QLabel("Şifre en az 8 karakter olmalı ve büyük harf, küçük harf, rakam ve özel karakter içermelidir.")
        self.password_requirements.setWordWrap(True)
        self.password_requirements.setStyleSheet("color: #888; font-size: 11px;")
        self.password_requirements.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.register_first_name = QLineEdit()
        self.register_first_name.setPlaceholderText("Ad")
        self.register_first_name.setMinimumHeight(40)
        
        self.register_last_name = QLineEdit()
        self.register_last_name.setPlaceholderText("Soyad")
        self.register_last_name.setMinimumHeight(40)
        
        register_button = QPushButton("Kayıt Ol")
        register_button.setMinimumHeight(40)
        register_button.setCursor(Qt.CursorShape.PointingHandCursor)
        register_button.clicked.connect(self.handle_register)
        
        back_to_login_button = QPushButton("Zaten hesabınız var mı? Giriş Yapın")
        back_to_login_button.setObjectName("linkButton")
        back_to_login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_to_login_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        register_form_layout.addWidget(self.register_username)
        register_form_layout.addWidget(self.register_email)
        register_form_layout.addWidget(register_password_container)
        register_form_layout.addWidget(self.password_strength_bar)
        register_form_layout.addWidget(self.password_strength_label)
        register_form_layout.addWidget(self.password_requirements)
        register_form_layout.addWidget(self.register_first_name)
        register_form_layout.addWidget(self.register_last_name)
        register_form_layout.addSpacing(10)
        register_form_layout.addWidget(register_button)
        register_form_layout.addSpacing(5)
        register_form_layout.addWidget(back_to_login_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        register_layout.addWidget(register_title)
        register_layout.addWidget(register_form_frame)
        
        self.stacked_widget.addWidget(login_widget)
        self.stacked_widget.addWidget(register_widget)
        
        login_layout.addWidget(self.logo_widget)
        login_layout.addWidget(self.stacked_widget)
        
        theme_button_layout = QHBoxLayout()
        theme_button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.theme_button = QPushButton()
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_button.setFixedSize(40, 40)
        self.theme_button.clicked.connect(self.toggle_theme)
        
        self.update_theme_button_icon()
        
        theme_button_layout.addWidget(self.theme_button)
        login_layout.insertLayout(0, theme_button_layout)
        
        main_layout.addWidget(login_panel)
        
        forgot_password_widget = QWidget()
        forgot_password_layout = QVBoxLayout(forgot_password_widget)
        forgot_password_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        forgot_password_title = QLabel("Şifremi Unuttum")
        forgot_password_title.setFont(QFont("Arial", 20))
        forgot_password_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        forgot_password_frame = QFrame()
        forgot_password_frame.setObjectName("formFrame")
        forgot_password_form_layout = QVBoxLayout(forgot_password_frame)
        
        self.forgot_email = QLineEdit()
        self.forgot_email.setPlaceholderText("E-posta")
        self.forgot_email.setMinimumHeight(40)
        
        send_code_button = QPushButton("Doğrulama Kodu Gönder")
        send_code_button.setMinimumHeight(40)
        send_code_button.setCursor(Qt.CursorShape.PointingHandCursor)
        send_code_button.clicked.connect(self.send_reset_code)
        
        self.verification_code = QLineEdit()
        self.verification_code.setPlaceholderText("Doğrulama Kodu")
        self.verification_code.setMinimumHeight(40)
        self.verification_code.setVisible(False)
        
        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("Yeni Parola")
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password.setMinimumHeight(40)
        self.new_password.setVisible(False)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Parolayı Doğrula")
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setMinimumHeight(40)
        self.confirm_password.setVisible(False)
        
        reset_password_button = QPushButton("Şifreyi Sıfırla")
        reset_password_button.setMinimumHeight(40)
        reset_password_button.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_password_button.clicked.connect(self.reset_password)
        reset_password_button.setVisible(False)
        
        self.reset_password_button = reset_password_button
        
        back_from_forgot_button = QPushButton("Giriş sayfasına dön")
        back_from_forgot_button.setObjectName("linkButton")
        back_from_forgot_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_from_forgot_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        forgot_password_form_layout.addWidget(self.forgot_email)
        forgot_password_form_layout.addWidget(send_code_button)
        forgot_password_form_layout.addWidget(self.verification_code)
        forgot_password_form_layout.addWidget(self.new_password)
        forgot_password_form_layout.addWidget(self.confirm_password)
        forgot_password_form_layout.addWidget(reset_password_button)
        forgot_password_form_layout.addWidget(back_from_forgot_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        forgot_password_layout.addWidget(forgot_password_title)
        forgot_password_layout.addWidget(forgot_password_frame)
        
        self.stacked_widget.addWidget(forgot_password_widget)
        
        verification_widget = QWidget()
        verification_layout = QVBoxLayout(verification_widget)
        verification_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        verification_title = QLabel("E-posta Doğrulama")
        verification_title.setFont(QFont("Arial", 20))
        verification_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        verification_frame = QFrame()
        verification_frame.setObjectName("formFrame")
        verification_form_layout = QVBoxLayout(verification_frame)
        verification_form_layout.setSpacing(12)
        
        verification_description = QLabel("E-posta adresinize gönderilen 6 haneli doğrulama kodunu girin.")
        verification_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        verification_description.setWordWrap(True)
        
        self.verification_code_register = QLineEdit()
        self.verification_code_register.setPlaceholderText("Doğrulama Kodu")
        self.verification_code_register.setMinimumHeight(40)
        
        verify_button = QPushButton("Doğrula")
        verify_button.setMinimumHeight(40)
        verify_button.setCursor(Qt.CursorShape.PointingHandCursor)
        verify_button.clicked.connect(self.verify_account)
        
        resend_code_button = QPushButton("Kodu Tekrar Gönder")
        resend_code_button.setObjectName("linkButton")
        resend_code_button.setCursor(Qt.CursorShape.PointingHandCursor)
        resend_code_button.clicked.connect(self.resend_verification_code)
        
        back_button = QPushButton("Giriş Ekranına Dön")
        back_button.setObjectName("linkButton")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        verification_form_layout.addWidget(verification_description)
        verification_form_layout.addWidget(self.verification_code_register)
        verification_form_layout.addWidget(verify_button)
        verification_form_layout.addWidget(resend_code_button, alignment=Qt.AlignmentFlag.AlignCenter)
        verification_form_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        verification_layout.addWidget(verification_title)
        verification_layout.addWidget(verification_frame)
        
        self.stacked_widget.addWidget(verification_widget)
        
        self.wave_animation = WaveAnimation()
        main_layout.addWidget(self.wave_animation, alignment=Qt.AlignmentFlag.AlignBottom)
        
        self.setCentralWidget(central_widget)
    
    def start_intro_animation(self):
        animation = QPropertyAnimation(self.stacked_widget, b"geometry")
        animation.setDuration(800)
        
        current_geometry = self.stacked_widget.geometry()
        start_geometry = QRect(
            current_geometry.x(),
            current_geometry.y() + 100,
            current_geometry.width(),
            current_geometry.height()
        )
        
        animation.setStartValue(start_geometry)
        animation.setEndValue(current_geometry)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
    
    def toggle_theme(self):
        if self.is_dark_theme:
            self.is_dark_theme = False
            self.theme = self.settings['ui']['theme']['light']
        else:
            self.is_dark_theme = True
            self.theme = self.settings['ui']['theme']['dark']
        
        self.update_theme_button_icon()
        
        self.apply_styles()
    
    def update_theme_button_icon(self):
        if self.is_dark_theme:
            self.theme_button.setToolTip("Açık Tema")
            self.theme_button.setText("☀️")
        else:
            self.theme_button.setToolTip("Koyu Tema")
            self.theme_button.setText("🌙")
    
    def apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {self.theme['background']};
                color: {self.theme['foreground']};
                font-family: 'Segoe UI', Arial;
            }}
            
            #loginPanel {{
                background-color: {self.theme['background']};
                padding: 20px;
            }}
            
            #formFrame {{
                background-color: {self.theme['secondary']};
                border-radius: 10px;
                padding: 20px;
                max-width: 400px;
            }}
            
            QLineEdit {{
                background-color: {self.theme['background']};
                border: 1px solid {self.theme['border']};
                border-radius: 5px;
                padding: 5px 10px;
                color: {self.theme['foreground']};
            }}
            
            QLineEdit:focus {{
                border: 1px solid {self.theme['accent']};
            }}
            
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: #0088cc;
            }}
            
            #linkButton {{
                background-color: transparent;
                color: {self.theme['accent']};
                border: none;
                text-decoration: underline;
                font-weight: normal;
            }}
            
            #linkButton:hover {{
                color: #0088cc;
                background-color: transparent;
            }}
            
            #themeButton {{
                background-color: {self.theme['secondary']};
                color: {self.theme['foreground']};
                border-radius: 20px;
                font-size: 18px;
            }}
            
            #themeButton:hover {{
                background-color: {self.theme['hover']};
            }}
        """)
    
    def handle_login(self):
        email_or_username = self.login_email_input.text().strip()
        password = self.login_password_input.text()
        if not email_or_username or not password:
            QMessageBox.warning(self, "Hata", "Kullanıcı adı/e-posta ve şifre gereklidir.")
            return
        try:
            session = get_db_session()
            user = session.query(User).filter((User.email == email_or_username) | (User.username == email_or_username)).first()
            
            if not user:
                QMessageBox.warning(self, "Hata", "Kullanıcı bulunamadı.")
                session.close()
                return
            
            if user.password != password:
                QMessageBox.warning(self, "Hata", "Hatalı şifre.")
                session.close()
                return
            
            if hasattr(user, 'is_verified') and not user.is_verified:
                 QMessageBox.warning(self, "Hata", "Hesabınız doğrulanmadı. Lütfen e-posta adresinize gönderilen doğrulama kodunu girin.")
                 self.pending_verification_user = user
                 self.stacked_widget.setCurrentIndex(3)
                 session.close()
                 return

            self.login_successful.emit(user)
            session.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Giriş yapılırken bir hata oluştu: {str(e)}")
            session.close()
    
    def handle_register(self):
        username = self.register_username.text().strip()
        email = self.register_email.text().strip()
        password = self.register_password.text()
        first_name = self.register_first_name.text().strip()
        last_name = self.register_last_name.text().strip()
        
        if not username or not email or not password or not first_name or not last_name:
            QMessageBox.warning(self, "Hata", "Tüm alanlar zorunludur.")
            return
            
        if len(password) < 8:
            QMessageBox.warning(self, "Hata", "Parola en az 8 karakter olmalıdır.")
            return
            
        if not validators.email(email):
            QMessageBox.warning(self, "Hata", "Geçerli bir e-posta adresi girin.")
            return
            
        session = get_db_session()
        try:
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    QMessageBox.warning(self, "Hata", "Bu kullanıcı adı zaten kullanılıyor.")
                else:
                    QMessageBox.warning(self, "Hata", "Bu e-posta adresi zaten kullanılıyor.")
                session.close()
                return
                
            new_user = User(
                user_id=User.generate_user_id(),
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_admin=False,
                is_verified=False
            )
            
            session.add(new_user)
            session.commit()
            session.close()
            
            self.pending_verification_user = new_user
            QMessageBox.information(self, "Kayıt Başarılı", "Hesabınız oluşturuldu. Lütfen e-posta adresinize gönderilen doğrulama kodunu girin.")
            self.stacked_widget.setCurrentIndex(3)
            
        except Exception as e:
            session.rollback()
            session.close()
            QMessageBox.critical(self, "Hata", f"Kayıt sırasında bir hata oluştu: {str(e)}")
    
    def verify_account(self):
        code = self.verification_code_register.text().strip()
        
        if not hasattr(self, 'pending_verification_user') or not self.pending_verification_user:
            QMessageBox.warning(self, "Hata", "Doğrulama yapılacak bir kullanıcı bulunamadı.")
            self.stacked_widget.setCurrentIndex(0)
            return
        
        if not code:
            QMessageBox.warning(self, "Doğrulama Hatası", "Lütfen doğrulama kodunu girin.")
            return
        
        session = get_db_session()
        try:
            user = session.query(User).filter(User.user_id == self.pending_verification_user.user_id).first()
            
            if user and hasattr(user, 'verification_code') and user.verification_code == code:
                user.is_verified = True
                user.verification_code = None
                session.commit()
                session.close()
                
                QMessageBox.information(self, "Başarılı", "Hesabınız başarıyla doğrulandı. Şimdi giriş yapabilirsiniz.")
                self.stacked_widget.setCurrentIndex(0)
                self.login_email_input.setText(user.username)
                self.login_password_input.setText("")
                self.login_password_input.setFocus()
            else:
                session.close()
                QMessageBox.warning(self, "Doğrulama Hatası", "Doğrulama kodu hatalı veya süresi dolmuş.")
                
        except Exception as e:
            session.rollback()
            session.close()
            QMessageBox.critical(self, "Hata", f"Doğrulama sırasında bir hata oluştu: {str(e)}")
    
    def send_reset_code(self):
        email = self.forgot_email.text().strip()
        
        if not email:
            QMessageBox.warning(self, "Hata", "E-posta adresi gereklidir.")
            return
        
        if not validators.email(email):
            QMessageBox.warning(self, "Hata", "Geçerli bir e-posta adresi girin.")
            return
        
        session = get_db_session()
        
        try:
            user = session.query(User).filter_by(email=email).first()
            
            if not user:
                QMessageBox.information(self, "Bilgi", "Eğer bu e-posta sistemimizde kayıtlıysa, bir şifre sıfırlama kodu gönderilecektir.")
                return
            
            code = email_manager.generate_verification_code(email)
            email_manager.send_reset_password_email(email, code)
            
            self.verification_code.setVisible(True)
            self.new_password.setVisible(True)
            self.confirm_password.setVisible(True)
            self.reset_password_button.setVisible(True)
            
            QMessageBox.information(self, "Bilgi", "Şifre sıfırlama kodu e-posta adresinize gönderildi.")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kod gönderimi sırasında bir hata oluştu: {str(e)}")
        finally:
            session.close()
    
    def reset_password(self):
        email = self.forgot_email.text().strip()
        code = self.verification_code.text().strip()
        new_password = self.new_password.text()
        confirm_password = self.confirm_password.text()
        
        if not email or not code or not new_password or not confirm_password:
            QMessageBox.warning(self, "Hata", "Tüm alanlar zorunludur.")
            return
            
        if new_password != confirm_password:
            QMessageBox.warning(self, "Hata", "Parolalar eşleşmiyor.")
            return
            
        if len(new_password) < 8:
            QMessageBox.warning(self, "Hata", "Parola en az 8 karakter olmalıdır.")
            return

        session = get_db_session()
        try:
            user = session.query(User).filter_by(email=email).first()
            
            if not user:
                QMessageBox.warning(self, "Hata", "Kullanıcı bulunamadı.")
                session.close()
                return
                
            if not hasattr(user, 'verification_code') or user.verification_code != code:
                 QMessageBox.warning(self, "Hata", "Doğrulama kodu geçersiz veya süresi dolmuş.")
                 session.close()
                 return

            user.password = new_password
            user.verification_code = None
            
            session.commit()
            session.close()
            
            QMessageBox.information(self, "Başarılı", "Parolanız başarıyla sıfırlandı. Şimdi giriş yapabilirsiniz.")
            
            self.verification_code.setVisible(False)
            self.new_password.setVisible(False)
            self.confirm_password.setVisible(False)
            self.forgot_email.clear()
            self.verification_code.clear()
            self.new_password.clear()
            self.confirm_password.clear()
            self.stacked_widget.setCurrentIndex(0)

        except Exception as e:
            session.rollback()
            session.close()
            QMessageBox.critical(self, "Hata", f"Şifre sıfırlama sırasında bir hata oluştu: {str(e)}")
    
    def toggle_login_password_visibility(self):
        if self.login_password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.login_password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.login_password_toggle.setIcon(QIcon("assets/icons/eye.svg"))
        else:
            self.login_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.login_password_toggle.setIcon(QIcon("assets/icons/eye-slash.svg"))
    
    def toggle_register_password_visibility(self):
        if self.register_password.echoMode() == QLineEdit.EchoMode.Password:
            self.register_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.register_password_toggle.setIcon(QIcon("assets/icons/eye.svg"))
        else:
            self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.register_password_toggle.setIcon(QIcon("assets/icons/eye-slash.svg"))
    
    def check_password_strength(self):
        password = self.register_password.text()
        
        strength = 0
        feedback = []
        
        if len(password) >= 8:
            strength += 25
        else:
            feedback.append("en az 8 karakter")
        
        if any(c.isupper() for c in password):
            strength += 25
        else:
            feedback.append("büyük harf")
        
        if any(c.islower() for c in password):
            strength += 25
        else:
            feedback.append("küçük harf")
        
        if any(c.isdigit() for c in password):
            strength += 15
        else:
            feedback.append("rakam")
        
        special_chars = "!@#$%^&*()-+?_=,<>/"
        if any(c in special_chars for c in password):
            strength += 10
        else:
            feedback.append("özel karakter")
        
        self.password_strength_bar.setValue(strength)
        
        if strength < 40:
            self.password_strength_label.setText("Şifre Gücü: Zayıf")
            self.password_strength_bar.setStyleSheet(self.password_strength_style % "#ff4d4d")
        elif strength < 70:
            self.password_strength_label.setText("Şifre Gücü: Orta")
            self.password_strength_bar.setStyleSheet(self.password_strength_style % "#ffaa00")
        elif strength < 90:
            self.password_strength_label.setText("Şifre Gücü: Güçlü")
            self.password_strength_bar.setStyleSheet(self.password_strength_style % "#2eb82e")
        else:
            self.password_strength_label.setText("Şifre Gücü: Çok Güçlü")
            self.password_strength_bar.setStyleSheet(self.password_strength_style % "#00cc00")
        
        if feedback:
            self.password_requirements.setText(f"Şifre şunları içermelidir: {', '.join(feedback)}")
        else:
            self.password_requirements.setText("Tüm şifre gereksinimleri karşılandı ✓")
            self.password_requirements.setStyleSheet("color: #2eb82e; font-size: 11px;")

    def resend_verification_code(self):
        if not hasattr(self, 'pending_verification_user') or not self.pending_verification_user:
            QMessageBox.warning(self, "Hata", "Doğrulama yapılacak bir kullanıcı bulunamadı.")
            self.stacked_widget.setCurrentIndex(0)
            return
        
        user_email = self.pending_verification_user.get("email") if isinstance(self.pending_verification_user, dict) else self.pending_verification_user.email
        user_name = self.pending_verification_user.get("first_name") if isinstance(self.pending_verification_user, dict) else self.pending_verification_user.first_name
        
        try:
            email_manager.send_verification_email(user_email, user_name)
            QMessageBox.information(self, "Bilgi", f"Doğrulama kodu {user_email} adresine tekrar gönderildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kod gönderimi sırasında bir hata oluştu: {str(e)}")

    def on_login_successful(self, user):
        from ui.main_window import MainWindow
        self.main_window = MainWindow(user)
        self.main_window.show()
        self.hide() 