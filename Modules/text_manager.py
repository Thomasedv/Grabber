from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QWidget

from utils.utilities import FONT_CONSOLAS


class TextTab(QWidget):

    def __init__(self, parent=None):
        """Handles text files for batch downloads from a list of links."""

        super().__init__(parent=parent)
        # Denotes if the textfile is saved.
        self.SAVED = True

        self.textedit = QTextEdit()
        self.textedit.setObjectName('TextFileEdit')
        self.textedit.setFont(FONT_CONSOLAS)

        # Create load button and label.
        self.label = QLabel('Add videos to textfile:')
        self.loadButton = QPushButton('Load file')
        self.saveButton = QPushButton('Save file')
        self.saveButton.setDisabled(True)

        self.textedit.textChanged.connect(self.enable_saving)

        # Layout
        # Create horizontal layout.
        self.QH = QHBoxLayout()

        # Filling horizontal layout
        self.QH.addWidget(self.label)
        self.QH.addStretch(1)
        self.QH.addWidget(self.loadButton)
        self.QH.addWidget(self.saveButton)

        # Horizontal layout with a textedit and a button.
        self.VB = QVBoxLayout()
        self.VB.addLayout(self.QH)
        self.VB.addWidget(self.textedit)
        self.setLayout(self.VB)

    def enable_saving(self):
        self.saveButton.setDisabled(False)
        self.SAVED = False
