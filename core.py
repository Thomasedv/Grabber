import sys
import os.path
import json
import re
import traceback

from Modules.parameterTree import ParameterTree
from Modules.tabWidget import Tabwidget
from Modules.lineEdit import LineEdit

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QLineEdit, \
    QCheckBox, QMessageBox, QShortcut, QFileDialog, QGridLayout, QTextBrowser, QTreeWidgetItem, qApp, QAction, QMenu
from PyQt5.QtCore import QProcess, pyqtSignal, Qt, QMimeData
from PyQt5.QtGui import QFont, QKeySequence, QIcon, QTextCursor, QClipboard, QGuiApplication


class GUI(QProcess):
    sendclose = pyqtSignal()
    EXIT_CODE_REBOOT = -123456789

    def __init__(self):
        super(GUI, self).__init__()
        # starts checks
        self.initial_checks()

        # Builds GUI and everything.
        self.build_gui()

        # Set the channel to merged.
        self.setProcessChannelMode(QProcess.MergedChannels)
        # connects output to the GUI part.
        self.readyReadStandardOutput.connect(self.read_stdoutput)

    def initial_checks(self):
        self.settings = self.write_default_settings(reset=False)

        # Find resources.
        # Find youtube-dl
        self.youtube_dl_path = self.locate_program_path('youtube-dl.exe')
        self.ffmpeg_path = self.locate_program_path('ffmpeg.exe')
        self.program_workdir = self.set_program_working_directory().replace('\\', '/')
        self.workDir = os.getcwd().replace('\\', '/')
        self.lincense_path = self.resource_path('LICENSE')

        self.local_dl_path = ''.join([self.workDir, '/DL/'])

        self.check_settings_integrity()
        # NB! For stylesheet stuff, the slashes '\' in the path, must be replaced with '/'.
        # Use replace('\\', '/') on path.
        self.iconlist = []

        # Find icon paths
        self.unchecked_icon = self.resource_path('GUI\\Icon_unchecked.ico').replace('\\', '/')
        self.checked_icon = self.resource_path('GUI\\Icon_checked.ico').replace('\\', '/')
        self.alert_icon = self.resource_path('GUI\\Alert.ico').replace('\\', '/')
        self.window_icon = self.resource_path('GUI\\YTDLGUI.ico').replace('\\', '/')

        # Adding icons to list. For debug purposes.
        self.iconlist.append(self.unchecked_icon)
        self.iconlist.append(self.checked_icon)
        self.iconlist.append(self.alert_icon)
        self.iconlist.append(self.window_icon)

        # Creating icon objects for use in message windows.
        self.alertIcon = QIcon()
        self.windowIcon = QIcon()

        # Setting the icons image, using found paths.
        self.alertIcon.addFile(self.alert_icon)
        self.windowIcon.addFile(self.window_icon)

    def build_gui(self):
        # Denotes if the process(youtube-dl) is running.
        self.RUNNING = False
        # Denotes if the textfile is saved.
        self.SAVED = True
        # Indicates if license is shown.
        self.license_shown = False

        # Used later for checking the text feed from youtuibne-dl.
        self.replace_dict = {
            '[ffmpeg] ': '',
            '[youtube] ': ''
        }
        self.substrs = sorted(self.replace_dict, key=len, reverse=True)
        ## Stylesheet of widget!
        self.style = f"""
                        QWidget {{
                            background-color: #484848;
                            color: white;
                        }}

                        QTabWidget::pane {{
                            border: none;
                        }}
                        
                        QMenu {{
                            border: 1px solid #303030;
                        }}
                        
                        QMenu::item:selected {{
                            background-color: #303030;
                        }}

                        QMenu::item:disabled {{
                            color: #808080;
                        }}

                        QTabWidget {{
                            background-color: #303030;
                        }}

                        QTabBar {{
                            background-color: #313131;
                        }}

                        QTabBar::tab {{
                            color: rgb(186,186,186);
                            background-color: #606060;
                            border-top-left-radius: 5px;
                            border-top-right-radius: 5px;
                            border-bottom: none;
                            min-width: 15ex;
                            min-height: 7ex;
                        }}

                        QTabBar::tab:selected {{
                            color: white;
                            background-color: #484848;
                        }}
                        QTabBar::tab:!selected {{
                            margin-top: 6px;
                        }}

                        QTabWidget::tab-bar {{
                            border-top: 1px solid #505050;
                        }}

                        QLineEdit {{
                            background-color: #303030;
                            color: rgb(186,186,186);
                            border-radius: 5px;
                            padding: 0 3px;

                        }}
                        QLineEdit:disabled {{
                            background-color: #303030;
                            color: #505050;
                            border-radius: 5px;
                        }}

                        QTextEdit {{
                            background-color: #484848;
                            color: rgb(186,186,186);
                            border: none;
                        }}

                        QTextEdit#TextFileEdit {{
                            background-color: #303030;
                            color: rgb(186,186,186);
                            border-radius: 5px;
                        }}

                        QScrollBar:vertical {{
                            border: none;
                            background-color: rgba(255,255,255,0);
                            width: 10px;
                            margin: 0px 0px 1px 0px;
                        }}

                        QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
                            border: none;
                            background: none;
                        }}

                        QScrollBar::handle:vertical {{
                            background: #303030;
                            color: red;
                            min-height: 20px;
                            border-radius: 5px;
                        }}

                        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical  {{
                            background: none;
                        }}

                        QPushButton {{
                            background-color: #303030;
                            color: white;
                            border: 1px grey;
                            border-radius: 5px;
                            border-style: solid;
                            width: 60px;
                            height: 20px;
                        }}

                        QPushButton:disabled {{
                            background-color: #484848;
                            color: grey;
                        }}
                        QPushButton:pressed {{
                            background-color: #101010;
                            color: white;
                        }}

                        QCheckBox::indicator:unchecked {{
                            image: url({self.unchecked_icon});
                        }}

                        QCheckBox::indicator:checked {{
                            image: url({self.checked_icon});
                        }}

                        QTreeWidget {{
                            selection-color: red;
                            border: none;
                            outline: none;
                            outline-width: 0px;
                            selection-background-color: blue;
                        }}      

                        QTreeWidget::item {{
                            height: 16px;
                        }}

                        QTreeWidget::item:disabled {{
                            color: grey;
                        }}

                        QTreeWidget::item:hover, QTreeWidget::item:selected {{
                            background-color: transparent;
                            color: white;
                        }}

                        QTreeWidget::indicator:checked {{
                            image: url({self.checked_icon});
                        }}
                        QTreeWidget::indicator:unchecked {{
                            image: url({self.unchecked_icon});
                        }}

                        """

        ### Main widget. This will be the ones that holds everything.

        ## Create top level tab widget system for the UI.
        self.main_tab = Tabwidget()
        self.main_tab.onclose.connect(self.confirm)
        self.sendclose.connect(self.main_tab.closeE)

        # When statechanged, then the program state changed function is called.
        # Checks if the process is running and enables/disables buttons.
        self.stateChanged.connect(self.program_state_changed)


        ### TAB 1 ###

        ## Widget creation tab 1. Core tab.

        # Starts the program (Youtube-dl)
        self.tab1_start_btn = QPushButton('Download')
        # stops the program
        self.tab1_stop_btn = QPushButton('Abort')
        # Closes window (also stops the program)
        self.tab1_close_btn = QPushButton('Close')

        # Label and lineedit creation. Line edit for acception youtube links as well as paramters.
        self.tab1_label = QLabel("Url: ")
        self.tab1_lineedit = LineEdit()

        # TextEdit creation, for showing status messages, and the youtube-dl output.
        self.tab1_textbrowser = QTextBrowser()

        self.tab1_textbrowser.setAcceptRichText(True)
        self.tab1_textbrowser.setOpenExternalLinks(True)
        self.tab1_textbrowser.setContextMenuPolicy(Qt.NoContextMenu)

        # Adds welcome message on startup.
        self.tab1_textbrowser.append('Welcome!\n\nAdd video url, or load from text file.')
        # self.edit.append('<a href="URL">Showtext</a>') Learning purposes.

        # Start making checkbutton for selecting downloading from text file mode.
        self.tab1_checkbox = QCheckBox('Download from text file.')

        ## Layout tab 1.

        # Contains, start, abort, close buttons, and a stretch to make buttons stay on the correct side on rezise.
        self.tab1_QH = QHBoxLayout()

        self.tab1_QH.addStretch(1)
        self.tab1_QH.addWidget(self.tab1_start_btn)
        self.tab1_QH.addWidget(self.tab1_stop_btn)
        self.tab1_QH.addWidget(self.tab1_close_btn)

        # Horizontal layout 2, contains label and LineEdit. LineEdit stretches horizontally by default.
        self.tab1_QH2 = QHBoxLayout()

        self.tab1_QH2.addWidget(self.tab1_label)
        self.tab1_QH2.addWidget(self.tab1_lineedit)

        # Creates vertical box for tab1.
        self.tab1_QV = QVBoxLayout()

        # Adds horizontal layouts, textbrowser and checkbox to create tab1.
        self.tab1_QV.addLayout(self.tab1_QH2)
        self.tab1_QV.addWidget(self.tab1_checkbox)
        self.tab1_QV.addWidget(self.tab1_textbrowser, 1)
        self.tab1_QV.addLayout(self.tab1_QH)

        # Tab 1 as a Qwidget.
        self.tab1 = QWidget()
        self.tab1.setLayout(self.tab1_QV)

        ## Connecting stuff for tab 1.

        # Start buttons starts download
        self.tab1_start_btn.clicked.connect(self.start_DL)
        # Stop button kills the process, aka youtube-dl.
        self.tab1_stop_btn.clicked.connect(self.kill)
        # Close button closes the window/process.
        self.tab1_close_btn.clicked.connect(self.main_tab.close)
        # When the check button is checked or unchecked, calls function checked.
        self.tab1_checkbox.stateChanged.connect(self.is_batch_dl_checked)
        # Connects actions to text changes and adds action to when you press Enter.
        self.tab1_lineedit.textChanged.connect(self.enable_start)
        # Starts downloading
        self.tab1_lineedit.returnPressed.connect(self.tab1_start_btn.click)

        ### Tab 2
        #  Building widget tab 2.

        # Button for browsing download location.
        self.tab2_browse_btn = QPushButton('Browse')

        # Label for the lineEdit.
        self.tab2_download_label = QLabel('Download to:')

        # LineEdit for download location.
        self.tab2_download_lineedit = QLineEdit()
        self.tab2_download_lineedit.setReadOnly(True)

        if self.settings['Settings']['Download location']['options']:
            self.tab2_download_lineedit.setText('')
            self.tab2_download_lineedit.setToolTip(self.settings['Settings']['Download location']['options'][
                                                       self.settings['Settings']['Download location'][
                                                           'Active option']].replace('%(title)s.%(ext)s', ''))
        else:
            # Should not be reachable anymore!
            self.tab2_download_lineedit.setText('DL')
            self.tab2_download_lineedit.setToolTip('Default download location.')

        # Sets up the parameter tree.
        self.tab2_options = ParameterTree(self.settings['Settings'])
        self.custom_options()

        self.tab2_download_lineedit.setContextMenuPolicy(Qt.ActionsContextMenu)

        # Menu creation for tab2_download_lineedit
        menu = QMenu()
        # Makes an action for the tab2_download_lineedit
        open_folder_action = QAction('Open location', parent=self.tab2_download_lineedit)
        #open_folder_action.setEnabled(True)
        open_folder_action.triggered.connect(self.open_folder)

        copy_action = QAction('Copy',parent=self.tab2_download_lineedit)
        copy_action.triggered.connect(self.copy_to_cliboard)

        menu.addAction(copy_action)

        ## Layout tab 2.

        # Horizontal layout for the download line.
        self.tab2_QH = QHBoxLayout()

        # Adds widgets to the horizontal layout. label, lineedit and button. LineEdit stretches by deafult.
        self.tab2_QH.addWidget(self.tab2_download_label)
        self.tab2_QH.addWidget(self.tab2_download_lineedit)
        self.tab2_QH.addWidget(self.tab2_browse_btn)

        # Vertical layout creation
        self.tab2_QV = QVBoxLayout()
        # Adds the dl layout to the vertical one.
        self.tab2_QV.addLayout(self.tab2_QH)

        # Adds stretch to the layout.
        self.tab2_grid_layout = QGridLayout()
        self.tab2_grid_layout.expandingDirections()
        self.tab2_grid_layout.addWidget(self.tab2_options)

        self.tab2_QV.addLayout(self.tab2_grid_layout)
        self.tab2_QV.addStretch(1)

        # Create Qwidget for the layout for tab 2.
        self.tab2 = QWidget()
        # Adds the tab2 layout to the widget.
        self.tab2.setLayout(self.tab2_QV)

        ## Connection stuff tab 2.

        self.tab2_download_lineedit.addAction(open_folder_action)
        self.tab2_download_lineedit.addAction(copy_action)

        self.tab2_options.itemChanged.connect(self.parameter_updater)
        self.tab2_browse_btn.clicked.connect(self.savefile_dialog)

        ### Tab 3.

        ## Widget creation tab 3.
        # Create textedit
        self.tab3_textedit = QTextEdit()
        self.tab3_textedit.setObjectName('TextFileEdit')

        self.font = QFont()
        self.font.setFamily('Consolas')
        self.font.setPixelSize(13)
        self.tab3_textedit.setFont(self.font)

        # Create load button and label.
        self.tab3_label = QLabel('Add videos to textfile:')
        self.tab3_loadButton = QPushButton('Load file')
        self.tab3_saveButton = QPushButton('Save file')
        self.tab3_saveButton.setDisabled(True)

        ## Layout tab 3.

        # Create horizontal layout.
        self.tab3_QH = QHBoxLayout()

        # Filling horizontal layout
        self.tab3_QH.addWidget(self.tab3_label)
        self.tab3_QH.addStretch(1)
        self.tab3_QH.addWidget(self.tab3_loadButton)
        self.tab3_QH.addWidget(self.tab3_saveButton)

        # Horizontal layout with a textedit and a button.
        self.tab3_VB = QVBoxLayout()
        self.tab3_VB.addLayout(self.tab3_QH)
        self.tab3_VB.addWidget(self.tab3_textedit)

        # Tab creation.
        self.tab3 = QWidget()
        self.tab3.setLayout(self.tab3_VB)

        ## Connecting stuff tab 3.

        # When loadbutton is clicked, launch load textfile.
        self.tab3_loadButton.clicked.connect(self.load_text_from_file)
        # When savebutton clicked, save text to document.
        self.tab3_saveButton.clicked.connect(self.save_text_to_file)
        self.tab3_textedit.textChanged.connect(self.enable_saving)

        ### Tab 4

        # Button to browse for .txt file to download files.
        self.tab4_txt_location_btn = QPushButton('Browse')
        # Button to check for youtube-dl updates.
        self.tab4_update_btn = QPushButton('Update')
        # License
        self.tab4_license_btn = QPushButton('License')
        # Debugging
        self.tab4_dirinfo_btn = QPushButton('Dirinfo')
        # Reset settings, (requires restart!)
        self.tab4_test_btn = QPushButton('Reset\n settings')
        # Adjust button size to match naming. (Possibly change later in some form)
        self.tab4_test_btn.setMinimumHeight(30)

        # Lineedit to show path to text file. (Can be changed later to use same path naming as other elements.)
        self.tab4_txt_lineedit = QLineEdit()
        self.tab4_txt_lineedit.setReadOnly(True)  # Read only
        self.tab4_txt_lineedit.setText(self.settings['Other stuff']['multidl_txt'])  # Path from settings.

        self.tab4_txt_label = QLabel('Textfile:')

        # Textbrowser to adds some info about Grabber.
        self.tab4_abouttext_textedit = QTextBrowser()
        self.tab4_abouttext_textedit.setObjectName('AboutText')
        self.tab4_abouttext_textedit.setOpenExternalLinks(True)
        self.tab4_abouttext_textedit.setText('In-development (on my free time) version of a Youtube-dl GUI. \n'
                                             'I\'m just a developer for fun.\nThis is licensed under GPL 3.\n')
        self.tab4_abouttext_textedit.append('Source on Github: '
                                            '<a style="color: darkorange" '
                                            'href="https://github.com/Thomasedv/Grabber">'
                                            'Website'
                                            '</a>')
        self.tab4_abouttext_textedit.append('<br>PyQt5 use for making this: '
                                            '<a style="color: darkorange" '
                                            'href="https://www.riverbankcomputing.com/software/pyqt/intro">'
                                            'Website'
                                            '</a>')

        ## Layout tab 4.

        self.tab4_QH = QHBoxLayout()
        self.tab4_QV = QVBoxLayout()

        self.tab4_QH.addWidget(self.tab4_abouttext_textedit)

        self.tab4_QV.addWidget(self.tab4_update_btn)
        self.tab4_QV.addWidget(self.tab4_dirinfo_btn)
        self.tab4_QV.addWidget(self.tab4_license_btn)
        self.tab4_QV.addWidget(self.tab4_test_btn)

        self.tab4_QV.addStretch(1)

        self.tab4_QH.addLayout(self.tab4_QV)

        self.tab4_topQH = QHBoxLayout()
        self.tab4_topQH.addWidget(self.tab4_txt_label)
        self.tab4_topQH.addWidget(self.tab4_txt_lineedit)
        self.tab4_topQH.addWidget(self.tab4_txt_location_btn)

        self.tab4_topQV = QVBoxLayout()
        self.tab4_topQV.addLayout(self.tab4_topQH)
        self.tab4_topQV.addLayout(self.tab4_QH)

        self.tab4 = QWidget()
        self.tab4.setLayout(self.tab4_topQV)

        ## Connecting stuff tab 4.

        # Starts self.update_youtube_dl, locate_program_path checks for updates.
        self.tab4_update_btn.clicked.connect(self.update_youtube_dl)
        self.tab4_dirinfo_btn.clicked.connect(self.dir_info)
        self.tab4_test_btn.clicked.connect(self.reset_settings)
        self.tab4_license_btn.clicked.connect(self.read_license)
        self.tab4_txt_location_btn.clicked.connect(self.textfile_dialog)

        ### Future tab creation here! Currently 4 tabs already.

        ### Configuration main widget.

        # Adds tabs to the tab widget, and names the tabs.
        self.main_tab.addTab(self.tab1, 'Main')
        self.main_tab.addTab(self.tab2, 'Param')
        self.main_tab.addTab(self.tab3, 'List')
        self.main_tab.addTab(self.tab4, 'About')
        # Sets the styling for the GUI, everything from buttons to anything. ##
        self.main_tab.setStyleSheet(self.style)
        # Set window title.
        self.main_tab.setWindowTitle('GUI')
        # Set base size.
        self.main_tab.setMinimumWidth(340)
        self.main_tab.setMinimumHeight(200)
        self.main_tab.setWindowIcon(self.windowIcon)  # Window icon

        # Other functionality.
        self.shortcut = QShortcut(QKeySequence("Ctrl+S"), self.tab3_textedit)
        self.shortcut.activated.connect(self.tab3_saveButton.click)

        # Check for youtube
        if self.youtube_dl_path is None:
            self.tab4_update_btn.setDisabled(True)
            self.tab1_textbrowser.append(self.color_text('\nNo youtube-dl.exe found! Add to path, '
                                                         'or make sure it\'s in the same folder as this program. '
                                                         'Then close and reopen this program.', 'darkorange', 'bold'))

        # Renames items for download paths, adds tooltip. Essentially handles how the widget looks at startup.
        self.download_name_handler()
        # Ensures widets are in correct state at startup and when tab1_lineedit is changed.
        self.enable_start()
        # Shows the main window.
        self.main_tab.show()
        # Sets the lineEdit for youtube links and paramters as focus. For easier writing.
        self.tab1_lineedit.setFocus()

    def copy_to_cliboard(self, text):
        mime = QMimeData()
        mime.setText(self.tab2_download_lineedit.text())
        board = QGuiApplication.clipboard()
        board.setMimeData(mime, mode=QClipboard.Clipboard)

    @staticmethod
    def path_shortener(full_path):
        full_path = full_path.replace('%(title)s.%(ext)s', '')
        if full_path[-1] != '/':
            full_path = ''.join([full_path, '/'])

        if len(full_path) > 15:
            times = 0
            for integer, letter in enumerate(reversed(full_path)):
                if letter == '/':
                    split = -integer - 1
                    times += 1
                    if times == 3:
                        break
            else:
                raise Exception(''.join(['Something went wrong with path shortening! Path:', full_path]))

            short_path = ''.join([full_path[0:3], '...', full_path[split:]])
        else:
            short_path = full_path

        if not short_path[-1] == '/':
            short_path += '/'

        return short_path

    def open_folder(self):
        QProcess.startDetached('explorer {}'.format(self.tab2_download_lineedit.toolTip().replace("/","\\")))

    def custom_options(self):
        self.tab2_options.blockSignals(True)

        parent = self.tab2_options.make_option(self.settings['Other stuff']['custom']['Command'],
                                               self.tab2_options,
                                               self.settings['Other stuff']['custom']['state'],
                                               2,
                                               self.settings['Other stuff']['custom']['tooltip'])

        parent.setFlags(parent.flags() | Qt.ItemIsEditable)
        self.tab2_options.blockSignals(False)

    def download_name_handler(self):
        for item in self.tab2_options.topLevelItems():
            self.tab2_options.blockSignals(True)

            if item.data(0, 32) == 'Download location':
                for number in range(item.childCount()):
                    item.child(number).setData(0, 0,
                                               self.path_shortener(item.child(number).data(0, 0)))
                    item.child(number).setToolTip(0, item.child(number).data(0, 32).replace('%(title)s.%(ext)s', ''))

                if item.checkState(0) == Qt.Checked:
                    for number in range(item.childCount()):
                        if item.child(number).checkState(0) == Qt.Checked:
                            self.tab2_download_lineedit.setText(item.child(number).data(0, 0))
                            break
                else:
                    self.tab2_download_lineedit.setText(self.path_shortener(self.local_dl_path))
                    self.tab2_download_lineedit.setToolTip(self.local_dl_path)

            self.tab2_options.blockSignals(False)

    def download_option_handler(self, full_path):
        # Adds new dl location to the tree and settings. Removes oldest one, if there is more than 3.
        # Remove try/except later.
        for item in self.tab2_options.topLevelItems():
            try:
                if item.data(0, 32) == 'Download location':
                    short_path = self.path_shortener(full_path)

                    names = [i.data(0, 0) for i in self.tab2_options.childrens(item)]
                    if short_path in names \
                            and full_path+'/%(title)s.%(ext)s' in self.settings['Settings']['Download location']['options']:
                        self.alert_message('Warning','Option already exists!','',question=False)
                        break
                    self.tab2_options.blockSignals(True)

                    sub = self.tab2_options.make_option(name=full_path,
                                                        parent=item,
                                                        checkstate=False,
                                                        level=1,
                                                        tooltip=full_path,
                                                        dependency=None,
                                                        subindex=None)
                    sub.setData(0, 0, short_path)

                    moving_sub = item.takeChild(item.indexOfChild(sub))

                    item.insertChild(0, moving_sub)

                    for number in range(item.childCount()):
                        item.child(number).setData(0, 35, number)

                    if self.settings['Settings']['Download location']['options'] is None:
                        self.settings['Settings']['Download location']['options'] = [full_path + '/%(title)s.%(ext)s']
                    else:
                        if item.childCount() >= 4:
                            self.settings['Settings']['Download location']['options']: list
                            self.settings['Settings']['Download location']['options'].insert(0,
                                                                                             full_path + '/%(title)s.%(ext)s')

                            del self.settings['Settings']['Download location']['options'][3:]
                        else:
                            self.settings['Settings']['Download location']['options'].insert(0,
                                                                                             full_path + '/%(title)s.%(ext)s')

                    if item.childCount() >= 3:
                        item.removeChild(item.child(3))

                    self.tab2_options.resizer(item)
                    self.tab2_options.blockSignals(False)

                    # self.tab2_download_lineedit.setText(location)
                    # self.tab2_download_lineedit.setToolTip(tooltip)

                    item.setCheckState(0, Qt.Checked)
                    sub.setCheckState(0, Qt.Checked)

                    self.write_setting(self.settings)

            except Exception as e:
                raise NotImplementedError('Failed to catch an error.\n'+str(e))

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    @staticmethod
    def write_default_settings(reset=False):
        if reset:
            settings = {}
            settings['Settings'] = {}
            settings['Other stuff'] = {
                'multidl_txt': '',
                'custom':{
                    "Command": "Custom",
                    "state": False,
                    "tooltip": "Custom option, double click to edit."
                }
            }
            settings['Settings']['Convert to audio'] = {
                "Active option": 0,
                "Command": "-x --audio-format {} --audio-quality 0",
                "dependency": None,
                "options": ['mp3'],
                "state": True,
                "tooltip": "Convert to selected audio format."
            }
            settings['Settings']["Add thumbnail"] = {
                "Active option": 0,
                "Command": "--embed-thumbnail",
                "dependency": 'Convert to audio',
                "options": None,
                "state": True,
                "tooltip": "Include thumbnail on audio files."
            }
            settings['Settings']['Ignore errors'] = {
                "Active option": 0,
                "Command": "-i",
                "dependency": None,
                "options": None,
                "state": True,
                "tooltip": "Ignores errors, and jumps to next element instead of stopping."
            }
            settings['Settings']['Download location'] = {
                "Active option": 0,
                "Command": "-o {}",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Select download location."
            }
            settings['Settings']['Strict file names'] = {
                "Active option": 0,
                "Command": "--restrict-filenames",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Sets strict naming, to prevent unsupported characters in names."
            }
            settings['Settings']['Keep archive'] = {
                "Active option": 0,
                "Command": "--download-archive {}",
                "dependency": None,
                "options": ['Archive.txt'],
                "state": True,
                "tooltip": "Saves links to a textfile to avoid duplicate downloads later."
            }
            with open('Settings.json', 'w') as f:
                json.dump(settings, f, indent=4, sort_keys=True)
            return settings
        else:
            if os.path.isfile('Settings.json'):
                with open('Settings.json', 'r') as f:
                    return json.load(f)
            else:
                return GUI.write_default_settings(reset=True)

    def check_settings_integrity(self):
        # Base info.
        base_settings = ['Convert to audio',
                         'Add thumbnail',
                         'Ignore errors',
                         'Download location',
                         'Strict file names',
                         'Keep archive']
        base_keys = ['Command',
                     'dependency',
                     'options',
                     'state',
                     'tooltip']

        if not self.settings:
            raise SettingsError('Empty settings file!')

        missing_settings = {}

        for option in base_settings:
            if option not in self.settings['Settings']:
                missing_settings[option] = []
            else:
                for key in base_keys:
                    if key not in self.settings['Settings'][option]:
                        if option not in missing_settings.keys():
                            missing_settings[option] = [key]
                        else:
                            missing_settings[option].append(key)

        if missing_settings:
            raise SettingsError('\n'.join(['Settings file is corrupt/missing:',
                                           '-' * 20,
                                           *[f'{key}:\n - {", ".join(value)}' if value
                                             else f"{key}" for key, value in missing_settings.items()],
                                           '-' * 20]))

        if not self.settings['Settings']['Download location']['options']:
            self.settings['Settings']['Download location']['options'] = [self.workDir + '/DL/%(title)s.%(ext)s']

        try:
            for option in self.settings['Settings'].keys():
                if self.settings['Settings'][option]['options'] is not None:
                    if self.settings['Settings'][option]['Active option'] >= len(
                            self.settings['Settings'][option]['options']):
                        self.settings['Settings'][option]['Active option'] = 0

        except KeyError as error:
            raise SettingsError(f'{option} is missing a needed option {error}.')

        self.write_setting(self.settings)

    def update_setting(self, diction: dict, section: str, key: str, value):
        diction[section][key] = value
        self.write_setting(diction)

    def update_parameters(self, diction, setting, state):
        diction['Settings'][setting]['state'] = state
        self.write_setting(diction)

    def update_options(self, diction, setting, index):
        diction['Settings'][setting]['Active option'] = index
        self.write_setting(diction)

    def reset_settings(self):
        result = self.alert_message('Warning!',
                                    'Restart required!',
                                    'To reset the settings, '
                                    'the program has to be restarted. '
                                    'Do you want to reset and restart?',
                                    question=True)

        if result == QMessageBox.Yes:
            self.write_default_settings(reset=True)
            qApp.exit(self.EXIT_CODE_REBOOT)

    @staticmethod
    def write_setting(diction):
        with open('Settings.json', 'w') as f:
            json.dump(diction, f, indent=4, sort_keys=True)

    def parameter_updater(self, item: QTreeWidgetItem):
        if item.data(0, 33) == 0:
            if item.checkState(0) == Qt.Checked:
                self.update_parameters(self.settings, item.data(0, 32), True)
                if item.data(0, 32) == 'Download location':
                    for i in range(item.childCount()):
                        self.parameter_updater(item.child(i))
            else:
                self.update_parameters(self.settings, item.data(0, 32), False)
                if item.data(0, 32) == 'Download location':
                    self.tab2_download_lineedit.setText('DL')
                    self.tab2_download_lineedit.setToolTip('DL')

        elif item.data(0, 33) == 1:
            self.update_options(self.settings, item.parent().data(0, 32), item.data(0, 35))
            if item.parent().data(0, 32) == 'Download location':
                if item.checkState(0) == Qt.Checked:
                    self.tab2_download_lineedit.setText(item.data(0, 0))
                    print('item data 32', item.data(0, 32))
                    self.tab2_download_lineedit.setToolTip(item.data(0, 32).replace('%(title)s.%(ext)s', ''))

        elif item.data(0, 33) == 2:
            # Handles custom options.
            # print('item is custom')
            # print(str(item.data(0,0)))
            # print(str(item.checkState(0) == Qt.Checked))
            if item.data(0, 0) in ('', ' '):
                item.setData(0,0, 'Custom command double click to change')
                item.setCheckState(0, Qt.Unchecked)
            if item.data(0, 0) in ('custom', 'Custom'):
                item.setCheckState(0, Qt.Unchecked)
            self.settings['Other stuff']['custom']['Command'] = item.data(0, 0)
            self.settings['Other stuff']['custom']['state'] = item.checkState(0) == Qt.Checked
            self.write_setting(self.settings)




    @staticmethod
    def locate_program_path(program):
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
        if os.path.isfile(program):
            return program
        return None

    @staticmethod
    def color_text(text, color='darkorange', extra='bold', sections=None):
        text = text.replace('\n', '<br>')

        if not sections:

            string = ''.join(["""<span style=\"color:""" + str(color) + '; font-weight:' + extra + """;\" >""",
                              text,
                              "</span>"]
                             )
        else:
            work_text = text[sections[0]:sections[1]]
            string = ''.join([text[:sections[0]],
                              """<span style=\"color:""" + str(color) + '; font-weight:' + extra + """;\" >""",
                              work_text,
                              "</span>",
                              text[sections[1]:]]
                             )
        return string

    def dir_info(self):

        file_dir = os.path.dirname(os.path.abspath(__file__))

        debug = [self.color_text('\nYoutube-dl.exe path:'), self.youtube_dl_path,
                 self.color_text('Filedir:'), file_dir,
                 self.color_text('Workdir:'), self.workDir,
                 self.color_text('Youtube-dl working directory:'), self.program_workdir,
                 self.color_text('\nIcon paths:'),
                 self.checked_icon, self.unchecked_icon, self.alert_icon,
                 self.window_icon]

        for i in debug:
            self.tab1_textbrowser.append(str(i))

        self.tab1_textbrowser.append(self.color_text('\nChecking if icons are in place:', 'darkorange', 'bold'))

        for i in self.iconlist:
            if i is not None:
                try:
                    if os.path.isfile(str(i)):
                        self.tab1_textbrowser.append(''.join(['Found:', os.path.split(i)[1]]))
                    else:
                        self.tab1_textbrowser.append(''.join(['Missing in:', i]))
                except IndexError:
                    if os.path.isfile(str(i)):
                        self.tab1_textbrowser.append(''.join(['Found: ', i]))
                    else:
                        self.tab1_textbrowser.append(''.join(['Missing in:', i]))

    def set_program_working_directory(self):
        try:
            work_dir = sys._MEIPASS
        except AttributeError:
            work_dir = os.path.abspath('.')
        self.setWorkingDirectory(work_dir)

        return work_dir

    def update_youtube_dl(self):
        self.tab1_textbrowser.clear()
        self.main_tab.setCurrentIndex(0)
        self.start(self.youtube_dl_path, ['-U'])

    # When the process is started/stopped then this runs.
    def program_state_changed(self, new_state):
        # If it's not running, start button is enabled, and stop button disabled.
        if new_state == QProcess.NotRunning:
            self.tab1_start_btn.setDisabled(False)
            self.tab1_stop_btn.setDisabled(True)
            self.RUNNING = False

            self.tab1_textbrowser.append('\nDone\n')
            self.tab1_textbrowser.append(f'Error count: '
                                         f'{self.Errors if self.Errors ==0 else self.color_text(str(self.Errors),"darkorange","bold")}.')
            self.Errors = 0

        # Vise versa of the above.
        elif new_state == QProcess.Running:
            self.tab1_start_btn.setDisabled(True)
            self.tab1_stop_btn.setDisabled(False)
            self.RUNNING = True

    def savefile_dialog(self):
        location = QFileDialog.getExistingDirectory(parent=self.main_tab)

        if location == '':
            pass
        elif os.path.exists(location):
            self.download_option_handler(location)

    def textfile_dialog(self):
        location = \
            QFileDialog.getOpenFileName(parent=self.main_tab, filter='*.txt',
                                        caption='Select textfile with video links')[0]
        if location == '':
            pass
        elif os.path.isfile(location):
            if not self.SAVED:
                result = self.alert_message('Warning!',
                                            'Selecting new textfile,'
                                            ' this will load over the text in the download list tab!',
                                            'Do you want to load over the unsaved changes?',
                                            question=True)

                if result == QMessageBox.Yes:
                    self.update_setting(self.settings, 'Other stuff', 'multidl_txt', location)
                    self.tab4_txt_lineedit.setText(location)
                    self.SAVED = True
                    self.load_text_from_file()

            else:
                self.update_setting(self.settings, 'Other stuff', 'multidl_txt', location)
                self.tab4_txt_lineedit.setText(location)
                self.SAVED = True
                self.load_text_from_file()
        else:
            self.alert_message('Error!','Could not find file!','')
            # Check if the checkbox is toggled, and disables the line edit if it is.
            #  Also disables start button if lineEdit is empty and checkbox is not checked

    def is_batch_dl_checked(self):
        self.tab1_lineedit.setDisabled(self.tab1_checkbox.isChecked())
        self.tab1_start_btn.setDisabled(
            (not (self.tab1_checkbox.checkState() == 2 or (self.tab1_lineedit.text() != '')) is True) or self.RUNNING)

    # The process for starting the download. Clears text edit.

    @staticmethod
    def format_in_list(command, option):
        split_command = command.split()
        for index, item in enumerate(split_command):
            if item == '{}':
                split_command[index] = item.format(option)
                return split_command
        return split_command

    def start_DL(self):
        self.tab1_lineedit.clearFocus()


        self.tab1_textbrowser.clear()
        command = []

        if self.tab1_checkbox.isChecked():
            if self.tab4_txt_lineedit.text() == '':
                self.alert_message('Error!','No textfile selected!','')
                self.tab1_textbrowser.append('No textfile selected...\n\nNo download started!')
                return

            txt = self.settings['Other stuff']['multidl_txt']
            command += (' -a {txt}'.split()[-1].format(txt=txt))
        else:
            txt = self.tab1_lineedit.text()
            command.append(f'{txt}')

        #for i in range(len(command)):
        #    command[i] = command[i].format(txt=txt)

        for parameter, options in self.settings['Settings'].items():
            if parameter == 'Download location':
                if options['state']:
                    add = self.format_in_list(options['Command'],
                                              options['options'][options['Active option']])
                    command += add
                else:
                    command += ['-o', self.local_dl_path+'%(title)s.%(ext)s']
            elif parameter == 'Keep archive':
                if options['state']:
                    add = self.format_in_list(options['Command'],
                                              os.path.join(self.workDir, options['options'][options['Active option']]))
                    command += add
            else:
                if options['state']:
                    add = self.format_in_list(options['Command'],
                                              options['options'][
                                                  options['Active option']] if options['options'] is not None
                                                                               or options['options'] else '')
                    command += add

        if self.settings['Other stuff']['custom']['state']:
            if self.settings['Other stuff']['custom']['Command'] not in ('Custom command double click to change','Custom'):
                command += self.settings['Other stuff']['custom']['Command'].split()

        try:
            if self.ffmpeg_path:
                command += ['--ffmpeg-location', self.ffmpeg_path]
        except Exception as error:
            self.tab1_textbrowser.append(f'There was a small error with ffmpeg. Give this to dev:\n'
                                         f'{error}')
            print(error)

        self.Errors = 0
        print(command)
        self.start(self.youtube_dl_path, command)
        self.tab1_textbrowser.append('Starting...\n')

    def cmdoutput(self, info):
        if info.startswith('ERROR'):
            self.Errors += 1
            info = info.replace('ERROR','<span style=\"color: darkorange; font-weight: bold;\">ERROR</span>')
        info = re.sub(r'\s+$', '', info, 0, re.M)
        info = re.sub(' +', ' ', info)
        regexp = re.compile('|'.join(map(re.escape, self.substrs)))

        return regexp.sub(lambda match: self.replace_dict[match.group(0)], info)

    # appends youtube-dl output to tab1_textbrowser.
    def read_stdoutput(self):
        data = self.readAllStandardOutput().data()
        text = data.decode('windows-1252', 'replace').strip()
        text = self.cmdoutput(text)

        scrollbar = self.tab1_textbrowser.verticalScrollBar()
        place = scrollbar.sliderPosition()

        if place == scrollbar.maximum():
            keepPos = False
        else:
            keepPos = True

        # get the last line of QTextEdit
        self.tab1_textbrowser.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)
        self.tab1_textbrowser.moveCursor(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
        self.tab1_textbrowser.moveCursor(QTextCursor.End, QTextCursor.KeepAnchor)
        last_line = self.tab1_textbrowser.textCursor().selectedText()

        # Check if a percentage has already been placed.
        if "%" in last_line and 'ETA' in last_line:
            self.tab1_textbrowser.textCursor().removeSelectedText()
            self.tab1_textbrowser.textCursor().deletePreviousChar()
            # Last line of text
            self.tab1_textbrowser.append(self.color_text(text.split("[download]")[-1][1:],
                                                         color='lawngreen',
                                                         extra='bold',
                                                         sections=[0, 5]))
            if '100%' in text:
                self.tab1_textbrowser.append('')

        else:
            if "%" in text and 'ETA' in text:
                # Last line of text
                self.tab1_textbrowser.append(self.color_text(text.split("[download]")[-1][1:],
                                                             color='lightgreen',
                                                             extra='bold',
                                                             sections=[0, 5]))
            elif '[download]' in text:
                self.tab1_textbrowser.append(''.join([text.replace('[download] ', ''), '\n']))
            else:
                self.tab1_textbrowser.append(''.join([text, '\n']))

        # Prevents some leftover highlighted text on errors and such.
        self.tab1_textbrowser.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)

        # Ensures slider position is kept when not at bottom, and stays at bottom with new text where there.
        if keepPos:
            scrollbar.setSliderPosition(place)
        else:
            scrollbar.setSliderPosition(scrollbar.maximum())

    # Startup function, sets the startbutton to disabled, if lineEdit is empty,
    # And disables the lineEdit if the textbox is checked.
    # Stop button is set to disabled, since no process is running.
    def enable_start(self):
        self.tab1_start_btn.setDisabled((self.tab1_lineedit.text() == "") or (self.RUNNING is True))
        self.tab1_lineedit.setDisabled(self.tab1_checkbox.isChecked() is True)
        self.tab1_stop_btn.setDisabled((self.RUNNING is False))
        self.is_batch_dl_checked()

    def load_text_from_file(self):
        if ((self.tab3_textedit.toPlainText() == '') or (not self.tab3_saveButton.isEnabled())) or self.SAVED:
            if os.path.isfile(self.tab4_txt_lineedit.text()):
                self.tab3_textedit.clear()
                with open(self.tab4_txt_lineedit.text(), 'r') as f:
                    for line in f.readlines():
                        self.tab3_textedit.append(line.strip())
                self.tab3_textedit.append('')
                self.tab3_textedit.setFocus()
                self.tab3_saveButton.setDisabled(True)
                self.SAVED = True
            else:
                if self.tab4_txt_lineedit.text() == '':
                    warning = 'No textfile selected!'
                else:
                    warning = 'Could not find file!'
                self.alert_message('Error!', warning, '')
        else:
            if self.tab4_txt_lineedit.text() == '':
                self.SAVED = True
                self.load_text_from_file()
            else:
                result = self.alert_message('Warning',
                                            'Overwrite?',
                                            'Do you want to load over the unsaved changes?',
                                            question=True)
                if result == QMessageBox.Yes:
                    self.SAVED = True
                    self.load_text_from_file()

    def save_text_to_file(self):
        if not self.tab4_txt_lineedit.text() == '':
            with open(self.tab4_txt_lineedit.text(), 'w') as f:
                for line in self.tab3_textedit.toPlainText():
                    f.write(line)
            self.tab3_saveButton.setDisabled(True)
            self.SAVED = True
        else:
            result = self.alert_message('Warning!',
                                        'No textfile selected!',
                                        'Do you want to create one?',
                                        question=True)

            if result == QMessageBox.Yes:
                save_path = QFileDialog.getSaveFileName(parent=self.main_tab, caption='Save as', filter='*.txt')
                if not save_path[0] == '':

                    with open(save_path[0], 'w') as f:
                        for line in self.tab3_textedit.toPlainText():
                            f.write(line)
                            self.update_setting(self.settings, 'Other stuff', 'multidl_txt', save_path[0])

                    self.tab4_txt_lineedit.setText(save_path[0])
                    self.tab3_saveButton.setDisabled(True)
                    self.SAVED = True

    def alert_message(self, title, text, info_text, question=False, allow_cancel=False):
        warning_window = QMessageBox(parent=self.main_tab)
        warning_window.setText(text)
        warning_window.setIcon(QMessageBox.Warning)
        warning_window.setWindowTitle(title)
        warning_window.setWindowIcon(self.alertIcon)

        if info_text:
            warning_window.setInformativeText(info_text)
        if question and allow_cancel:
            warning_window.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        elif question:
            warning_window.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        return warning_window.exec()

    def enable_saving(self):
        self.tab3_saveButton.setDisabled(False)
        self.SAVED = False

    def confirm(self):
        if self.RUNNING:
            result = self.alert_message('Want to quit?',
                                        'Still downloading!',
                                        'Do you want to close without letting youtube-dl finish? '
                                        'Will likely leave unwanted/incomplete files in the download folder.',
                                        question=True)
            if result != QMessageBox.Yes:
                return None

        if ((self.tab3_textedit.toPlainText() == '') or (not self.tab3_saveButton.isEnabled())) or self.SAVED:
            self.sendclose.emit()
        else:
            result = self.alert_message('Unsaved changes in list!',
                                        'Save?',
                                        'Do you want to save before exiting?',
                                        question=True,
                                        allow_cancel=True)
            if result == QMessageBox.Yes:
                self.save_text_to_file()
                self.sendclose.emit()
            elif result == QMessageBox.Cancel:
                pass
            else:
                self.sendclose.emit()

    def read_license(self):
        if not self.license_shown:
                self.tab4_abouttext_textedit.clear()
                with open(self.lincense_path,'r') as f:
                    for line in f.readlines():
                        self.tab4_abouttext_textedit.append(line.strip())
                self.license_shown = True
        else:
            self.tab4_abouttext_textedit.setText('In-development (on my free time) version of a Youtube-dl GUI. \n'
                                                 'I\'m just a developer for fun.\nThis is licensed under GPL 3.\n')
            self.tab4_abouttext_textedit.append('Source on Github: '
                                                '<a style="color: darkorange" '
                                                'href="https://github.com/Thomasedv/Grabber">'
                                                'Website'
                                                '</a>')
            self.tab4_abouttext_textedit.append('<br>PyQt5 use for making this: '
                                                '<a style="color: darkorange" '
                                                'href="https://www.riverbankcomputing.com/software/pyqt/intro">'
                                                'Website'
                                                '</a>')
            self.license_shown = False

    def selector(self):
        self.tab1_lineedit.selectAll()


class SettingsError(Exception):
    pass


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMessageBox

    while True:
        try:
            app = QApplication(sys.argv)
            qProcess = GUI()

            EXIT_CODE = app.exec_()
            app = None

            if EXIT_CODE == GUI.EXIT_CODE_REBOOT:
                continue
            break

        except (SettingsError, json.decoder.JSONDecodeError) as e:
            A = QMessageBox.warning(None, 'Corrupt settings', ''.join([str(e), '\nRestore default settings?']),
                                    buttons=QMessageBox.Yes | QMessageBox.No)

            app = None
            if A == QMessageBox.Yes:
                GUI.write_default_settings(True)
                continue
            else:
                break
