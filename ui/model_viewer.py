from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QPainter, QPen, QLinearGradient, QBrush, QRadialGradient, QImage, QPixmap, QFont
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
        
        painter.drawEllipse(int(-width/2), int(-height/2), int(width), int(height))
        painter.restore()

class DNAHologram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.animation_phase = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)
        
        self.pulse_value = 0
        self.pulse_direction = 1
        
        self.strand_color1 = QColor(169, 159, 201, 40)
        self.strand_color2 = QColor(139, 198, 217, 40)
        self.connector_color = QColor(240, 240, 240, 20)
        
        self.horizontal = True
        
    def update_animation(self):
        self.animation_phase += 0.03
        
        self.pulse_value += 0.02 * self.pulse_direction
        if self.pulse_value > 1.0:
            self.pulse_value = 1.0
            self.pulse_direction = -1
        elif self.pulse_value < 0.3:
            self.pulse_value = 0.3
            self.pulse_direction = 1
            
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        if self.horizontal:
            dna_width = self.width() * 0.9
            dna_height = self.height() * 0.1
            horizontal_offset = (self.width() - dna_width) / 2
            segments = 40
            turns = 6
        else:
            dna_height = self.height() * 0.6
            dna_width = self.width() * 0.15
            vertical_offset = (self.height() - dna_height) / 2
            segments = 20
            turns = 3
        
        strand_thickness = 1
        connector_thickness = 1
        
        painter.save()
        painter.translate(center_x, center_y)
        
        alpha_base = int(40 * self.pulse_value)
        
        for i in range(segments + 1):
            t = i / segments
            
            if self.horizontal:
                x = horizontal_offset + dna_width * t - dna_width/2
                
                angle1 = 2 * math.pi * t * turns + self.animation_phase
                angle2 = 2 * math.pi * t * turns + self.animation_phase + math.pi
                
                y1 = dna_height * math.sin(angle1)
                y2 = dna_height * math.sin(angle2)
                
                point1 = (x, y1)
                point2 = (x, y2)
                
                fade_mult = 1.0
                if t > 0.85:
                    fade_mult = max(0, (1.0 - t) / 0.15)
                elif t < 0.15:
                    fade_mult = min(1.0, t / 0.15)
            else:
                y = vertical_offset + dna_height * t - dna_height/2
                
                angle1 = 2 * math.pi * t * turns + self.animation_phase
                angle2 = 2 * math.pi * t * turns + self.animation_phase + math.pi
                
                x1 = dna_width * math.sin(angle1)
                x2 = dna_width * math.sin(angle2)
                
                point1 = (x1, y)
                point2 = (x2, y)
                
                fade_mult = 1.0
            
            strand1_alpha = int(alpha_base * fade_mult)
            strand2_alpha = int(alpha_base * fade_mult)
            connector_alpha = int(20 * fade_mult)
            
            strand_color1 = QColor(169, 159, 201, strand1_alpha)
            strand_color2 = QColor(139, 198, 217, strand2_alpha)
            connector_color = QColor(240, 240, 240, connector_alpha)
            
            if i > 0:
                pen1 = QPen(strand_color1)
                pen1.setWidth(strand_thickness)
                painter.setPen(pen1)
                painter.drawLine(int(prev_point1[0]), int(prev_point1[1]), 
                              int(point1[0]), int(point1[1]))
                
                pen2 = QPen(strand_color2)
                pen2.setWidth(strand_thickness)
                painter.setPen(pen2)
                painter.drawLine(int(prev_point2[0]), int(prev_point2[1]), 
                              int(point2[0]), int(point2[1]))
            
            if i % 2 == 0:
                pen3 = QPen(connector_color)
                pen3.setWidth(connector_thickness)
                painter.setPen(pen3)
                painter.drawLine(int(point1[0]), int(point1[1]), 
                              int(point2[0]), int(point2[1]))
                
                if fade_mult > 0.2:
                    painter.setBrush(QBrush(QColor(255, 255, 255, int(20 * fade_mult))))
                    painter.drawEllipse(int(point1[0]-1), int(point1[1]-1), 1, 1)
                    painter.drawEllipse(int(point2[0]-1), int(point2[1]-1), 1, 1)
            
            prev_point1 = point1
            prev_point2 = point2

        painter.setPen(Qt.PenStyle.NoPen)
        for _ in range(8):
            if self.horizontal:
                glimmer_size = np.random.randint(1, 2)
                x_range = dna_width
                y_range = dna_height * 2
                
                x_pos = np.random.uniform(-x_range/2, x_range/2)
                fade_mult = 1.0
                if abs(x_pos) > dna_width * 0.4:
                    fade_mult = max(0, (dna_width/2 - abs(x_pos)) / (dna_width/2 * 0.2))
                
                glimmer_x = x_pos
                glimmer_y = np.random.uniform(-y_range/2, y_range/2)
            else:
                glimmer_size = np.random.randint(1, 2)
                angle = np.random.uniform(0, 2 * math.pi)
                distance = np.random.uniform(0, dna_width * 1.2)
                
                glimmer_x = distance * math.cos(angle)
                glimmer_y = np.random.uniform(-dna_height/2, dna_height/2)
                fade_mult = 1.0
            
            alpha = int(np.random.uniform(10, 30) * self.pulse_value * fade_mult)
            
            rand_hue = np.random.random()
            if rand_hue < 0.5:
                glimmer_color = QColor(169, 159, 201, alpha)
            else:
                glimmer_color = QColor(139, 198, 217, alpha)
            
            painter.setBrush(QBrush(glimmer_color))
            painter.drawEllipse(int(glimmer_x-glimmer_size/2), int(glimmer_y-glimmer_size/2), 
                              glimmer_size, glimmer_size)
        
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
        
        painter.drawEllipse(int(center_x - self.width()/3), int(center_y - self.height()/3), 
                          int(self.width()*2/3), int(self.height()*2/3))
        
        pen = QPen(QColor(0, 170, 255, 60 + int(40 * self.glow_intensity)))
        pen.setWidth(1)
        painter.setPen(pen)
        
        segments = 80
        radius = min(self.width(), self.height()) * 0.4
        
        painter.save()
        painter.translate(center_x, center_y)
        
        wave_factor = self.wave_factor * 3
        
        painter.drawEllipse(int(-radius), int(-radius), int(radius*2), int(radius*2))
        
        points = []
        for i in range(segments + 1):
            angle = 2.0 * math.pi * i / segments
            wave = 0.15 * math.sin(angle * 6 + wave_factor)
            adjusted_radius = radius * (1.0 + wave)
            
            x = adjusted_radius * math.cos(angle)
            y = adjusted_radius * math.sin(angle)
            points.append((x, y))

        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]), 
                          int(points[i+1][0]), int(points[i+1][1]))
        
        painter.restore()
        
        super().paintEvent(event)

