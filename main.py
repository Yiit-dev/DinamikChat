import sys
import os
import json
from PyQt6.QtWidgets import QApplication, QMessageBox
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
        login_window = LoginWindow()
        login_window.show()
    except Exception as e:
        print(f"Hata: {e}")
        sys.exit(1)
    sys.exit(app.exec())

def show_main_window(user, login_window):
    login_window.hide()
    
    if user is None:
        print("Hata: User nesnesi boş!")
        QMessageBox.critical(None, "Hata", "Kullanıcı bilgileri yüklenemedi.")
        login_window.show()
        return
        
    try:
        main_window = MainWindow(user)
        main_window.show()
    except Exception as e:
        print(f"Ana pencere oluşturulurken hata: {e}")
        QMessageBox.critical(None, "Hata", f"Ana pencere açılırken bir hata oluştu: {str(e)}")
        login_window.show()

if __name__ == "__main__":
    main() 