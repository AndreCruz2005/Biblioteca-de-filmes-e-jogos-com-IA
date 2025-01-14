import os, socket, json
import google.generativeai as genai
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from api_calling import get_game_data, get_movie_data, url_to_png
from core import user_data, cache, path_to_src

# Inicializa Gemini
def reconfig_ai():
    genai.configure(api_key=user_data['api_keys']['GOOGLE'])

reconfig_ai()

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
    instructions_path = os.path.join(path_to_src, 'model_instructions.txt')

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
                path_to_image = os.path.join(path_to_src, f"caching/images_cache/{self.mode}/{name}.png")
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
            path_to_image = os.path.join(path_to_src, f"caching/images_cache/{self.mode}/{name}.png")
            if not os.path.isfile(path_to_image):
                url_to_png(self.mode, data, name)


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