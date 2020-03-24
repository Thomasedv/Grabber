import sys

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QLineEdit


class LineEdit(QLineEdit):
    def __init__(self, parent=None):
        super(LineEdit, self).__init__(parent)
        self.text_focus = False
        # Clicking automatically selects all text, this allows clicks and drag
        # to highlight part of a url better
        self.clicklength = QTimer()
        self.clicklength.setSingleShot(True)
        self.clicklength.setTimerType(Qt.PreciseTimer)

    def mousePressEvent(self, e):
        if not self.text_focus:
            self.clicklength.start(120)
            self.text_focus = True
        else:
            super(LineEdit, self).mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if self.clicklength.isActive():
            self.selectAll()
        super(LineEdit, self).mouseReleaseEvent(e)

    def focusOutEvent(self, e):
        super(LineEdit, self).focusOutEvent(e)
        self.text_focus = False


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    Checkbox = LineEdit()
    Checkbox.show()

    app.exec_()
