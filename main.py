import sys
import os
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from database import init_db, User

def create_assets_dirs():
    dirs = ["assets", "assets/models", "assets/icons", "assets/styles"]
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)

def main():
    create_assets_dirs()

    init_db()

    app = QApplication(sys.argv)

    if os.path.exists("assets/icons/app_icon.png"):
        app.setWindowIcon(QIcon("assets/icons/app_icon.png"))

    login_window = LoginWindow()

    def handle_successful_login(user):
        login_window.hide()

        main_window = MainWindow(user)
        main_window.show()

        main_window.destroyed.connect(lambda: login_window.close())
    
    login_window.login_successful.connect(handle_successful_login)
    login_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 