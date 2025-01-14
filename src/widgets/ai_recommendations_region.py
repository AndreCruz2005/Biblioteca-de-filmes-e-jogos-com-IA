from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from core import app_color_palette, path_to_src
import os, random, sys

# Região à direita no app, incluí caixa de recomendações e a caixa de input do usuário para IA
class AiRecommendationsRegion(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {app_color_palette['dark'][parent.mode]}") 
        self.parent = parent
        parent.hbox.addWidget(self, stretch=4)
        
        # Layout do Widget
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Cabeçalho pra aréa de recomendações
        self.topbar = QWidget(self)
        self.layout.addWidget(self.topbar, stretch=1)
        self.topbar_layout = QHBoxLayout(self.topbar)

        # Botão clear para deletar todas a recomendações
        self.clear_button = QPushButton(self)
        self.clear_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.clear_button.setText("APAGAR")
        self.clear_button.pressed.connect(self.clear_recommendations)
        self.topbar_layout.addWidget(self.clear_button, stretch=1)

        # Botão load more para carregar mover recomendações da low priority para high priority
        self.load_button = QPushButton(self)
        self.load_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.load_button.setText("MOSTRAR\nMAIS")
        self.load_button.pressed.connect(self.load_recommendations)
    
        # Título da área de recomendações
        self.title = QLabel(self)
        self.title.setAlignment(Qt.AlignCenter)
        self.topbar_layout.addWidget(self.title, stretch=5)

        # Adiciona elementos do layout do cabeçalho
        self.topbar_layout.addWidget(self.clear_button, stretch=1)
        self.topbar_layout.addWidget(self.title, stretch=5)
        self.topbar_layout.addWidget(self.load_button, stretch=1)

        # Scroll area para conter as recomendações
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setStyleSheet("border: none;")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.layout.addWidget(self.scroll_area, stretch=10)

        # Widget para exibir as recomendações
        self.scroll_content = QWidget(self)
        self.scroll_content.setStyleSheet("border: none;")
        self.scroll_area.setWidget(self.scroll_content)

        # Grid contendo recomendações
        self.recommendations_grid = QGridLayout(self.scroll_content)

        # Entrada de texto onde o usuário digitará sua mensagem para a IA
        self.user_chat_input = QLineEdit(self)
        self.user_chat_input.setPlaceholderText("Peça à IA recomendações ou que altere sua biblioteca")
        self.user_chat_input.returnPressed.connect(parent.ai_response) # Chama a função da MainWindow ai_response() ao apertar enter
        self.user_chat_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.user_chat_input, stretch=1)

        self.palette_setting(self.parent.mode)
        self.update()

    def palette_setting(self, mode):
        self.setStyleSheet(f"background-color: {app_color_palette['dark'][mode]}")

        # User input
        self.user_chat_input.setStyleSheet(f"border-top: 5px solid {app_color_palette['medium'][mode]};"
                                        f"color: {app_color_palette['light'][mode]};"
                                        "font-size: 20px")
        
        # Scroll area
        self.scroll_area.setStyleSheet(f"border-top: 5px solid {app_color_palette['medium'][mode]}")

        # Título
        self.title.setText(f"{'JOGOS' if mode == 'game' else 'FILMES'} RECOMENDADOS")
        self.title.setStyleSheet(f"color: {app_color_palette['medium'][mode]}; font-size: 30px; font-weight: bold;")

        # Clear button
        self.clear_button.setStyleSheet(f"background-color: {app_color_palette['medium'][mode]};"
                                        f"color: {app_color_palette['light'][mode]};"
                                        f"font-size: 15px; border: none; font-weight: bold;")
        
        # Load button
        self.load_button.setStyleSheet(f"background-color: {app_color_palette['medium'][mode]};"
                                        f"color: {app_color_palette['light'][mode]};"
                                        f"font-size: 15px; border: none; font-weight: bold;")
        
    def update(self):
        # Apaga todos os items do widget de recomendações mas não apaga o layout
        for child in self.scroll_content.children():
            if type(child) != QGridLayout:
                child.deleteLater()

        # Número de items por fileira da grid
        items_per_row = 4  

        # Pega o modo e recomendações de acordo com o modo da main window
        mode = self.parent.mode
        recomendations = self.parent.game_recommendations if mode == 'game' else self.parent.movie_recommendations

        for idx, key in enumerate(recomendations['High Priority']):
            item_displayer = RecommendedItemDisplayer(self.scroll_content, mode)
            data = recomendations['High Priority'][key]

            image_path = os.path.join(path_to_src, f'caching/images_cache/{mode}/{key}.png')
            item_displayer.image_thumb.setPixmap(QPixmap(image_path))
            item_displayer.title.setText(key)

            # 4 Items por coluna
            rows = idx//items_per_row
            collums = idx%items_per_row
            self.recommendations_grid.addWidget(item_displayer, rows, collums)

        # Preenche a grid de recomendações com item_displayers invisíveis de forma que haja pelo menos 4 fileiras para melhor formatação
        recs_size = len(recomendations)
        mininum_for_4_rows = max((items_per_row * 3 + 1) - recs_size, 0)
        for i in range(recs_size, mininum_for_4_rows + recs_size):
            filler = RecommendedItemDisplayer(self.scroll_content, mode)
            filler.make_invisible()
            self.recommendations_grid.addWidget(filler, i//items_per_row, i%items_per_row)

    def clear_recommendations(self):
        # Excluí todas as recomendações do modo atual quando o usuário aperta o botão "CLICK"
        recs = self.parent.game_recommendations if self.parent.mode == 'game' else self.parent.movie_recommendations
        recs['High Priority'], recs['Low Priority'] = {}, {}
        self.update()

    def load_recommendations(self):
        # Move até 6 recomendações aleatórias da low priority pra high priority quando o usuário clica o botão "LOAD MORE"
        recs = self.parent.game_recommendations if self.parent.mode == 'game' else self.parent.movie_recommendations

        amount_to_move = min(len(recs['Low Priority']), 6) 
        new_recs = random.sample([keys for keys in recs['Low Priority']], k=amount_to_move)

        for key in new_recs:
            recs['High Priority'][key] = recs['Low Priority'][key]
            del recs['Low Priority'][key]

        self.update()


# Classe das caixas na área de recomendações
class RecommendedItemDisplayer(QWidget):
    def __init__(self, parent, mode):
        super().__init__(parent)
        self.setFixedSize(143, 250)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Imagem
        self.image_thumb = QLabel(self)
        self.image_thumb.setScaledContents(True)
        self.image_thumb.setStyleSheet(f'border: 2px solid {app_color_palette['medium'][mode]}')
        self.image_thumb.setAlignment(Qt.AlignCenter)

        # Título
        self.title = QLabel(self)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet(f"font-size:15px; color:{app_color_palette['light'][mode]};background-color:{app_color_palette['medium'][mode]};font-weight:bold;")

        self.layout.addWidget(self.image_thumb)
        self.layout.addWidget(self.title)

    def make_invisible(self):
        self.image_thumb.setStyleSheet("background-color: transparent; border: none;")
        self.title.setStyleSheet("background-color: transparent; border: none;")
