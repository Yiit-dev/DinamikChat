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
    
    def send_verification_email(self, recipient, name=""):
        sender_email = self.email_settings['user']
        sender_password = self.email_settings['password']
        template_path = self.email_settings['verification']['template']
        subject = self.email_settings['verification']['subject']
        expiry_hours = self.email_settings['verification']['expiry_hours']
        
        code = self.generate_verification_code(recipient)
        verification_link = f"https://dinamikchat.com/verify?email={recipient}&code={code}"
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            html_content = html_content.replace('{name}', name if name else recipient.split('@')[0])
            html_content = html_content.replace('{verification_code}', code)
            html_content = html_content.replace('{verification_link}', verification_link)
            html_content = html_content.replace('{expiry_hours}', str(expiry_hours))
            
            message = MIMEMultipart('alternative')
            message['From'] = sender_email
            message['To'] = recipient
            message['Subject'] = subject
            
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)
            
            text_content = f"""
            Merhaba {name if name else recipient.split('@')[0]},
            
            DinamikChat hesabınızı doğrulamak için aşağıdaki kodu kullanın:
            
            {code}
            
            Bu kodu paylaşmayın ve kimseye vermeyin.
            
            Teşekkürler,
            DinamikChat Ekibi
            """
            text_part = MIMEText(text_content, 'plain')
            message.attach(text_part)
        else:
            message = MIMEMultipart()
            message['From'] = sender_email
            message['To'] = recipient
            message['Subject'] = subject
            
            body = f"""
            Merhaba {name if name else recipient.split('@')[0]},
            
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
                
        email_thread = threading.Thread(target=send_email)
        email_thread.daemon = True
        email_thread.start()
        
    def send_reset_password_email(self, recipient, name=""):
        sender_email = self.email_settings['user']
        sender_password = self.email_settings['password']
        template_path = self.email_settings['password_reset']['template']
        subject = self.email_settings['password_reset']['subject']
        expiry_hours = self.email_settings['password_reset']['expiry_hours']
        
        code = self.generate_verification_code(recipient)
        reset_link = f"https://dinamikchat.com/reset-password?email={recipient}&code={code}"
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            html_content = html_content.replace('{name}', name if name else recipient.split('@')[0])
            html_content = html_content.replace('{reset_link}', reset_link)
            html_content = html_content.replace('{expiry_hours}', str(expiry_hours))
            
            message = MIMEMultipart('alternative')
            message['From'] = sender_email
            message['To'] = recipient
            message['Subject'] = subject

            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)

            text_content = f"""
            Merhaba {name if name else recipient.split('@')[0]},
            
            DinamikChat şifrenizi sıfırlamak için aşağıdaki bağlantıyı kullanın:
            
            {reset_link}
            
            Bu bağlantı {expiry_hours} saat boyunca geçerlidir.
            
            Teşekkürler,
            DinamikChat Ekibi
            """
            text_part = MIMEText(text_content, 'plain')
            message.attach(text_part)
        else:
            message = MIMEMultipart()
            message['From'] = sender_email
            message['To'] = recipient
            message['Subject'] = subject
            
            body = f"""
            Merhaba {name if name else recipient.split('@')[0]},
            
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