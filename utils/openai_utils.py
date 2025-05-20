import os
import json
import threading
import time
import requests
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import random
import re

class OpenAIChatManager(QObject):
    response_received = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        self.load_settings()
        self.waiting_for_response = False
        self.current_message_id = None
        self.abort_current = False
        self.lock = threading.Lock()
    
    def load_settings(self):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            if 'api' in settings and 'openai' in settings['api']:
                self.api_key = settings['api']['openai']['api_key']
                self.model = settings['api']['openai']['model']
                self.temperature = settings['api']['openai']['temperature']
                self.max_tokens = settings['api']['openai']['max_tokens']
            else:
                self.api_key = "OPENAI_API_KEY"
                self.model = "gpt-3.5-turbo"
                self.temperature = 0.7
                self.max_tokens = 2000
        except Exception as e:
            print(f"Ayarlar yüklenirken hata oluştu: {e}")
            self.api_key = "OPENAI_API_KEY"
            self.model = "gpt-3.5-turbo"
            self.temperature = 0.7
            self.max_tokens = 2000
    
    def get_response(self, message, callback=None):
        if self.waiting_for_response:
            return False
        
        self.waiting_for_response = True
        message_id = time.time()
        self.current_message_id = message_id
        
        thread = threading.Thread(target=self._simulate_response, args=(message, message_id, callback))
        thread.daemon = True
        thread.start()

        return True
    
    def _simulate_response(self, message, message_id, callback):
        try:
            if "nasılsın" in message.lower():
                response = "İyiyim, teşekkür ederim! Size nasıl yardımcı olabilirim?"
            elif "selam" in message.lower() or "merhaba" in message.lower():
                response = "Merhaba! Size nasıl yardımcı olabilirim?"
            elif "nedir" in message.lower():
                topic = re.search(r"([a-zğüşıöçA-ZĞÜŞİÖÇ]+)\s+nedir", message.lower())
                if topic:
                    topic = topic.group(1)
                    response = f"{topic.capitalize()}, belirli bir kavram veya nesnenin açıklamasıdır. Daha spesifik bilgi için lütfen sorunuzu detaylandırın."
                else:
                    response = "Neyi açıklamamı istersiniz? Lütfen sorunuzu detaylandırın."
            elif "yapay zeka" in message.lower() or "ai" in message.lower():
                response = "Yapay zeka, insan zekasını taklit eden ve toplanan verilere göre yinelemeli olarak kendini geliştirebilen sistemlerdir. Bilgisayar bilimi dalıdır."
            elif "yardım" in message.lower():
                response = "Size şu konularda yardımcı olabilirim:\n- Sorularınızı yanıtlama\n- Bilgi verme\n- Önerilerde bulunma\n- Metin oluşturma\n\nNasıl yardımcı olabilirim?"
            elif "hava durumu" in message.lower():
                response = "Maalesef gerçek zamanlı hava durumu verilerine erişimim yok. Ancak güncel hava durumu için bir hava durumu sitesini veya uygulamasını kontrol edebilirsiniz."
            elif "saat" in message.lower():
                response = "Şu anki saati göremiyorum, ancak cihazınızın saatini kontrol edebilirsiniz."
            elif "teşekkür" in message.lower():
                response = "Rica ederim! Başka bir konuda yardıma ihtiyacınız olursa lütfen sorun."
            elif "dinle" in message.lower() or "ses" in message.lower() or "müzik" in message.lower():
                response = "Ses çalma veya müzik dinleme özelliğim henüz mevcut değil."
            elif "göster" in message.lower() or "resim" in message.lower() or "fotoğraf" in message.lower():
                response = "Görsel içerik gösterme özelliğim henüz mevcut değil."
            else:
                responses = [
                    "Bu konu hakkında size yardımcı olmak isterim. Daha fazla detay verebilir misiniz?",
                    "İlginç bir soru. Bu konu üzerinde biraz daha konuşabilir miyiz?",
                    "Anladığım kadarıyla bu konuyla ilgileniyorsunuz. Size nasıl yardımcı olabilirim?",
                    "Bu sorunuzu yanıtlamak için elimden geleni yapacağım. Biraz daha açıklayabilir misiniz?",
                    "Bu konuda size yardımcı olmaktan memnuniyet duyarım. Tam olarak neyi bilmek istiyorsunuz?"
                ]
                response = random.choice(responses)
            if callback and message_id == self.current_message_id and not self.abort_current:
                with self.lock:
                    self.waiting_for_response = False
                callback(response)
            with self.lock:
                if message_id == self.current_message_id:
                    self.waiting_for_response = False
        except Exception as e:
            print(f"Yanıt üretirken hata: {e}")
            with self.lock:
                self.waiting_for_response = False
    
    def abort_response(self):
        with self.lock:
            self.abort_current = True
            self.waiting_for_response = False
        
        time.sleep(0.2)
        
        with self.lock:
            self.abort_current = False

chatgpt_manager = OpenAIChatManager() 