import numpy as np
import json
import os
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import pyttsx3

class ModelManager(QObject):
    speech_started = pyqtSignal()
    speech_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        self.model_path = settings['model']['default_path']
        self.vertices = []
        self.faces = []
        self.normals = []
        self.texture_coords = []
        self.is_model_loaded = False
        
        self.speech_engine = pyttsx3.init()
        self.speech_engine.setProperty('rate', 150)
        self.speech_engine.setProperty('volume', 1.0)
        
        voices = self.speech_engine.getProperty('voices')
        for voice in voices:
            if "turkish" in voice.name.lower():
                self.speech_engine.setProperty('voice', voice.id)
                break
        
        self._load_model()
    
    def _load_model(self):
        try:
            if not os.path.exists(self.model_path):
                print(f"Model dosyası bulunamadı: {self.model_path}")
                return False
            
            with open(self.model_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    parts = line.split()
                    if not parts:
                        continue
                        
                    if parts[0] == 'v':
                        if len(parts) >= 4:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            self.vertices.append([x, y, z])
                    elif parts[0] == 'vn':
                        if len(parts) >= 4:
                            nx, ny, nz = float(parts[1]), float(parts[2]), float(parts[3])
                            self.normals.append([nx, ny, nz])
                    elif parts[0] == 'vt':
                        if len(parts) >= 3:
                            tu, tv = float(parts[1]), float(parts[2])
                            self.texture_coords.append([tu, tv])
                    elif parts[0] == 'f':
                        if len(parts) >= 4:
                            face = []
                            for i in range(1, len(parts)):
                                if '/' in parts[i]:
                                    v_indices = parts[i].split('/')
                                    face.append(int(v_indices[0]) - 1)
                                else:
                                    face.append(int(parts[i]) - 1)
                            self.faces.append(face)
            
            if len(self.vertices) > 0:
                self.is_model_loaded = True
                print(f"Model başarıyla yüklendi: {len(self.vertices)} vertices, {len(self.faces)} faces")
                return True
            else:
                print("Model yüklenemedi: Vertex bulunamadı")
                return False
        
        except Exception as e:
            print(f"Model yükleme hatası: {str(e)}")
            return False
    
    def get_model_data(self):
        if not self.is_model_loaded:
            return None
        
        return {
            'vertices': self.vertices,
            'faces': self.faces,
            'normals': self.normals,
            'texture_coords': self.texture_coords
        }
    
    def animate_mouth_for_speech(self, text):
        class SpeechThread(QThread):
            def __init__(self, parent, text, speech_engine):
                super().__init__(parent)
                self.text = text
                self.speech_engine = speech_engine
            
            def run(self):
                parent = self.parent()
                parent.speech_started.emit()
                self.speech_engine.say(self.text)
                self.speech_engine.runAndWait()
                parent.speech_finished.emit()
        
        speech_thread = SpeechThread(self, text, self.speech_engine)
        speech_thread.start()
        
    def calculate_mouth_animation_frames(self, text, duration_ms):
        if not self.is_model_loaded:
            return []
        
        # Bu fonksiyon metne göre ağız animasyonu oluşturur
        # Gerçek bir uygulamada dudak senkronizasyonu için daha karmaşık bir algoritma kullanılır
        # Burada basitleştirilmiş bir yaklaşım kullandım
        
        frames = []
        char_count = len(text)
        
        if char_count == 0:
            return frames
        
        frame_count = min(char_count * 4, duration_ms // 30)
        
        mouth_vertices_indices = []
        
        
        for i in range(min(10, len(self.vertices))):
            mouth_vertices_indices.append(i)
        
        for frame in range(frame_count):
            amplitude = np.sin(frame * 2 * np.pi / frame_count) * 0.1
            
            vertices_copy = self.vertices.copy()
            for idx in mouth_vertices_indices:
                vertices_copy[idx][1] += amplitude
            
            frames.append(vertices_copy)
        
        return frames

    def rotate_model(self, angle_x, angle_y, angle_z):
        if not self.is_model_loaded:
            return None

        angle_x = np.radians(angle_x)
        angle_y = np.radians(angle_y)
        angle_z = np.radians(angle_z)
        
        rotation_x = np.array([
            [1, 0, 0],
            [0, np.cos(angle_x), -np.sin(angle_x)],
            [0, np.sin(angle_x), np.cos(angle_x)]
        ])

        rotation_y = np.array([
            [np.cos(angle_y), 0, np.sin(angle_y)],
            [0, 1, 0],
            [-np.sin(angle_y), 0, np.cos(angle_y)]
        ])

        rotation_z = np.array([
            [np.cos(angle_z), -np.sin(angle_z), 0],
            [np.sin(angle_z), np.cos(angle_z), 0],
            [0, 0, 1]
        ])

        rotation_matrix = np.dot(rotation_z, np.dot(rotation_y, rotation_x))

        rotated_vertices = []
        for vertex in self.vertices:
            v = np.array(vertex)
            rotated_v = np.dot(rotation_matrix, v)
            rotated_vertices.append(rotated_v.tolist())
            
        return rotated_vertices
        
    def rotate_normals(self, angle_x, angle_y, angle_z):
        if not self.is_model_loaded or not self.normals:
            return None

        angle_x = np.radians(angle_x)
        angle_y = np.radians(angle_y)
        angle_z = np.radians(angle_z)
        
        rotation_x = np.array([
            [1, 0, 0],
            [0, np.cos(angle_x), -np.sin(angle_x)],
            [0, np.sin(angle_x), np.cos(angle_x)]
        ])

        rotation_y = np.array([
            [np.cos(angle_y), 0, np.sin(angle_y)],
            [0, 1, 0],
            [-np.sin(angle_y), 0, np.cos(angle_y)]
        ])

        rotation_z = np.array([
            [np.cos(angle_z), -np.sin(angle_z), 0],
            [np.sin(angle_z), np.cos(angle_z), 0],
            [0, 0, 1]
        ])

        rotation_matrix = np.dot(rotation_z, np.dot(rotation_y, rotation_x))

        rotated_normals = []
        for normal in self.normals:
            n = np.array(normal)
            rotated_n = np.dot(rotation_matrix, n)
            length = np.linalg.norm(rotated_n)
            if length > 0:
                rotated_n = rotated_n / length
            rotated_normals.append(rotated_n.tolist())
            
        return rotated_normals

model_manager = ModelManager() 