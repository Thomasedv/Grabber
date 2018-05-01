from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QAction, QMenu, QComboBox


class DropDown(QComboBox):
    deleteItem = pyqtSignal()

    def __init__(self, parent=None):
        super(DropDown, self).__init__(parent=parent)

        self.setDuplicatesEnabled(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

    def contextMenu(self, event):
        menu = QMenu(self)

        delete_action = QAction('Delete profile')
        delete_action.triggered.connect(self.delete_option)
        menu.addAction(delete_action)

        menu.exec(QCursor.pos())

    def delete_option(self):
        self.deleteItem.emit()
