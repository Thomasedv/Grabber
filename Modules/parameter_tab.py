from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, \
    QAction, QFrame

from Modules.parameter_tree import ParameterTree
from utils.utilities import SettingsError


class ParameterTab(QWidget):

    def __init__(self, options, favorites, settings, parent=None):
        super().__init__(parent=parent)

        #  Building widget tab 2.

        # Button for selecting download location.
        self.browse_btn = QPushButton('Browse')

        self.save_profile_btn = QPushButton('Save Profile')
        self.save_profile_btn.resize(self.save_profile_btn.sizeHint())

        self.download_label = QLabel('Download to:')

        self.favlabel = QLabel('Favorites:')
        self.optlabel = QLabel('All settings:')

        # LineEdit for download location.
        self.download_lineedit = QLineEdit()
        self.download_lineedit.setReadOnly(True)
        self.download_lineedit.setFocusPolicy(Qt.NoFocus)

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

        # Can only be toggled in settings manually
        if settings.user_options['show_collapse_arrows']:
            self.options.setRootIsDecorated(True)
            self.favorites.setRootIsDecorated(True)
        else:
            self.options.setRootIsDecorated(False)
            self.favorites.setRootIsDecorated(False)

        self.open_folder_action = QAction('Open location', parent=self.download_lineedit)
        self.copy_action = QAction('Copy', parent=self.download_lineedit)

        self.download_lineedit.addAction(self.open_folder_action)
        self.download_lineedit.addAction(self.copy_action)

        # Layout tab 2.

        self.QH = QHBoxLayout()

        # Adds widgets to the horizontal layout. label, lineedit and button.
        self.QH.addWidget(self.download_label)
        self.QH.addWidget(self.download_lineedit)
        self.QH.addWidget(self.browse_btn)
        self.QH.addWidget(self.save_profile_btn)

        self.QV = QVBoxLayout()
        self.QV.addLayout(self.QH, stretch=0)


        self.frame = QFrame()
        self.frame2 = QFrame()

        self.frame2.setFrameShape(QFrame.HLine)
        self.frame.setFrameShape(QFrame.HLine)

        self.frame.setLineWidth(2)
        self.frame2.setLineWidth(2)

        self.frame.setObjectName('line')
        self.frame2.setObjectName('line')
        # self.grid = QGridLayout()
        # self.grid.addWidget(self.favlabel, 1, 0, Qt.AlignTop)
        # self.grid.addWidget(self.optlabel, 1, 1, Qt.AlignTop)

        self.fav_layout = QVBoxLayout()
        self.all_layout = QVBoxLayout()

        self.fav_layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.fav_layout.addWidget(self.favlabel, stretch=0)
        self.fav_layout.addWidget(self.frame, stretch=0)
        self.fav_layout.addWidget(self.favorites, stretch=1, alignment=Qt.AlignTop)

        self.all_layout.addWidget(self.optlabel, stretch=0)
        self.all_layout.addWidget(self.frame2, stretch=0)
        self.all_layout.addWidget(self.options, stretch=1, alignment=Qt.AlignTop)

        self.parameter_layout = QHBoxLayout()
        self.parameter_layout.addLayout(self.fav_layout)
        self.parameter_layout.addLayout(self.all_layout)

        self.QV.addLayout(self.parameter_layout)

        self.setLayout(self.QV)

        self.download_option = self.find_download_widget()

    def enable_favorites(self, enable):
        if not enable:

            self.frame.resize(0, 0)
            self.favlabel.resize(0, 0)

            self.favorites.hide()
            self.frame.hide()
            self.favlabel.hide()
        else:
            # Just half the size of the all settings parametertree
            self.frame.resize(self.frame2.width() // 2, self.frame2.height() // 2)
            self.favlabel.resize(self.optlabel.width() // 2, self.optlabel.height() // 2)

            self.favorites.show()
            self.frame.show()
            self.favlabel.show()

    def find_download_widget(self):
        """ Finds the download widget. """
        # TODO: Refactor to check the settings file/object, not the parameterTrees.
        for item in self.favorites.topLevelItems():
            if item.data(0, 32) == 'Download location':
                self.download_option = item
                return item
        for item in self.options.topLevelItems():
            if item.data(0, 32) == 'Download location':
                self.download_option = item
                return item
        raise SettingsError('No download item found in settings.')
