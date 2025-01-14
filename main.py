"""
API da Gemini AI: https://aistudio.google.com/app/u/1/apikey
API do GiantBomb: https://www.giantbomb.com/api/
API do TMDB: https://developer.themoviedb.org/reference/intro/authentication
"""
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.widgets.main_window import QApplication, MainWindow

if __name__ == "__main__":
    App = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(App.exec())
