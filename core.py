import os, json
# Caminho para o diretório onde este arquivo está, este arquivo deve ficar no mesmo diretório que todos os outros que usam essa variável ###
path_to_folder = os.path.dirname(os.path.abspath(__file__))

# Paleta de cores da GUI ###
app_color_palette = {
    'dark': {'movie':"#280606", 'game':"#070F2B"},
    'dark-medium': {'movie':"#541A1A", 'game':"#1B1A55"},
    'medium': {'movie':"#BE3144", 'game':"#535C91"},
    'light': {'movie':"#EF6E23", 'game':"#9290C3"}
}

# Checa a existência das pastas de caching ###
# Diretórios a serem criados
directories = [
    'caching',
    'caching/images_cache',
    'caching/images_cache/game',
    'caching/images_cache/movie'
]

# Cria os diretórios caso não existam
for dir_name in directories:
    dir_path = os.path.join(path_to_folder, dir_name)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path, exist_ok=True)


# Carregar user data ###
user_data_path = os.path.join(path_to_folder, 'user_data.json')
try:
    with open(user_data_path, 'r') as file:
        user_data = json.load(file)

except FileNotFoundError:
    user_data = {'movie_library': {}, 'game_library': {}, 
                'movie_recommendations': {'High Priority': {}, 'Low Priority': {}}, 
                'game_recommendations': {'High Priority': {}, 'Low Priority': {}},
                'api_keys': {'GOOGLE':"", 'GIANTBOMB':"", 'TMDB':""}}

# Carregar dados de API ###
api_cache_path = os.path.join(path_to_folder, 'caching/api_data_cache.json')
try:
    with open('caching/api_data_cache.json', 'r') as file:
        cache = json.load(file)

except FileNotFoundError:
    cache = {'game':{}, 'movie':{}}


