"""
GUI feita com a biblioteca PyQt5
API da Gemini AI: https://aistudio.google.com/app/u/1/apikey
API do GiantBomb: https://www.giantbomb.com/api/
API do TMDB: https://developer.themoviedb.org/reference/intro/authentication
"""
import google.generativeai as genai
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from api_calling import get_game_data, get_movie_data, url_to_png
from core import app_color_palette, path_to_folder, user_data, cache, api_cache_path, user_data_path
import sys, json, os, socket

# Inicializa Gemini
genai.configure(api_key=user_data['api_keys']['GOOGLE'])

# Configurações do modelo de IA
main_generation_config = {
  "temperature": 0,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",  # Resposta sempre em JSON
}

# Criar o modelo de IA
def create_model():
    instructions_path = os.path.join(path_to_folder, 'model_instructions.txt')

    model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b-latest",
    generation_config=main_generation_config,
    system_instruction=open(instructions_path, encoding="utf8").readlines()
    )

    return model

# Inicia conversa com o modelo
conversation = create_model().start_chat()

# Função pra adicionar a mensagem do usuário a conversação e retornar a resposta do modelo como texto
def call_ai(prompt):
    response = conversation.send_message(str(prompt))
    return response.text

# Função para checar se o sistema está conectado a internet
def internet():
    try:
        # Conecta ao server do google
        socket.create_connection(("8.8.8.8", 53))
        return True
    except OSError:
        return False
        
#####################
# QRunnables
#####################
"""
Para as ações de recomendação e adição que levam mais tempo por envolverem chamadas de API, criamos objetos do tipo QRunnable
que permitem que cada item e possível chamada de API sejam processados simultaneamente
"""
class AICommandRunnable(QRunnable):
    def __init__(self, item, mode, current_recommendations=None, current_library=None):
        self.item = item
        self.mode = mode
        self.current_recommendations = current_recommendations
        self.current_library = current_library
        super().__init__()

class Recommend(AICommandRunnable):
    def __init__(self, item, mode, current_recommendations):
        super().__init__(item, mode, current_recommendations=current_recommendations)

    def run(self):
        search_results = get_game_data(self.item, user_data["api_keys"]['GIANTBOMB']) if self.mode == 'game' else \
                         get_movie_data(self.item, user_data["api_keys"]['TMDB'])

        for idx, result in enumerate(search_results):

            # Alta prioridade == Primeiros resultados de cada pesquisa. Serão exibidos antes dos demais na aba de recomendações
            priority = 'High Priority' if idx == 0 else 'Low Priority'

            # TMDB usa a key 'title' para o nome dos filmes, GiantBomb usa a key 'name' para o nome dos jogos  
            name_key = 'name' if self.mode == 'game' else 'title'
            name = result.get(name_key)

            # Evita adicionar None ao dicionário ou sobrescrever items já adicionados
            if name is not None and name not in self.current_recommendations[priority]:

                # / Causa problemas ao tentar acessar o diretório para salvar a imagem
                if '/' in name:
                    name = " ".join(name.split('/')) # Substitui / por espaço no nome do item

                self.current_recommendations[priority][name] = result # Adiciona o nome do item associado aos seus dados
                cache[self.mode][name] = result # Adiciona o resultado ao cache

                # Salva a imagem do cada item das recomendações no cache caso não hja uma imagem com este título lá
                path_to_image = os.path.join(path_to_folder, f"caching/images_cache/{self.mode}/{name}.png")
                if not os.path.isfile(path_to_image): 
                    url_to_png(self.mode, result, name)

class Add(AICommandRunnable):
    def __init__(self, item, mode, current_library):
        super().__init__(item, mode, current_library=current_library)

    def run(self):
        # Tenta encontrar o item a ser adicionado a biblioteca no cache antes de chamar a API
        cached_data = cache[self.mode].get(self.item)

        # Caso ache o item no cache
        if cached_data is not None:
            name = self.item
            data = cached_data
        
        # Chama API caso contrário
        else:
            search_results = get_game_data(self.item, user_data["api_keys"]['GIANTBOMB']) if self.mode == 'game' else \
            get_movie_data(self.item, user_data["api_keys"]['TMDB'])
            data = search_results[0] if search_results else {} # Utiliza o primeiro resultado da pesquisa

            # TMDB usa a key 'title' para o nome dos filmes, GiantBomb usa a key 'name' para o nome dos jogos
            name_key = 'name' if self.mode == 'game' else 'title'
            name = data.get(name_key)
            
        if name is not None:
            # / Causa problemas ao tentar acessar o diretório para salvar a imagem
            if '/' in name:
                name = " ".join(name.split('/')) # Substitui / por espaço no nome do item

            # Estado base inicial de novo item na biblioteca: não jogado ou não assistido
            state = f'{'Unplayed' if self.mode == 'game' else 'Unwatched'}'

            # Adiciona o item a biblioteca associado a um dicionário com rating, estado e o dicionário de dados sobre o item
            self.current_library[name] = {'rating':'unrated', 'state': state, 'data': data}
            cache[self.mode][name] = data # Salva item e dados no cache

            # Salva imagem no cache
            path_to_image = os.path.join(path_to_folder, f"caching/images_cache/{self.mode}/{name}.png")
            if not os.path.isfile(path_to_image):
                url_to_png(self.mode, data, name)

class SettingsMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        parent.hbox.addWidget(self)
        self.hide()

        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 800)

        # Titulo
        self.title = QLabel("Definir chaves de API")
        self.layout.addWidget(self.title)

        # Campos no qual o usuário colocará as suas chaves para as API com labels para o que cada um faz
        self.labels = [QLabel(parent=self, text="GEMINI AI"), QLabel(parent=self, text="GIANT BOMB"), QLabel(parent=self, text="THE MOVIE DB")]
        self.key_fields = [QLineEdit(self), QLineEdit(self), QLineEdit(self)]

        for label, key_field, api_key_data in zip(self.labels, self.key_fields, user_data["api_keys"]):
            self.layout.addWidget(label)

            self.layout.addWidget(key_field)
            key_field.setText(user_data["api_keys"][api_key_data])
            key_field.textChanged.connect(self.update_api_keys)

        self.set_palette()

    def set_palette(self):
        self.title.setStyleSheet("color: white; font-weight:bold; font-size: 20px;")

        for label in self.labels:
            label.setStyleSheet("color: white; font-weight: bold;")

        for key_field in self.key_fields:
            key_field.setStyleSheet("color: white;")

    def setVisibility(self):
        self.setHidden(not self.isHidden())

    def update_api_keys(self):
        # Atualiza as chaves de api de acordo com os campos nas configurações
        for idx, api_key_data in enumerate(user_data["api_keys"]):
            user_data["api_keys"][api_key_data] = self.key_fields[idx].text()
        self.parent.reconfig_ai()


# Classe para pegar a resposta da IA e APIs em uma thread separada para evitar que o app congele equanto espera as respostas
class AiResponseThread(QThread):
    processing_request = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, formatted_prompt, current_library, current_recommendations, mode):
        super().__init__()
        self.mode = mode
        self.formatted_prompt = formatted_prompt
        self.current_library = current_library
        self.current_recommendations = current_recommendations
        self.threadpool = QThreadPool()

    def run(self):
        try:
            # Interrope o processo com uma exceção caso não seja possível verificar a conexão
            if not internet():
                raise Exception("Sem conexão à internet. Reinice o programa e tente novamente.")
            
            self.processing_request.emit("Aguardando resposta do modelo...")

            # Pega a resposta da gemini
            response = call_ai(self.formatted_prompt)

            # Processar resposta do modelo
            response_list = json.loads(response)
            if type(response_list) != list or False in [(type(item) == dict) for item in response_list]:
                raise Exception(f"Resposta formatada incorretamente: {response}")

            # Para cada comando na lista de respostas, processa os comandos
            for response_dictionary in response_list:
                command = response_dictionary.get("command", "")
                self.processing_request.emit(f"Processando comando {command}")

                if command == "Recommend":
                    self.current_recommendations['High Priority'], self.current_recommendations['Low Priority']  = {}, {}  # Limpa as recomendações
                    recommendations = response_dictionary.get("recommendations", [])

                    # Para cada recomendação retorna os resultados de busca de acordo com o modo do app
                    for item in recommendations:
                        recommending = Recommend(item, self.mode, self.current_recommendations)
                        self.threadpool.start(recommending)
                        
                elif command == "Add":
                    additions = response_dictionary.get("additions", [])
                    for item in additions:

                        adding = Add(item, self.mode, self.current_library)
                        self.threadpool.start(adding)          
                                
                elif command == "Set State":
                    new_states = response_dictionary.get("new_states", {})
                    for item, state in new_states.items():
                        
                        print(self.current_library.keys())
                        if item in self.current_library:
                            self.current_library[item]['state'] = state

                elif command == "Set Rating":
                    new_ratings = response_dictionary.get("new_ratings", {})
                    for item, rating in new_ratings.items():
                        
                        print(self.current_library.keys())
                        if item in self.current_library:
                            self.current_library[item]['rating'] = rating

                elif command == "Remove":

                    removals = response_dictionary.get("removals", [])
                    for item in removals:

                        if item in self.current_library:
                            del self.current_library[item]

            self.threadpool.waitForDone()
                
            self.finished.emit(response)

        except Exception as e:
            self.error.emit(str(e))

from library_region import LibaryRegion
from ai_recommendations_region import AiRecommendationsRegion

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

    def reconfig_ai(self):
        genai.configure(api_key=user_data['api_keys']['GOOGLE'])

    def closeEvent(self, event):
        # Salva dados de usuário
        with open(user_data_path, 'w') as file:
            json.dump(user_data, file)

        # Salva o cache
        with open(api_cache_path, 'w') as file:
            json.dump(cache, file)

        event.accept()

if __name__ == "__main__":
    App = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(App.exec())







    
