import os
import json
import threading
import time
import requests
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class OpenAIChatManager(QObject):
    response_received = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        self.api_key = settings['openai']['api_key']
        self.model = settings['openai']['model']
        self.temperature = settings['openai']['temperature']
        self.max_tokens = settings['openai']['max_tokens']
        
        self.lock = threading.Lock()
        self.busy = False
    
    def get_response(self, user_input, callback=None):
        if self.busy:
            return False
        
        with self.lock:
            self.busy = True
        
        def request_thread():
            try:
                url = "https://api.openai.com/v1/chat/completions"
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                data = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Sen DinamikChat yapay zeka asistanısın. Kullanıcılara Türkçe dilinde yardımcı oluyorsun."
                        },
                        {
                            "role": "user",
                            "content": user_input
                        }
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
                
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        assistant_response = response_data["choices"][0]["message"]["content"]
                        
                        if callback:
                            callback(assistant_response)
                        else:
                            self.response_received.emit(assistant_response)
                    else:
                        error_message = "API yanıt döndürdü ancak cevap bulunamadı."
                        if callback:
                            callback(error_message)
                        else:
                            self.response_received.emit(error_message)
                else:
                    error_message = f"API hatası (Kod: {response.status_code}): {response.text}"
                    
                    if callback:
                        callback(error_message)
                    else:
                        self.response_received.emit(error_message)
            
            except Exception as e:
                error_message = f"İstek hatası: {str(e)}"
                
                if callback:
                    callback(error_message)
                else:
                    self.response_received.emit(error_message)
            
            finally:
                with self.lock:
                    self.busy = False
        
        thread = threading.Thread(target=request_thread)
        thread.daemon = True
        thread.start()
        
        return True

    def is_busy(self):
        with self.lock:
            return self.busy

chatgpt_manager = OpenAIChatManager() 