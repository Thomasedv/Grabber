from PyQt5.QtCore import pyqtSlot, pyqtSignal, QEvent
from PyQt5.QtWidgets import QMainWindow


class MainWindow(QMainWindow):
    """Top level window, custom close method to ensure safe exit."""
    gotfocus = pyqtSignal()
    resizedByUser = pyqtSignal()
    onclose = pyqtSignal()

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.let_close = False

        self.installEventFilter(self)

    def eventFilter(self, widget, event):
        if event.type() == QEvent.WindowActivate:
            self.gotfocus.emit()
            return True
        return False

    def resizeEvent(self, resize_event):
        self.resizedByUser.emit()
        super().resizeEvent(resize_event)

    def closeEvent(self, event):
        self.onclose.emit()
        if self.let_close:
            event.accept()
        else:
            event.ignore()

    @pyqtSlot()
    def closeE(self):
        self.let_close = True
        self.close()
