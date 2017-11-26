from PyQt5.QtCore import pyqtSignal, pyqtSlot, QEvent, QObject
from PyQt5.QtWidgets import QTabWidget


class Tabwidget(QTabWidget):
    onclose = pyqtSignal()
    LetClose = False
    gotfocus = pyqtSignal()

    def __init__(self):
        super(Tabwidget, self).__init__()

        self.installEventFilter(self)

    def eventFilter(self, QObject, Event):
        if Event.type() == QEvent.WindowActivate:
            self.gotfocus.emit()
            return True
        return False

    def focusInEvent(self, *args, **kwargs):
        self.gotfocus.emit()
        super(Tabwidget, self).focusInEvent(*args, **kwargs)

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