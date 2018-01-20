import re

from PyQt5.QtWidgets import QPushButton, QLabel, QLineEdit, \
    QGridLayout, QDialog


class Dialog(QDialog):

    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        self.option = QLineEdit()

        self.label = QLabel('Insert option:')
        self.ok_button = QPushButton('Ok', self)
        self.ok_button.setDisabled(True)
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.clicked.connect(self.reject)

        layout = QGridLayout(self)
        layout.addWidget(self.label, 0, 0, 1, 2)
        layout.addWidget(self.option, 1, 0, 1, 2)

        layout.addWidget(self.ok_button, 2, 0)
        layout.addWidget(self.cancel_button, 2, 1)

        self.option.textChanged.connect(self.input_check)
        self.setFixedHeight(self.sizeHint().height())
        self.option.setFocus()

    def input_check(self):
        test = re.match(r'(^ *$)', self.option.text())
        if test is not None:
            self.ok_button.setDisabled(True)
        else:
            self.ok_button.setDisabled(False)
