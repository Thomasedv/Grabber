from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, \
    QGridLayout, QAction, QMenu, \
    QFrame

from Modules import ParameterTree
from utils.utilities import SettingsError


class ParameterTab(QWidget):

    def __init__(self, options, favorites, settings, parent=None):
        super().__init__(parent=parent)

        #  Building widget tab 2.

        # Button for browsing download location.
        self.browse_btn = QPushButton('Browse')

        self.save_profile_btn = QPushButton('Save Profile')
        self.save_profile_btn.resize(self.save_profile_btn.sizeHint())

        # Label for the lineEdit.
        self.download_label = QLabel('Download to:')

        self.favlabel = QLabel('Favorites:')
        self.optlabel = QLabel('All settings:')

        # LineEdit for download location.
        self.download_lineedit = QLineEdit()
        self.download_lineedit.setReadOnly(True)

        if settings.is_activate('Download location'):
            self.download_lineedit.setText('')
            self.download_lineedit.setToolTip(settings.get_active_setting('Download location'))
        else:
            self.download_lineedit.setText('DL')
            self.download_lineedit.setToolTip('Default download location.')
        self.download_lineedit.setContextMenuPolicy(Qt.ActionsContextMenu)

        # Sets up the parameter tree.
        self.options = ParameterTree(options, self)
        self.favorites = ParameterTree(favorites, self)
        self.favorites.favorite = True

        if settings.user_options['show_collapse_arrows']:
            self.options.setRootIsDecorated(True)
            self.favorites.setRootIsDecorated(True)
        else:
            self.options.setRootIsDecorated(False)
            self.favorites.setRootIsDecorated(False)

        # Menu creation for download_lineedit
        menu = QMenu()
        # Makes an action for the download_lineedit
        self.open_folder_action = QAction('Open location', parent=self.download_lineedit)
        # open_folder_action.setEnabled(True)

        self.copy_action = QAction('Copy', parent=self.download_lineedit)

        menu.addAction(self.copy_action)
        self.download_lineedit.addAction(self.open_folder_action)
        self.download_lineedit.addAction(self.copy_action)

        ## Layout tab 2.

        # Horizontal layout for the download line.
        self.QH = QHBoxLayout()

        # Adds widgets to the horizontal layout. label, lineedit and button. LineEdit stretches by deafult.
        self.QH.addWidget(self.download_label)
        self.QH.addWidget(self.download_lineedit)
        self.QH.addWidget(self.browse_btn)
        self.QH.addWidget(self.save_profile_btn)
        # Vertical layout creation
        self.QV = QVBoxLayout()
        # Adds the dl layout to the vertical one.
        self.QV.addLayout(self.QH, stretch=0)

        # Adds stretch to the layout.
        self.grid = QGridLayout()

        self.frame = QFrame()
        self.frame2 = QFrame()

        self.frame2.setFrameShape(QFrame.HLine)
        self.frame.setFrameShape(QFrame.HLine)

        self.frame.setLineWidth(2)
        self.frame2.setLineWidth(2)

        self.frame.setObjectName('line')
        self.frame2.setObjectName('line')

        self.grid.addWidget(self.favlabel, 1, 0)
        self.grid.addWidget(self.optlabel, 1, 1)
        self.grid.addWidget(self.frame, 2, 0)
        self.grid.addWidget(self.frame2, 2, 1)
        self.grid.addWidget(self.favorites, 3, 0, Qt.AlignTop)
        self.grid.addWidget(self.options, 3, 1, Qt.AlignTop)
        self.grid.setRowStretch(0, 0)
        self.grid.setRowStretch(1, 0)
        self.grid.setRowStretch(2, 0)
        self.grid.setRowStretch(3, 1)
        self.QV.addLayout(self.grid)

        self.setLayout(self.QV)
        self.download_option = self.find_download_widget()

    def find_download_widget(self):
        """ Finds the download widget. """
        # TODO: Refactor to check the settings file/object, not the parameterTrees.
        for item in self.tab2.favorites.topLevelItems():
            if item.data(0, 32) == 'Download location':
                return item
        for item in self.tab2.options.topLevelItems():
            if item.data(0, 32) == 'Download location':
                return item
        raise SettingsError('No download item found in settings.')
