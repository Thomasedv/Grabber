import typing

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QCheckBox, \
    QHBoxLayout, QVBoxLayout, QListWidget

from Modules.download_element import ProcessListItem
from Modules.dropdown_widget import DropDown
from Modules.lineedit import LineEdit
from utils.utilities import SettingsClass


class ProcessList(QListWidget):
    """ Subclass to tweak resizing of widget. Holds ProcessListItems. """

    def __init__(self, *args, **kwargs):
        super(ProcessList, self).__init__(*args, **kwargs)
        self.verticalScrollBar().setObjectName('main')

    def resizeEvent(self, a0):
        super(ProcessList, self).resizeEvent(a0)

        # Ensure the length of long labels are not too long at small window sizes
        for item in self.iter_items():
            if self.verticalScrollBar().isVisible():
                padding = self.verticalScrollBar().width()
            else:
                padding = 0
            item.info_label.setFixedWidth(self.width() - 18 - padding)

    def iter_items(self) -> typing.Iterator[ProcessListItem]:
        yield from [self.itemWidget(self.item(i)) for i in range(self.count())]

    def clear(self) -> None:
        """ Only removed finished downloads from display"""
        for item in self.iter_items():
            if not item.is_running():
                self.takeItem(self.indexFromItem(item.slot).row())


class MainTab(QWidget):
    """ QWidget for starting downloads, swapping profiles, and showing progress"""
    def __init__(self, settings: SettingsClass, parent=None):
        super().__init__(parent=parent)

        # Queue download
        self.start_btn = QPushButton('Download')
        # Enables start btn after some time
        self.start_btn.clicked.connect(self.start_button_timer)
        # Stops one or all downloads
        self.stop_btn = QPushButton('Abort')
        # Closes the program
        self.close_btn = QPushButton('Close')

        self.clear_btn = QPushButton('Clear')
        self.label = QLabel("Url: ")

        self.url_input = LineEdit()

        self.profile_label = QLabel('Current profile:')

        self.profile_dropdown = DropDown(self)
        self.profile_dropdown.setFixedWidth(100)

        # Setup for startbutton timer
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.start_btn.setDisabled(False))

        # Populate profile selector
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

        # Holds entries for with queue downloads
        self.process_list = ProcessList(self)

        self.process_list.setSelectionMode(QListWidget.NoSelection)
        self.process_list.setFocusPolicy(Qt.NoFocus)
        self.process_list.setVerticalScrollMode(self.process_list.ScrollPerPixel)
        self.process_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Start making checkbutton for selecting downloading from text file mode.
        self.checkbox = QCheckBox('Download from text file.')

        # Contains, start, abort, close buttons, and a stretch to make buttons stay on the correct side on rezise.
        self.button_bar = QHBoxLayout()

        self.button_bar.addWidget(self.clear_btn)
        self.button_bar.addStretch(1)
        self.button_bar.addWidget(self.start_btn)
        self.button_bar.addWidget(self.stop_btn)
        self.button_bar.addWidget(self.close_btn)

        self.url_bar = QHBoxLayout()
        self.url_bar.addWidget(self.label)
        self.url_bar.addWidget(self.url_input)

        self.profile_bar = QHBoxLayout()
        self.profile_bar.addWidget(self.checkbox)
        self.profile_bar.addStretch(1)
        self.profile_bar.addWidget(self.profile_label)
        self.profile_bar.addWidget(self.profile_dropdown)

        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.addLayout(self.url_bar)
        self.vertical_layout.addLayout(self.profile_bar)
        self.vertical_layout.addWidget(self.process_list)
        self.vertical_layout.addLayout(self.button_bar)

        self.setLayout(self.vertical_layout)

        self.clear_btn.clicked.connect(self.process_list.clear)

    def start_button_timer(self, state):
        """ Disables start button for a second. Prevents double queueing. """
        self.start_btn.setDisabled(True)

        if not state:
            self.timer.start(1000)


if __name__ == '__main__':
    # Only visuals work
    import sys
    from PyQt5.QtWidgets import QApplication
    from utils.filehandler import FileHandler

    app = QApplication(sys.argv)
    gui = MainTab(FileHandler().load_settings())
    gui.show()
    app.exec_()