class ModelViewer(QWidget):
    animation_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.dna_hologram = DNAHologram(self)
        self.dna_hologram.setGeometry(0, 0, self.width(), self.height())

        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        self.central_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        central_layout = QVBoxLayout(self.central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_frame = QFrame()
        self.title_frame.setObjectName("titleFrame")
        title_layout = QVBoxLayout(self.title_frame)
        title_layout.setContentsMargins(40, 40, 40, 40)
        
        self.ai_title = QLabel("YAPAY ZEKA")
        self.ai_title.setObjectName("aiTitle")
        self.ai_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.model_title = QLabel("MODELİ")
        self.model_title.setObjectName("modelTitle")
        self.model_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_layout.addWidget(self.ai_title)
        title_layout.addWidget(self.model_title)

        central_layout.addWidget(self.title_frame, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.central_widget)

        QTimer.singleShot(500, self.start_animation)

        self.setStyleSheet("""
            ModelViewer {
                background-color: transparent;
            }
            
            #centralWidget {
                background-color: transparent;
            }
            
            #titleFrame {
                background-color: rgba(13, 17, 23, 0.85);
                border: 3px solid rgba(169, 159, 201, 0.5);
                border-radius: 25px;
                margin: 10px;
                min-width: 450px;
                min-height: 200px;
            }
            
            #aiTitle {
                color: rgba(169, 159, 201, 0.95);
                font-family: 'Arial Black', sans-serif;
                font-size: 60px;
                font-weight: bold;
                letter-spacing: 5px;
                text-transform: uppercase;
            }
            
            #modelTitle {
                color: rgba(169, 159, 201, 0.8);
                font-family: 'Arial Black', sans-serif;
                font-size: 56px;
                font-weight: bold;
                letter-spacing: 5px;
                text-transform: uppercase;
            }
        """)
    
    def start_animation(self):
        title_anim = QPropertyAnimation(self.title_frame, b"geometry")
        title_anim.setDuration(1000)
        title_anim.setStartValue(self.title_frame.geometry().adjusted(0, -50, 0, -50))
        title_anim.setEndValue(self.title_frame.geometry())
        title_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        title_anim.start()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'dna_hologram'):
            self.dna_hologram.setGeometry(0, 0, self.width(), self.height())
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(13, 17, 23, 200))
        gradient.setColorAt(0.5, QColor(13, 17, 23, 150))
        gradient.setColorAt(1, QColor(13, 17, 23, 200))
        
        painter.fillRect(self.rect(), gradient)