from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QTabWidget


class Tabwidget(QTabWidget):
    onclose = pyqtSignal()
    LetClose = False

    def __init__(self):
        super().__init__()

    def closeEvent(self, event):
        self.onclose.emit()
        if self.LetClose:
            event.accept()
        else:
            event.ignore()

    @pyqtSlot()
    def closeE(self):
        self.LetClose = True
        self.close()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QPushButton

    app = QApplication(sys.argv)
    Tab = Tabwidget()
    CloseButton = QPushButton('Force Close')
    CloseButton.clicked.connect(Tab.closeE)
    Tab.addTab(CloseButton, 'Test')

    Tab.show()

    app.exec_()