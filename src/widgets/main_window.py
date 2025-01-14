from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from ai_response_manager import AiResponseThread, reconfig_ai
from core import app_color_palette, user_data, cache, api_cache_path, user_data_path
import json

from src.widgets.library_region import LibaryRegion
from src.widgets.ai_recommendations_region import AiRecommendationsRegion
from src.widgets.settings_menu import SettingsMenu

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Informações de uso do app
        self.setWindowTitle("Recomendador de Jogos e Filmes")
        self.mode = 'game'
        self.language = 'pt' # Vá em frente, implemente duas idiomas no app e uma configuração pra trocar entre elas pela GUI
        self.user_data = user_data

        # Bibilioteca que será enviada a IA
        self.movie_library = user_data['movie_library']
        self.game_library = user_data['game_library']

        # Resultados de pesquisa associados aos seus dados recolhidos da API com base nas recomendações da IA
        self.movie_recommendations = user_data['movie_recommendations']
        self.game_recommendations = user_data['game_recommendations']

        # Timer para limitar tempo de resposta de APIs
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.thread_timeout)

        self.setStyleSheet(f"background-color: {app_color_palette['dark-medium'][self.mode]}")
        
        #################################
        # GUI
        #################################

        # Define o widget central da janela e o layout horizontal (hbox) onde todos os widgets do app ficarão
        self.center_widget = QWidget(self)
        self.setCentralWidget(self.center_widget)
        self.hbox = QHBoxLayout(self.center_widget)
        self.hbox.setContentsMargins(0, 0, 0, 0)

        # Menu de configurações
        self.settings_menu = SettingsMenu(self)
        
        # Libary
        self.library_region = LibaryRegion(self)

        # AI
        self.ai_recommendation_region = AiRecommendationsRegion(self)

    def ai_response(self):
        # Pega o texto no prompt de usuário na área de recomendações da IA e deixa a caixa de texto vazia
        prompt = self.ai_recommendation_region.user_chat_input.text()
        self.ai_recommendation_region.user_chat_input.setText('')
        if prompt == "":  # Não enviar prompt vazio
            return
        
        # Formata o prompt de usuário
        current_libarary = self.game_library if self.mode == "game" else self.movie_library
        current_recommendations = self.game_recommendations if self.mode == "game" else self.movie_recommendations

        # Omite os campos de data de cada dicionário para reduzir o tamanho do prompt enviado a IA
        library_for_ai = {key : {'rating':current_libarary[key]['rating'], 'state':current_libarary[key]['state']} for key in current_libarary}
        recom_for_ai = [key for key in current_recommendations['High Priority']]
        
        # Prompt formatado
        formatted_prompt = {'type': self.mode, 'user_prompt': prompt, 'current_library': library_for_ai, 'current_recommendations': recom_for_ai}

        # Processa a resposta da IA criando uma instância da AiResponseThread
        self.ai_thread = AiResponseThread(formatted_prompt, current_libarary, current_recommendations, self.mode)
        self.ai_thread.processing_request.connect(self.lock_user_input)
        self.ai_thread.error.connect(self.handle_error)
        self.ai_thread.finished.connect(self.handle_response)
        self.ai_thread.start()

        # Inicia um timer para a resposta da ai_thread, 60s
        self.timer.start(60000)

    def lock_user_input(self, stage):
        # Impende novas mensagens de serem enviadas enquato a IA e as APIs não finalizaram o processamento da última
        self.ai_recommendation_region.user_chat_input.setReadOnly(True)
        self.ai_recommendation_region.user_chat_input.setText("")

        # Atualiza o texto da caixa de input com informações sobre o processamento do prompt
        self.ai_recommendation_region.user_chat_input.setPlaceholderText(stage)

    def handle_response(self, response):
        self.timer.stop()

        # Função para caso a ai_thread funcione corretamente
        print(f'Resposta do modelo: {response}')

        # Desbloqueia o campo de input do usuário
        self.ai_recommendation_region.user_chat_input.setReadOnly(False)
        self.ai_recommendation_region.user_chat_input.setPlaceholderText("Peça à IA recomendações ou que altere sua biblioteca")

        self.library_region.update()
        self.ai_recommendation_region.update()
            
    def handle_error(self, error):
        self.timer.stop()

        # Função para exibir mensagens de erro da ai_thread
        print(error)
        self.ai_recommendation_region.user_chat_input.setReadOnly(False)
        self.ai_recommendation_region.user_chat_input.setPlaceholderText(error)

    def thread_timeout(self):
        # Função para parar a ai_thread se ela levar tempo demais
        if self.ai_thread.isRunning():
            self.ai_thread.terminate()
            self.ai_thread.wait()

        self.handle_error("Resposta demorou demais")

    @staticmethod
    def reconfig_ai():
        reconfig_ai()

    def closeEvent(self, event):
        # Salva dados de usuário
        with open(user_data_path, 'w') as file:
            json.dump(user_data, file)

        # Salva o cache
        with open(api_cache_path, 'w') as file:
            json.dump(cache, file)

        event.accept()