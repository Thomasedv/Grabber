from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QTextBrowser, QCheckBox, \
    QHBoxLayout, QVBoxLayout, QListWidget

from Modules.dropdown_widget import DropDown
from Modules.lineedit import LineEdit
from utils.utilities import SettingsClass


class MainTab(QWidget):

    def __init__(self, settings: SettingsClass, parent=None):
        super().__init__(parent=parent)

        # Starts the program (Youtube-dl)
        self.start_btn = QPushButton('Download')
        self.start_btn.clicked.connect(self.start_button_timer)
        # stops the program
        self.stop_btn = QPushButton('Abort')
        # Closes window (also stops the program)
        self.close_btn = QPushButton('Close')

        # Label and lineedit creation. Line edit for acception youtube links as well as paramters.
        self.label = QLabel("Url: ")
        self.lineedit = LineEdit()

        self.profile_label = QLabel('Current profile:')

        self.profile_dropdown = DropDown(self)
        self.profile_dropdown.setFixedWidth(100)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.start_btn.setDisabled(False))

        if settings.profiles:
            for profile in settings.profiles:
                self.profile_dropdown.addItem(profile)
            current_profile = settings.user_options['current_profile']
            if current_profile:
                self.profile_dropdown.setCurrentText(current_profile)
            else:
                self.profile_dropdown.addItem('Custom')
                self.profile_dropdown.setCurrentText('Custom')
        else:
            self.profile_dropdown.setDisabled(True)
            self.profile_dropdown.addItem('None')

        self.queue_label = QLabel('Items in queue:   0')

        # TextEdit creation, for showing status messages, and the youtube-dl output.
        self.textbrowser = QTextBrowser()

        self.textbrowser.setAcceptRichText(True)
        self.textbrowser.setOpenExternalLinks(True)
        self.textbrowser.setContextMenuPolicy(Qt.NoContextMenu)

        # Adds welcome message on startup.
        self.textbrowser.append('Welcome!\n\nAdd video url, or load from text file.')
        # self.edit.append('<a href="URL">Showtext</a>') Learning purposes.

        self.process_list = QListWidget(self)
        self.process_list.setSelectionMode(QListWidget.NoSelection)
        self.process_list.setFocusPolicy(Qt.NoFocus)
        self.process_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Start making checkbutton for selecting downloading from text file mode.
        self.checkbox = QCheckBox('Download from text file.')

        # Contains, start, abort, close buttons, and a stretch to make buttons stay on the correct side on rezise.
        self.QH = QHBoxLayout()

        self.QH.addStretch(1)
        self.QH.addWidget(self.start_btn)
        self.QH.addWidget(self.stop_btn)
        self.QH.addWidget(self.close_btn)

        # Horizontal layout 2, contains label and LineEdit. LineEdit stretches horizontally by default.
        self.QH2 = QHBoxLayout()

        self.QH2.addWidget(self.label)
        self.QH2.addWidget(self.lineedit)

        # Line where Checkbox and queue label is.
        self.QH3 = QHBoxLayout()
        self.QH3.addWidget(self.checkbox)
        self.QH3.addStretch(1)
        self.QH3.addWidget(self.profile_label)
        self.QH3.addWidget(self.profile_dropdown)
        # self.QH3.addWidget(self.queue_label)
        #
        # TODO: Remove queue label and things related

        # Creates vertical box for tab1.
        self.QV = QVBoxLayout()

        # Adds horizontal layouts, textbrowser and checkbox to create tab1.
        self.QV.addLayout(self.QH2)
        self.QV.addLayout(self.QH3)

        # self.QV.addWidget(self.textbrowser, 1)
        self.QV.addWidget(self.process_list)
        self.QV.addLayout(self.QH)

        self.setLayout(self.QV)

    def start_button_timer(self, state):
        self.start_btn.setDisabled(True)
        print(state)
        print(self.start_btn.isEnabled())
        if not state:
            self.timer.start(1000)
            print('t')


if __name__ == '__main__':
    # Only visual aspects work here!!
    import sys
    from PyQt5.QtWidgets import QApplication
    from utils.filehandler import FileHandler

    app = QApplication(sys.argv)
    gui = MainTab(FileHandler().load_settings())
    gui.show()
    app.exec_()
