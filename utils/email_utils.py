import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import threading
import json

class EmailManager:
    def __init__(self):
        self.verification_codes = {}
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        self.email_settings = settings['email']
        
    def generate_verification_code(self, email):
        code = ''.join(random.choices(string.digits, k=6))
        self.verification_codes[email] = code
        return code
    
    def verify_code(self, email, code):
        stored_code = self.verification_codes.get(email)
        if stored_code and stored_code == code:
            del self.verification_codes[email]
            return True
        return False
    
    def send_verification_email(self, recipient, code):
        sender_email = self.email_settings['user']
        sender_password = self.email_settings['password']
        
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient
        message['Subject'] = 'DinamikChat Email Doğrulama Kodu'
        
        body = f"""
        Merhaba,
        
        DinamikChat hesabınızı doğrulamak için aşağıdaki kodu kullanın:
        
        {code}
        
        Bu kodu paylaşmayın ve kimseye vermeyin.
        
        Teşekkürler,
        DinamikChat Ekibi
        """
        
        message.attach(MIMEText(body, 'plain'))
        
        def send_email():
            try:
                server = smtplib.SMTP(self.email_settings['smtp_server'], self.email_settings['smtp_port'])
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
                server.quit()
                print(f"Doğrulama e-postası gönderildi: {recipient}")
            except Exception as e:
                print(f"E-posta gönderimi başarısız: {str(e)}")
                
        # Asenkron e-posta gönderimi
        email_thread = threading.Thread(target=send_email)
        email_thread.daemon = True
        email_thread.start()
        
    def send_reset_password_email(self, recipient, code):
        sender_email = self.email_settings['user']
        sender_password = self.email_settings['password']
        
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient
        message['Subject'] = 'DinamikChat Şifre Sıfırlama Kodu'
        
        body = f"""
        Merhaba,
        
        DinamikChat şifrenizi sıfırlamak için aşağıdaki kodu kullanın:
        
        {code}
        
        Bu kodu paylaşmayın ve kimseye vermeyin.
        
        Teşekkürler,
        DinamikChat Ekibi
        """
        
        message.attach(MIMEText(body, 'plain'))
        
        def send_email():
            try:
                server = smtplib.SMTP(self.email_settings['smtp_server'], self.email_settings['smtp_port'])
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
                server.quit()
                print(f"Şifre sıfırlama e-postası gönderildi: {recipient}")
            except Exception as e:
                print(f"E-posta gönderimi başarısız: {str(e)}")

        email_thread = threading.Thread(target=send_email)
        email_thread.daemon = True
        email_thread.start()

email_manager = EmailManager() 