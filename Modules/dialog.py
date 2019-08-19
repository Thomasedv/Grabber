import re

from PyQt5.QtWidgets import QPushButton, QLabel, QLineEdit, \
    QGridLayout, QDialog

from utils.utilities import color_text


class Dialog(QDialog):

    def __init__(self, parent=None, name: str = '', description: str = '', allow_empty=False):
        super(Dialog, self).__init__(parent)
        self.option = QLineEdit()
        self.allow_empty = allow_empty
        self.label = QLabel(color_text('Insert option:', 'limegreen'))
        self.name_label = QLabel(color_text(name + ':', 'limegreen'))
        self.tooltip = QLabel(description)
        self.ok_button = QPushButton('Ok', self)
        self.ok_button.setFixedSize(self.ok_button.sizeHint())
        self.ok_button.setDisabled(not allow_empty)
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.setFixedSize(self.cancel_button.sizeHint())
        self.cancel_button.clicked.connect(self.reject)

        layout = QGridLayout(self)
        layout.addWidget(self.name_label, 0, 0, 1, 3)
        layout.addWidget(self.tooltip, 1, 0, 1, 3)

        layout.addWidget(self.label, 2, 0, 1, 3)
        layout.addWidget(self.option, 3, 0, 1, 3)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 0)
        layout.setColumnStretch(2, 0)
        layout.addWidget(self.ok_button, 4, 1)
        layout.addWidget(self.cancel_button, 4, 2)

        self.option.textChanged.connect(self.input_check)
        self.setFixedHeight(self.sizeHint().height())
        self.setFixedWidth(self.sizeHint().width())
        self.option.setFocus()

    def input_check(self):
        if not self.allow_empty:
            test = re.match(r'(^ *$)', self.option.text())
            if test is not None:
                self.ok_button.setDisabled(True)
            else:
                self.ok_button.setDisabled(False)
