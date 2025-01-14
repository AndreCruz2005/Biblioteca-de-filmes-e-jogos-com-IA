from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from core import app_color_palette, path_to_src, os

# Região à esquerda do app, incluí a caixa da biblioteca e os botões para mudar de modo
class LibaryRegion(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        parent.hbox.addWidget(self, stretch=8)

        # Cabeçalho da area da biblioteca onde ficarão os botões para trocar o modo
        # e o botão de configurações
        self.library_topbar = QWidget(self)
        self.library_topbar_buttons = {} # Dicionário para armazenar os widgets de cada botão

        self.library_topbar_layout = QHBoxLayout(self.library_topbar)
        self.library_topbar_layout.setSpacing(0)
        self.library_topbar_layout.setContentsMargins(0, 0, 0, 0)

        # Cria os dois botões de trocar o modo junto na esquerda do layout do cabeçalho
        for mode_name in ('GAME', 'MOVIE'):
            if mode_name != '': # Botões
                button = QPushButton(self.library_topbar)
                button.setText("JOGOS" if  mode_name == 'GAME' else "FILMES")
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

                # Conecta cada botão a função switch mode enviado o nome como parâmetro
                button.pressed.connect(lambda mode_name=button.text()[:-1]: self.switch_mode(mode_name))
                self.library_topbar_layout.addWidget(button, stretch=1)
                self.library_topbar_buttons[mode_name] = button

        # Label com o título da biblioteca na direita do cabeçalho
        self.title = QLabel(self)
        self.title.setAlignment(Qt.AlignCenter)
        self.library_topbar_layout.addWidget(self.title, stretch=7)

        # Botão de configurações
        self.settings = QPushButton(self)
        self.settings.setIconSize(QSize(84, 84))
        self.settings.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.settings.clicked.connect(self.parent.settings_menu.setVisibility)
        self.library_topbar_layout.addWidget(self.settings, stretch=1)

        # Adiciona o cabeçalho ao layout com stretch de 1
        self.layout.addWidget(self.library_topbar, stretch=1)
        
        # Cria a area de scroll onde ficarão os filmes e jogos e adiciona ao layout stretch de 8
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.layout.addWidget(self.scroll_area, stretch=8)

        # Widget dentro do scroll com os filmes e jogos
        self.library_content = QWidget(self)
        self.library_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.scroll_area.setWidget(self.library_content)
        self.libary_grid = QGridLayout(self.library_content) # Grid, cada item na grid será os filmes e jogos

        self.palette_setting(self.parent.mode)
        self.update()

    def switch_mode(self, button_text):
        # Alterna modo do app entre jogos e filmes ao clicar os botões de cada modo na library_region
        if button_text == self.parent.mode.upper():
            return # Retorna quando apertado o botão do modo já selecionado
        
        self.parent.mode = 'game' if self.parent.mode != 'game' else 'movie'

        # Palette changes
        self.parent.setStyleSheet(f"background-color: {app_color_palette['dark-medium'][self.parent.mode]}")
        self.palette_setting(self.parent.mode)
        self.parent.ai_recommendation_region.palette_setting(self.parent.mode)

        self.update()
        self.parent.ai_recommendation_region.update()

    def remove_item(self, item):
        library = self.parent.game_library if self.parent.mode == 'game' else self.parent.movie_library
        if item in library:
            del library[item]
            self.update()

    def palette_setting(self, mode):
        # Scroll area
        self.scroll_area.setStyleSheet(f"border: 3px solid {app_color_palette['medium'][mode]}")

        # Botões de troca de modo
        for mode_name in ('GAME', 'MOVIE'):
            button = self.library_topbar_buttons[mode_name]
            button.setStyleSheet(
                    f"background-color: {app_color_palette['medium' if button.text() == {'game':'JOGOS', 'movie':'FILMES'}[mode] else 'dark-medium'][mode]}; "
                    f"border-top: 3px solid {app_color_palette['medium'][mode]}; border-left: 5px solid {app_color_palette['medium'][mode]}; border-right: 3px solid {app_color_palette['medium'][mode]};"
                    f"color: {app_color_palette['light'][mode]}; "
                    f"font-weight: bold;"
                    f"font-size: 25px;"
                )
            
        # Title
        self.title.setStyleSheet(f"color: {app_color_palette['light'][mode]}; font-size: 48px; font-weight: bold;")
        self.title.setText(f'MINHA BIBLIOTECA DE {"JOGOS" if self.parent.mode.upper() == 'GAME' else 'FILMES'}')

        # Botão de configurações
        self.settings.setStyleSheet("border: none;")
        self.settings.setIcon(QIcon(os.path.join(path_to_src, "img", "settings_game.png") if self.parent.mode == "game" else 
                        os.path.join(path_to_src, "img", "settings_movie.png")))
    
    def update(self):
        # Função para atualizar os filmes e jogos exibidos
        # Apaga todos os items do widget da biblioteca resetando-a, mas não apaga o layout
        for child in self.library_content.children():
            if type(child) != QGridLayout:
                child.deleteLater()

        # Pega o modo atual e o dicionário da biblioteca deste modo na MainWindow
        mode = self.parent.mode
        library = self.parent.game_library if mode == 'game' else self.parent.movie_library

        # Número de items por fileira na grid
        items_per_row = 7  

        # Itera sob o dicionário da biblioteca
        for idx, item in enumerate(library):
            # Extrai o dicionário e o campo de data do diconário
            item_dict = library[item]
            data = item_dict['data']

            # Cria o objeto para exibir este item na biblioteca
            item_displayer = LibraryItemDisplayer(self.library_content, mode, data=data)
            
            # Configura os elementos do slot da grid de acordo com os dados do item da biblioteca
            image_path = os.path.join(path_to_src, f'caching/images_cache/{mode}/{item}.png')
            item_displayer.image_thumb.setPixmap(QPixmap(image_path))
            item_displayer.title.setText(item)
            item_displayer.rating_bar.setText(str(item_dict['rating']))
            item_displayer.status_bar.setText(item_dict['state'])

            # Conecta o botão de remoção do item
            item_displayer.removal_button.clicked.connect(lambda _, name=item: self.remove_item(name))

            # Adiciona os items a grid de modo que haja 7 items por fileira
            rows = idx//items_per_row
            collums = idx%items_per_row
            self.libary_grid.addWidget(item_displayer, rows, collums)

        # Preenche a grid da biblioteca com itemdisplayers invisíveis de forma que haja pelo menos 3 fileiras para melhor formatação
        library_size = len(library)
        mininum_for_3_rows = max((items_per_row * 2 + 1) - library_size, 0)

        for i in range(library_size, mininum_for_3_rows+library_size):
            filler = LibraryItemDisplayer(self.library_content, mode)
            filler.make_invisible()
            self.libary_grid.addWidget(filler, i//items_per_row, i%items_per_row)

# Classe para mostrar um item na biblioteca com sua imagem, nome, rating e status
class LibraryItemDisplayer(QWidget):
    def __init__(self, parent, mode, data=None):
        super().__init__(parent)
        self.setFixedSize(166, 280)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Imagem
        self.image_thumb = QLabel(self)
        self.image_thumb.setAlignment(Qt.AlignCenter)
        self.image_thumb.setScaledContents(True)

        # Botão para remover item
        self.removal_button = QPushButton(self.image_thumb)
        self.removal_button.setIcon(QIcon(os.path.join(path_to_src, "img", "remove_button.png")))
        self.removal_button.setStyleSheet("background-color: transparent; border: none;")
        self.removal_button.move(139, 162)

        # Nome
        self.title = QLabel(self)
        self.title.setStyleSheet(f"font-size:15px;color:{app_color_palette['light'][mode]};background-color:{app_color_palette['medium'][mode]};font-weight:bold;")
        self.title.setAlignment(Qt.AlignCenter)

        # Rating
        self.rating_bar = QLabel(self)
        self.rating_bar.setStyleSheet(f"font-size:15px;color:{app_color_palette['light'][mode]};background-color:{app_color_palette['medium'][mode]}")
        self.rating_bar.setAlignment(Qt.AlignCenter)

        # Status
        self.status_bar = QLabel(self)
        self.status_bar.setStyleSheet(f"font-size:15px;color:{app_color_palette['light'][mode]};background-color:{app_color_palette['medium'][mode]}")
        self.status_bar.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.image_thumb)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.rating_bar)
        self.layout.addWidget(self.status_bar)

    def make_invisible(self):
        self.image_thumb.setStyleSheet("background-color: transparent; border: none;")
        self.removal_button.hide()
        self.title.setStyleSheet("background-color: transparent; border: none;")
        self.rating_bar.setStyleSheet("background-color: transparent; border: none;")
        self.status_bar.setStyleSheet("background-color: transparent; border: none;")