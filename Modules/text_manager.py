from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel

from utils.utilities import FONT_CONSOLAS


class TextTab(QW):
    def __init__(self, parent=None):
        """Handles taxt files for batch downloads from a list of links."""
        super(TextTab, self).__init__(self, parent=parent)

        self.textedit = QTextEdit()
        self.textedit.setObjectName('TextFileEdit')
        self.textedit.setFont(FONT_CONSOLAS)

        # Create load button and label.
        self.label = QLabel('Add videos to textfile:')
        self.loadButton = QPushButton('Load file')
        self.saveButton = QPushButton('Save file')
        self.saveButton.setDisabled(True)

        # Layout
        # Create horizontal layout.
        self.QH = QHBoxLayout()

        # Filling horizontal layout
        self.QH.addWidget(self.tab3_label)
        self.QH.addStretch(1)
        self.QH.addWidget(self.tab3_loadButton)
        self.QH.addWidget(self.tab3_saveButton)

        # Horizontal layout with a textedit and a button.
        self.VB = QVBoxLayout()
        self.VB.addLayout(self.tab3_QH)
        self.VB.addWidget(self.tab3_textedit)
        self.setLayout(self.VB)
