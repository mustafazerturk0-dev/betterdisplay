import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui import BTDSTrayApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    if getattr(sys, 'frozen', False):
        icon_path = os.path.join(sys._MEIPASS, 'assets', 'icon.jpg')
    else:
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.jpg'))
        
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    ex = BTDSTrayApp()
    
    if os.path.exists(icon_path):
        ex.tray_icon.setIcon(QIcon(icon_path))
        
    sys.exit(app.exec_())
