import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from ui.dashboard import DashboardWidget

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Lịch Việt")
    
    widget = DashboardWidget()
    widget.show()
    
    if widget.tray_icon is not None:
        widget.tray_icon.show()
        
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
