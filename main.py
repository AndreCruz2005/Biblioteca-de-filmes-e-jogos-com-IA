import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.main_window import QApplication, MainWindow

if __name__ == "__main__":
    App = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(App.exec())
