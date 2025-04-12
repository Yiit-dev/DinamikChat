from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QPen, QLinearGradient, QBrush, QRadialGradient, QImage, QPixmap
import math
import numpy as np

from utils.animation_utils import AnimatableWidget

class HologramRing(QWidget):
    def __init__(self, parent=None, rotation_deg=0, rotation_speed=15, reverse=False):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.rotation_angle = rotation_deg
        self.rotation_speed = rotation_speed
        self.reverse = reverse
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(50)
        
    def rotate(self):
        delta = 0.5 if not self.reverse else -0.5
        self.rotation_angle = (self.rotation_angle + delta) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.save()
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.rotation_angle)
        
        pen = QPen(QColor(0, 170, 255, 40))
        pen.setWidth(2)
        painter.setPen(pen)
        
        width = self.width() * 0.9
        height = self.height() * 0.3
        
        painter.drawEllipse(-width/2, -height/2, width, height)
        painter.restore()

class HologramicBackgroundWidget(AnimatableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.ring_rotation = 0
        self.wave_offset = 0
        
        self.rings = []
        self.setup_rings()
        
        self.glimmer_timer = QTimer(self)
        self.glimmer_timer.timeout.connect(self.update_glimmer)
        self.glimmer_timer.start(50)
        
        self.start_wave_animation(4000)
        
    def setup_rings(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        ring_container = QWidget(self)
        ring_container.setFixedHeight(self.height())
        ring_layout = QVBoxLayout(ring_container)
        ring_layout.setContentsMargins(0, 0, 0, 0)
        
        ring1 = HologramRing(rotation_deg=0, rotation_speed=15, reverse=False) 
        ring2 = HologramRing(rotation_deg=60, rotation_speed=20, reverse=True)
        ring3 = HologramRing(rotation_deg=120, rotation_speed=25, reverse=False)
        
        layout.addWidget(ring1)
        layout.addWidget(ring2)
        layout.addWidget(ring3)
        
        self.rings = [ring1, ring2, ring3]
        
    def update_glimmer(self):
        self.wave_offset += 0.05
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        gradient = QRadialGradient(center_x, center_y, self.width() / 1.5)
        gradient.setColorAt(0, QColor(0, 170, 255, 30 + int(20 * self.glow_intensity)))
        gradient.setColorAt(0.7, QColor(0, 120, 180, 10 + int(10 * self.glow_intensity)))
        gradient.setColorAt(1, QColor(0, 80, 120, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        
        painter.drawEllipse(center_x - self.width()/3, center_y - self.height()/3, 
                          self.width()*2/3, self.height()*2/3)
        
        pen = QPen(QColor(0, 170, 255, 60 + int(40 * self.glow_intensity)))
        pen.setWidth(1)
        painter.setPen(pen)
        
        segments = 80
        radius = min(self.width(), self.height()) * 0.4
        
        painter.save()
        painter.translate(center_x, center_y)
        
        wave_factor = self.wave_factor * 3
        
        painter.drawEllipse(-radius, -radius, radius*2, radius*2)
        
        points = []
        for i in range(segments + 1):
            angle = 2.0 * math.pi * i / segments
            wave = 0.15 * math.sin(angle * 6 + wave_factor)
            adjusted_radius = radius * (1.0 + wave)
            
            x = adjusted_radius * math.cos(angle)
            y = adjusted_radius * math.sin(angle)
            points.append((x, y))

        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], 
                          points[i+1][0], points[i+1][1])
        
        painter.restore()
        
        super().paintEvent(event)

class ModelViewer(QWidget):
    animation_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.model_data = None
        self.animation_frames = []
        self.current_frame = 0
        self.is_speaking = False
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        
        self.rotation_x = 0
        self.rotation_y = 0
        self.rotation_z = 0
        self.scale = 1.0
        
        self.bg_animation_timer = QTimer(self)
        self.bg_animation_timer.timeout.connect(self.update_background_animation)
        self.bg_animation_timer.start(50)
        self.bg_animation_angle = 0
        self.bg_animation_color = QColor(0, 170, 255, 100)
        
        self.grid_size = 20
        self.grid_spacing = 0.2
        
        self.container_layout = QVBoxLayout(self)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.hologram_image = QLabel()
        self.hologram_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hologram_image.setObjectName("hologramImage")
        
        self.create_default_hologram()
        
        self.hologram_bg = HologramicBackgroundWidget(self)
        self.container_layout.addWidget(self.hologram_bg)
        self.container_layout.addWidget(self.hologram_image)
        
        self.hologram_bg.start_glow_animation(2000)
        
        self.auto_rotate = True
        self.auto_rotate_speed_x = 0.0
        self.auto_rotate_speed_y = 0.3
        self.auto_rotate_speed_z = 0.0
        self.auto_rotate_timer = QTimer(self)
        self.auto_rotate_timer.timeout.connect(self.update_auto_rotation)
        self.auto_rotate_timer.start(30)
    
    def create_default_hologram(self):
        width, height = 400, 400
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x, center_y = width // 2, height // 2
        gradient = QRadialGradient(center_x, center_y, width // 3)
        gradient.setColorAt(0, QColor(0, 170, 255, 150))
        gradient.setColorAt(1, QColor(0, 80, 180, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_x - width//4, center_y - height//4, width//2, height//2)
        
        pen = QPen(QColor(0, 200, 255, 180))
        pen.setWidth(2)
        painter.setPen(pen)
        
        painter.drawEllipse(center_x - width//6, center_y - height//4, width//3, height//4)
        
        painter.drawEllipse(center_x - width//7, center_y, width//3.5, height//5)
        
        eye_size = width // 20
        painter.drawEllipse(center_x - width//10 - eye_size//2, center_y - height//10, eye_size, eye_size)
        painter.drawEllipse(center_x + width//10 - eye_size//2, center_y - height//10, eye_size, eye_size)
        
        painter.end()
        
        pixmap = QPixmap.fromImage(image)
        self.hologram_image.setPixmap(pixmap)
        self.hologram_image.setStyleSheet("background: transparent;")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'hologram_bg'):
            self.hologram_bg.setGeometry(0, 0, self.width(), self.height())
        
        self.create_default_hologram()
    
    def set_model_data(self, model_data):
        self.model_data = model_data
        
        if model_data:
            self.play_model_loaded_animation()
        
        self.update()
    
    def play_model_loaded_animation(self):
        self.scale = 0.1
        
        animation = QPropertyAnimation(self, b"modelScale")
        animation.setDuration(800)
        animation.setStartValue(0.1)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutElastic)
        animation.start()
    
    def get_model_scale(self):
        return self.scale
    
    def set_model_scale(self, scale):
        self.scale = scale
        self.update()
    
    modelScale = pyqtProperty(float, get_model_scale, set_model_scale)
    
    def update_background_animation(self):
        self.bg_animation_angle += 0.5
        if self.bg_animation_angle >= 360:
            self.bg_animation_angle = 0
        self.update()
    
    def update_animation(self):
        if len(self.animation_frames) > 0:
            self.current_frame += 1
            if self.current_frame >= len(self.animation_frames):
                self.current_frame = 0
                self.animation_timer.stop()
                self.animation_frames = []
                self.animation_finished.emit()
            self.update()
    
    def start_animation(self, frames, fps=30):
        if frames and len(frames) > 0:
            self.animation_frames = frames
            self.current_frame = 0
            self.animation_timer.start(1000 // fps)
    
    def update_auto_rotation(self):
        if self.auto_rotate and self.model_data:
            self.rotation_x += self.auto_rotate_speed_x
            self.rotation_y += self.auto_rotate_speed_y
            self.rotation_z += self.auto_rotate_speed_z
            
            self.rotation_x %= 360
            self.rotation_y %= 360
            self.rotation_z %= 360
            
            self.update()
            
    def set_auto_rotate(self, enabled):
        self.auto_rotate = enabled
        
    def set_auto_rotate_speeds(self, speed_x, speed_y, speed_z):
        self.auto_rotate_speed_x = speed_x
        self.auto_rotate_speed_y = speed_y
        self.auto_rotate_speed_z = speed_z
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.auto_rotate = False
        self.last_pos = event.pos()
        
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.auto_rotate = True
        
    def mouseMoveEvent(self, event):
        if not hasattr(self, 'last_pos'):
            self.last_pos = event.pos()
            
        dx = event.pos().x() - self.last_pos.x()
        dy = event.pos().y() - self.last_pos.y()
        
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.rotation_y += dx * 0.5
            self.rotation_x += dy * 0.5
            self.update()
            
        self.last_pos = event.pos()
        
    def wheelEvent(self, event):
        super().wheelEvent(event)
        delta = event.angleDelta().y()

        scale_factor = 1.1 if delta > 0 else 0.9
        self.scale *= scale_factor

        self.scale = max(0.1, min(5.0, self.scale))
        self.update()