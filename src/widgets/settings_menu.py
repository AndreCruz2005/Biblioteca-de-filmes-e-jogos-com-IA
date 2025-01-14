from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from core import user_data

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
            key_field.returnPressed.connect(self.update_api_keys)
            key_field.editingFinished.connect(self.update_api_keys)

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