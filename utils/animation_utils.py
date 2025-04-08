from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QPoint, QSize, Qt, pyqtProperty
from PyQt6.QtWidgets import QWidget

class AnimationUtils:
    @staticmethod
    def slide_animation(widget, start_value, end_value, duration=300, property_name=b"geometry", 
                        easing=QEasingCurve.Type.OutCubic, finished_callback=None):
        animation = QPropertyAnimation(widget, property_name)
        animation.setDuration(duration)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setEasingCurve(easing)
        
        if finished_callback:
            animation.finished.connect(finished_callback)
        
        return animation
    
    @staticmethod
    def fade_animation(widget, start_value=0.0, end_value=1.0, duration=300, 
                        easing=QEasingCurve.Type.OutCubic, finished_callback=None):
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setEasingCurve(easing)
        
        if finished_callback:
            animation.finished.connect(finished_callback)
        
        return animation
    
    @staticmethod
    def resize_animation(widget, start_size, end_size, duration=300, 
                       easing=QEasingCurve.Type.OutCubic, finished_callback=None):
        animation = QPropertyAnimation(widget, b"size")
        animation.setDuration(duration)
        animation.setStartValue(start_size)
        animation.setEndValue(end_size)
        animation.setEasingCurve(easing)
        
        if finished_callback:
            animation.finished.connect(finished_callback)
        
        return animation
    
    @staticmethod
    def panel_toggle_animation(panel, expanded_width, collapsed_width, duration=300, 
                             finished_callback=None):
        current_width = panel.width()
        is_expanding = current_width < expanded_width
        target_width = expanded_width if is_expanding else collapsed_width
        
        animation = QPropertyAnimation(panel, b"minimumWidth")
        animation.setDuration(duration)
        animation.setStartValue(current_width)
        animation.setEndValue(target_width)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if finished_callback:
            animation.finished.connect(finished_callback)
        
        return animation, is_expanding

class AnimatableWidget(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation_progress = 0.0
        self._glow_intensity = 0.0
        self._wave_factor = 0.0

    def get_animation_progress(self):
        return self._animation_progress
    
    def set_animation_progress(self, progress):
        self._animation_progress = progress
        self.update()
    
    animation_progress = pyqtProperty(float, get_animation_progress, set_animation_progress)

    def get_glow_intensity(self):
        return self._glow_intensity
    
    def set_glow_intensity(self, intensity):
        self._glow_intensity = intensity
        self.update()
    
    glow_intensity = pyqtProperty(float, get_glow_intensity, set_glow_intensity)

    def get_wave_factor(self):
        return self._wave_factor
    
    def set_wave_factor(self, factor):
        self._wave_factor = factor
        self.update()
    
    wave_factor = pyqtProperty(float, get_wave_factor, set_wave_factor)
    
    def start_glow_animation(self, duration=1500):
        animation = QPropertyAnimation(self, b"glow_intensity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        animation.setLoopCount(-1)
        animation.start()
        return animation
    
    def start_wave_animation(self, duration=3000):
        animation = QPropertyAnimation(self, b"wave_factor")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(2 * 3.14159)
        animation.setEasingCurve(QEasingCurve.Type.Linear)
        animation.setLoopCount(-1)
        animation.start()
        return animation 