import sys
import os
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from database import create_db, User, get_db_session

def create_assets_dirs():
    dirs = ["assets", "assets/models", "assets/icons", "assets/styles"]
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)

def main():
    create_assets_dirs()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/icons/app_icon.png"))
    
    create_db()
    
    try:
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            
        app_name = settings['app_name']
        app.setApplicationName(app_name)
        
        auto_login = settings.get('auto_login', False)
        
        if auto_login:
            session = get_db_session()
            admin_user = session.query(User).filter_by(email="admin@dinanik.com").first()
            
            if not admin_user:
                admin_user = User(
                    user_id="admin123",
                    name="Admin",
                    email="admin@dinanik.com",
                    password_hash="hashed_password",
                    is_admin=True
                )
                session.add(admin_user)
                session.commit()
            
            session.close()
            
            main_window = MainWindow(admin_user)
            main_window.show()
        else:
            login_window = LoginWindow()
            login_window.show()
        
    except Exception as e:
        print(f"Hata: {e}")
        sys.exit(1)
    
    sys.exit(app.exec())

def show_main_window(user, login_window):
    login_window.hide()
    main_window = MainWindow(user)
    main_window.show()

if __name__ == "__main__":
    main() 