from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QWidget, QTextBrowser, QLineEdit


class AboutTab(QWidget):

    def __init__(self, settings, parent=None):
        super(AboutTab, self).__init__(parent=parent)

        # Select folder for textfile to use as download list
        self.location_btn = QPushButton('Browse')
        # Button to check for youtube-dl updates.
        self.update_btn = QPushButton('Update')
        # License
        self.license_btn = QPushButton('License')
        # Debugging
        self.dirinfo_btn = QPushButton('Dirinfo')
        # Parralel / Series toggle
        self.dl_mode_btn = QPushButton("Singular" if not settings.user_options['parallel'] else "Parallel")
        # Debug info mode
        self.debug_info = QPushButton('Debug:\nFalse')
        self.debug_info.setMinimumHeight(30)
        # Reset settings, (requires restart!)
        self.reset_btn = QPushButton('Reset\n settings')
        # Adjust button size to match naming. (Possibly change later in some form)
        self.reset_btn.setMinimumHeight(30)

        # Lineedit to show path to text file. (Can be changed later to use same path naming as other elements.)
        self.txtfile_url = QLineEdit()
        self.txtfile_url.setReadOnly(True)  # Read only
        self.txtfile_url.setText(settings.user_options['multidl_txt'])  # Path from settings.

        self.txt_label = QLabel('Textfile:')

        # Textbrowser to adds some info about Grabber.
        self.textbrowser = QTextBrowser()
        self.textbrowser.setObjectName('AboutText')
        self.textbrowser.setOpenExternalLinks(True)

        self.set_standard_text()

        self.QH = QHBoxLayout()
        self.QV = QVBoxLayout()

        self.QH.addWidget(self.textbrowser)

        self.QV.addWidget(self.update_btn)
        self.QV.addWidget(self.dl_mode_btn)
        self.QV.addWidget(self.dirinfo_btn)
        self.QV.addWidget(self.license_btn)
        self.QV.addWidget(self.debug_info)
        self.QV.addWidget(self.reset_btn)

        self.QV.addStretch(1)

        self.QH.addLayout(self.QV)

        self.topQH = QHBoxLayout()
        self.topQH.addWidget(self.txt_label)
        self.topQH.addWidget(self.txtfile_url)
        self.topQH.addWidget(self.location_btn)

        self.topQV = QVBoxLayout()
        self.topQV.addLayout(self.topQH)
        self.topQV.addLayout(self.QH)

        self.setLayout(self.topQV)

    def set_standard_text(self):
        self.textbrowser.setText('In-development (on my free time) version of a Youtube-dl GUI. \n'
                                 'I\'m just a developer for fun.\nThis is licensed under GPL 3.\n')
        self.textbrowser.append('Source on Github: '
                                '<a style="color: darkorange" '
                                'href="https://github.com/Thomasedv/Grabber">'
                                'Website'
                                '</a>')
        self.textbrowser.append('<br>PyQt5 use for making this: '
                                '<a style="color: darkorange" '
                                'href="https://www.riverbankcomputing.com/software/pyqt/intro">'
                                'Website'
                                '</a>')
