import openai
import os
import json
import threading
from queue import Queue

class ChatGPTManager:
    def __init__(self):
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        self.api_key = settings['api']['openai']['api_key']
        self.model = settings['api']['openai']['model']
        self.modes = settings['ui']['modes']
        self.current_mode = 'normal'
        self.current_mode_prompt = self.modes.get('normal', "")
        self.web_search_enabled = False
        self.reason_enabled = False
        
        openai.api_key = self.api_key
    
    def set_api_key(self, api_key):
        self.api_key = api_key
        openai.api_key = api_key
    
    def set_mode(self, mode):
        if mode in self.modes:
            self.current_mode = mode
            self.current_mode_prompt = self.modes.get(mode, "")
    
    def set_response_mode(self, mode_prompt):
        """ChatGPT'nin cevap modunu ayarlar
        
        Args:
            mode_prompt (str): Modun prompt metni
        """
        self.current_mode_prompt = mode_prompt
    
    def toggle_web_search(self):
        self.web_search_enabled = not self.web_search_enabled
        return self.web_search_enabled
    
    def toggle_reason(self):
        self.reason_enabled = not self.reason_enabled
        return self.reason_enabled
    
    def get_response(self, message, callback=None):
        prompt_suffix = self.current_mode_prompt
        
        messages = [
            {"role": "system", "content": f"Sen yardımcı bir yapay zeka asistanısın. {prompt_suffix}"}
        ]
        
        if self.web_search_enabled:
            messages[0]["content"] += " Web araması yaparak en güncel bilgileri kullanabilirsin."
        
        if self.reason_enabled:
            messages[0]["content"] += " Cevaplarında mantıksal çıkarımlar ve nedensellik ilişkileri kurabilirsin."
        
        messages.append({"role": "user", "content": message})
        
        def generate_response(response_queue):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                assistant_response = response.choices[0].message['content']
                response_queue.put(assistant_response)
                
                if callback:
                    callback(assistant_response)
            except Exception as e:
                error_message = f"OpenAI API hatası: {str(e)}"
                response_queue.put(error_message)
                
                if callback:
                    callback(error_message)
        
        response_queue = Queue()
        thread = threading.Thread(target=generate_response, args=(response_queue,))
        thread.daemon = True
        thread.start()

        if callback is None:
            return response_queue.get()

chatgpt_manager = ChatGPTManager() 