from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QTextBrowser, QCheckBox, \
    QHBoxLayout, QVBoxLayout

from Modules.dropdown_widget import DropDown
from Modules.lineEdit import LineEdit


class MainTab(QWidget):

    def __init__(self, settings, parent=None):
        super().__init__(parent=parent)

        # Starts the program (Youtube-dl)
        self.start_btn = QPushButton('Download')
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

        if settings['Profiles']:
            for profile in settings['Profiles'].keys():
                self.profile_dropdown.addItem(profile)
            current_profile = settings['Other stuff']['current_profile']
            self.profile_dropdown.setCurrentText(current_profile if current_profile else 'Custom')
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

        # Start making checkbutton for selecting downloading from text file mode.
        self.checkbox = QCheckBox('Download from text file.')

        ## Layout tab 1.

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
        self.QH3.addWidget(self.queue_label)

        # Creates vertical box for tab1.
        self.QV = QVBoxLayout()

        # Adds horizontal layouts, textbrowser and checkbox to create tab1.
        self.QV.addLayout(self.QH2)
        self.QV.addLayout(self.QH3)
        self.QV.addWidget(self.textbrowser, 1)
        self.QV.addLayout(self.QH)

        self.setLayout(self.QV)


if __name__ == '__main__':
    # Only visual aspects work here!!
    import sys
    from PyQt5.QtWidgets import QApplication
    from utils.utilities import get_base_settings

    app = QApplication(sys.argv)
    gui = MainTab(get_base_settings())
    gui.show()
    app.exec_()
