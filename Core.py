import sys
import os.path
import json
import re
import traceback

from Modules.paramTree import paramTree
from Modules.TabWidget import Tabwidget

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QLineEdit, \
    QCheckBox, QMessageBox, QShortcut, QFileDialog, QGridLayout, QTextBrowser, QTreeWidgetItem, qApp
from PyQt5.QtCore import QProcess, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QKeySequence, QIcon, QTextCursor


class GUI(QProcess):
    sendclose = pyqtSignal()
    EXIT_CODE_REBOOT = -123456789

    def __init__(self):
        super(GUI, self).__init__()
        self.initial_checks()
        self.build_gui()
        # Set the channel to merged.
        self.setProcessChannelMode(QProcess.MergedChannels)
        # connects output to the GUI part.
        self.readyReadStandardOutput.connect(self.read_stdoutput)

    def initial_checks(self):
        self.Settings = self.write_default_settings(All=False)
        self.youtube_dl_path = self.locate_program_path('youtube-dl.exe')
        self.ffmpeg_path = self.locate_program_path('ffmpeg.exe')
        print(self.ffmpeg_path)
        self.program_workdir = self.setProgramWorkDir()
        self.workDir = os.getcwd().replace('\\', '/')


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
        self.Alerticon = QIcon()
        self.Windicon = QIcon()

        # Setting the icons image, using found paths.
        self.Alerticon.addFile(self.alert_icon)
        self.Windicon.addFile(self.window_icon)

    def build_gui(self):
        # Find resources.
        # Find youtube-dl

        self.replace_dict = {
            '[ffmpeg] ': '',
            '[youtube] ': '',
            'ERROR': '<span style=\"color: darkorange; font-weight: bold;\">ERROR</span>'
        }
        self.substrs = sorted(self.replace_dict, key=len, reverse=True)

        # Building tab 1. Core tab.
        # Starts the program (Youtube-dl)
        self.tab1_start_btn = QPushButton('Download')
        # stops the program
        self.tab1_stop_btn = QPushButton('Abort')
        # Closes window (also stops the program)
        self.tab1_close_btn = QPushButton('Close')

        # Horizontal layout, part of tab1.
        # Contains, start, abort, close buttons, and a stretch to make buttons stay on the correct side on rezise.
        self.tab1_QH = QHBoxLayout()
        self.tab1_QH.addStretch(1)
        self.tab1_QH.addWidget(self.tab1_start_btn)
        self.tab1_QH.addWidget(self.tab1_stop_btn)
        self.tab1_QH.addWidget(self.tab1_close_btn)

        # Label and lineedit creation. Line edit for acception youtube links as well as paramters.
        self.tab1_label = QLabel("Url: ")
        self.tab1_lineedit = QLineEdit()

        # Connects actions to text changes and adds action to when you press Enter.
        self.tab1_lineedit.textChanged.connect(self.enable_start)
        # Starts downloading
        self.tab1_lineedit.returnPressed.connect(self.tab1_start_btn.click)

        # Horizontal layout 2, contains label and LineEdit. LineEdit stretches horizontally by default.
        self.tab1_QH2 = QHBoxLayout()
        self.tab1_QH2.addWidget(self.tab1_label)
        self.tab1_QH2.addWidget(self.tab1_lineedit)

        # TextEdit creation, for showing status messages, and the youtube-dl output.
        self.tab1_textbrowser = QTextBrowser()
        self.tab1_textbrowser.setAcceptRichText(True)
        self.tab1_textbrowser.setOpenExternalLinks(True)

        # Adds weclome message on startup.
        self.tab1_textbrowser.append('Welcome!\n\nAdd video url, or load from text file.')

        # self.edit.append('<a href="URL">Showtext</a>') Learning purposes.

        # Creates vertical box for tab1.
        self.tab1_QV = QVBoxLayout()

        # Start making checkbutton for selecting downloading from text file mode.
        self.tab1_checkbox = QCheckBox('Download from text file.')

        # Adds horizontal layouts, textbrowser and checkbox to create tab1.
        self.tab1_QV.addLayout(self.tab1_QH2)
        self.tab1_QV.addWidget(self.tab1_checkbox)
        self.tab1_QV.addWidget(self.tab1_textbrowser, 1)
        self.tab1_QV.addLayout(self.tab1_QH)

        # Tab 1 as a Qwidget.
        self.tab1 = QWidget()
        self.tab1.setLayout(self.tab1_QV)

        ###
        # Tab 2
        ###


        # Horizontal layout for the download line.
        self.tab2_QH = QHBoxLayout()

        # Button for browsing download location.
        self.tab2_browse_btn = QPushButton('Browse')
        self.tab2_browse_btn.clicked.connect(self.savefile_dialog)
        # LineEdit for download location.
        self.tab2_download_lineedit = QLineEdit()
        self.tab2_download_lineedit.setReadOnly(True)
        if self.Settings['Settings']['Download location']['options']:
            self.tab2_download_lineedit.setText('')
            self.tab2_download_lineedit.setToolTip(self.Settings['Settings']['Download location']['options'][
                                                       self.Settings['Settings']['Download location'][
                                                           'Active option']].replace('%(title)s.%(ext)s', ''))
        else:
            self.tab2_download_lineedit.setText('DL')
            self.tab2_download_lineedit.setToolTip('Default download location.')
        # Label for the lineEdit.
        self.tab2_download_label = QLabel('Download to:')

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

        self.tab2_options = paramTree(self.Settings['Settings'])
        self.tab2_options.itemChanged.connect(self.paramchanger)
        self.tab2_grid_layout.addWidget(self.tab2_options)

        self.tab2_QV.addLayout(self.tab2_grid_layout)
        self.tab2_QV.addStretch(1)

        ## Create top level tab widget system for the UI.
        self.main_tab = Tabwidget()
        self.main_tab.onclose.connect(self.confirm)
        self.sendclose.connect(self.main_tab.closeE)

        # Create Qwidget for the layout for tab 2.
        self.tab_2 = QWidget()
        # Adds the tab2 layout to the widget.
        self.tab_2.setLayout(self.tab2_QV)

        # Tab 3. YTW.txt file changes.
        # Tab creation.
        self.tab3 = QWidget()

        # Create textedit
        self.YTW_TextEdit = QTextEdit()
        self.YTW_TextEdit.setObjectName('TextFileEdit')
        self.font = QFont()
        self.font.setFamily('Consolas')
        self.font.setPixelSize(13)
        self.YTW_TextEdit.setFont(self.font)
        # Create horizontal layout.
        self.tab3_QH = QHBoxLayout()

        # Create load button and label.
        self.tab3_label = QLabel('Add videos to textfile:')
        self.tab3_loadButton = QPushButton('Load file')
        self.tab3_saveButton = QPushButton('Save file')
        self.tab3_saveButton.setDisabled(True)

        # Filling horizontal layout
        self.tab3_QH.addWidget(self.tab3_label)
        self.tab3_QH.addStretch(1)
        self.tab3_QH.addWidget(self.tab3_loadButton)
        self.tab3_QH.addWidget(self.tab3_saveButton)

        # Horizontal layout with a textedit and a button.
        self.tab3_VB = QVBoxLayout()
        self.tab3_VB.addLayout(self.tab3_QH)
        self.tab3_VB.addWidget(self.YTW_TextEdit)

        self.tab3.setLayout(self.tab3_VB)

        # Tab 4
        self.tab4 = QWidget()
        self.tab4_QH = QHBoxLayout()
        self.tab4_QV = QVBoxLayout()

        # Checks for youtube-dl updates.
        self.tab4_txt_location_btn = QPushButton('Browse')
        self.tab4_update_btn = QPushButton('Update')
        self.tab4_dirinfo_btn = QPushButton('Dirinfo')
        self.tab4_test_btn = QPushButton('Reset\n settings')
        self.tab4_test_btn.setMinimumHeight(30)

        self.tab4_txt_lineedit = QLineEdit()
        self.tab4_txt_lineedit.setReadOnly(True)
        self.tab4_txt_lineedit.setText(self.Settings['Other stuff']['multidl_txt'])
        self.tab4_txt_label = QLabel('Textfile:')

        self.tab4_abouttext_textedit = QTextBrowser()
        self.tab4_abouttext_textedit.setObjectName('AboutText')
        self.tab4_abouttext_textedit.setOpenExternalLinks(True)
        self.tab4_abouttext_textedit.setText('In-development version of a Youtube-dl GUI. \n'
                                             'I\'m just a developer for fun.\n')
        self.tab4_abouttext_textedit.append('PyQt5 use for making this: '
                                            '<a style="color: darkorange" '
                                            'href="https://www.riverbankcomputing.com/software/pyqt/intro">'
                                            'Website'
                                            '</a>')

        # self.tab4_checkbox_test = paramTree(self.Settings['Settings'])


        self.tab4_QH.addWidget(self.tab4_abouttext_textedit)
        # self.tab4_QH.addWidget(self.tab4_checkbox_test)


        self.tab4_QV.addWidget(self.tab4_update_btn)
        self.tab4_QV.addWidget(self.tab4_dirinfo_btn)
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

        self.tab4.setLayout(self.tab4_topQV)

        #
        ### Future tab creation here!### (Tabs 4 and up.)
        #

        # Adds tabs to the tab widget, and names the tabs.
        self.main_tab.addTab(self.tab1, 'Main')
        self.main_tab.addTab(self.tab_2, 'Param')
        self.main_tab.addTab(self.tab3, 'List')
        self.main_tab.addTab(self.tab4, 'About')

        ## Sets the styling for the GUI, everything from buttons to anything. ##
        self.Style = ("""
        QWidget {
            background-color: #484848;
            color: white;
        }

        QTabWidget::pane {
            border: none;
        }

        QTabWidget {
        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #303030, stop: 0.9 #484848);
        }

        QTabBar {
            background-color: #313131;
        }

        QTabBar::tab {
            color: rgb(186,186,186);
            background-color: #606060;
            border: 2px solid #404040;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            border-bottom: none;
            min-width: 15ex;
            min-height: 7ex;
        }

        QTabBar::tab:selected {
            color: rgb(186,186,186);
            background-color: #484848;
        }
        QTabBar::tab:!selected {
            margin-top: 6px;
        }

        QTabWidget::tab-bar {
            border-top: 1px solid #505050;
        }

        QLineEdit {
            background-color: #303030;
            color: rgb(186,186,186);
            border-radius: 5px;
            padding: 0 3px;

        }
        QLineEdit:disabled {
            background-color: #303030;
            color: #505050;
            border-radius: 5px;
        }

        QTextEdit {
            background-color: #484848;
            color: rgb(186,186,186);
            border: none;
        }

        QTextEdit#TextFileEdit {
            background-color: #303030;
            color: rgb(186,186,186);
            border-radius: 5px;
        }

        QScrollBar:vertical {
            border: none;
            background-color: rgba(255,255,255,0);
            width: 10px;
            margin: 0px 0px 1px 0px;
        }

        QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
            border: none;
            background: none;
        }

        QScrollBar::handle:vertical {
            background: #303030;
            color: red;
            min-height: 20px;
            border-radius: 5px;
        }

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical  {
            background: none;
        }

        QPushButton {
            background-color: #303030;
            color: white;
            border: 1px grey;
            border-radius: 5px;
            border-style: solid;
            width: 60px;
            height: 20px;
        }

        QPushButton:disabled {
            background-color: #484848;
            color: grey;
        }
        QPushButton:pressed {
            background-color: #101010;
            color: white;
        }

        QCheckBox::indicator:unchecked {
            image: url(""" + self.unchecked_icon + """);
        }

        QCheckBox::indicator:checked {
            image: url(""" + self.checked_icon + """);
        }

        QTreeWidget {
            selection-color: red;
            border: none;
            outline: none;
            outline-width: 0px;
            selection-background-color: blue;
        }       

        QTreeWidget::item {
            height: 16px;
        }

        QTreeWidget::item:disabled {
            color: grey;
        }

        QTreeWidget::item:hover, QTreeWidget::item:selected {
            background-color: transparent;
            color: white;
        }

        QTreeWidget::indicator:checked {
            image: url(""" + self.checked_icon + """);
        }
        QTreeWidget::indicator:unchecked {
            image: url(""" + self.unchecked_icon + """);
        }

        """)

        self.main_tab.setStyleSheet(self.Style)

        # Set window title.
        self.main_tab.setWindowTitle('GUI')
        self.main_tab.setMinimumWidth(340)
        self.main_tab.setMinimumHeight(200)

        self.main_tab.setWindowIcon(self.Windicon)

        # Shows the main window.
        self.main_tab.show()

        # Sets the lineEdit for youtube links and paramters as focus. For easier writing.
        self.tab1_lineedit.setFocus()

        # Adds actions to the btt
        # Start buttons starts download
        self.tab1_start_btn.clicked.connect(self.start_DL)
        # Stop button kills the process, aka youtube-dl.
        self.tab1_stop_btn.clicked.connect(self.kill)
        # Close button closes the window/process.
        self.tab1_close_btn.clicked.connect(self.main_tab.close)
        # Starts self.update, locate_program_path checks for updates.
        self.tab4_update_btn.clicked.connect(self.update)
        self.tab4_dirinfo_btn.clicked.connect(self.dirinfo)
        self.tab4_test_btn.clicked.connect(self.reset_settings)

        # When statechanged, then the slotcahnge fuction is called. Checks if the process is running and enables/disables buttons.
        self.stateChanged.connect(self.slot_changed)
        # When the check button is checked or unchecked, calls function checked.
        # self.multiDL=self.Wid2.findChild(QCheckBox,'dl from textfile')
        self.tab1_checkbox.stateChanged.connect(self.is_batch_dl_checked)
        # When loadbutton is clicked, launch load textfile.
        self.tab3_loadButton.clicked.connect(self.load_text_from_file)
        # When savebutton clicked, save text to document.
        self.tab3_saveButton.clicked.connect(self.save_text_to_file)
        self.YTW_TextEdit.textChanged.connect(self.enable_saving)
        self.tab4_txt_location_btn.clicked.connect(self.textfile_dialog)

        self.shortcut = QShortcut(QKeySequence("Ctrl+S"), self.YTW_TextEdit)

        self.shortcut.activated.connect(self.slot)

        # Color specific text elements in textedit! More for future references or oppurtunities.
        # redText = """<span style=\"color:#ff0000;\" >"""
        # redText+=("I want this text red")
        # redText+=("</span>")
        # self.edit.append(redText)

        # Runs the startup function.
        if self.youtube_dl_path is None:
            self.tab1_textbrowser.append(self.color_text('\nNo youtube-dl.exe found! Add to path, '
                                                         'or make sure it\'s in the same folder as this program. '
                                                         'Then close and reopen this program.', 'darkorange', 'bold'))
            self.tab4_update_btn.setDisabled(True)

        # for i in range(self.tab2_options.topLevelItemCount()):
        #    self.paramchanger(self.tab2_options.topLevelItem(i))
        self.dl_naming_changer()

        self.RUNNING = False
        self.enable_start()
        self.SAVED = True



    def dl_naming_changer(self):
        def namer(location):
            location = location.replace('%(title)s.%(ext)s', '')
            if len(location) > 15:
                shortlocation = 0
                times = 0
                for number, letter in enumerate(reversed(location)):
                    if letter == '/':
                        shortlocation = -number - 1
                        times += 1
                        if times == 3:
                            break

                location = location[0:3] + '...' + location[shortlocation:]
            if not location[-1] == '/':
                location += '/'
            return location

        self.tab2_options.blockSignals(True)

        for i in range(self.tab2_options.topLevelItemCount()):
            item = self.tab2_options.topLevelItem(i)
            if item.data(0, 32) == 'Download location':
                for number in range(item.childCount()):
                    item.child(number).setData(0, 0,
                                               namer(item.child(number).data(0, 0)).replace('%(title)s.%(ext)s', ''))
                    item.child(number).setToolTip(0,item.child(number).data(0,32).replace('%(title)s.%(ext)s', ''))
                if item.checkState(0) == Qt.Checked:
                    for number in range(item.childCount()):
                        if item.child(number).checkState(0) == Qt.Checked:
                            self.tab2_download_lineedit.setText(item.child(number).data(0, 0))
                else:
                    self.tab2_download_lineedit.setText('DL')
                    self.tab2_download_lineedit.setToolTip('DL')
        self.tab2_options.blockSignals(False)

    def testfunction(self, location):
        for i in range(self.tab2_options.topLevelItemCount()):
            try:
                if self.tab2_options.topLevelItem(i).data(0, 32) == 'Download location':
                    if len(location) > 15:
                        tooltip = location
                        times = 0
                        for number, letter in enumerate(reversed(location)):
                            if letter == '/':
                                shortlocation = -number - 1
                                times += 1
                                if times == 2:
                                    break
                        location = location[0:3] + '...' + location[shortlocation:]

                    else:
                        tooltip = location
                    if not location[-1] == '/':
                        location += '/'

                    self.tab2_options.blockSignals(True)

                    print('location:', location)
                    print('tooltip:', tooltip)
                    sub = self.tab2_options.makeOption(name=tooltip,
                                                       parent=self.tab2_options.topLevelItem(i),
                                                       checkstate=False,
                                                       level=1,
                                                       tooltip=tooltip,
                                                       dependency=None,
                                                       subindex=None)
                    sub.setData(0, 0, location)

                    A = sub.parent().takeChild(sub.parent().indexOfChild(sub))

                    self.tab2_options.topLevelItem(i).insertChild(0, A)

                    # self.tab2_options.topLevelItem(i).
                    # self.tab1_textbrowser.append('Adding option.'+str(self.tab2_options.topLevelItem(i).childCount()))

                    for number in range(sub.parent().childCount()):
                        sub.parent().child(number).setData(0, 35, number)

                    if self.Settings['Settings']['Download location']['options'] is None:
                        self.Settings['Settings']['Download location']['options'] = [tooltip + '/%(title)s.%(ext)s']
                    else:
                        if self.tab2_options.topLevelItem(i).childCount() >= 4:
                            self.Settings['Settings']['Download location']['options']: list
                            self.Settings['Settings']['Download location']['options'].insert(0,
                                                                                             tooltip + '/%(title)s.%(ext)s')

                            del self.Settings['Settings']['Download location']['options'][3:]
                            print('DL, options', self.Settings['Settings']['Download location']['options'])
                        else:
                            print('Not 4 subs')
                            self.Settings['Settings']['Download location']['options'].insert(0,
                                                                                             tooltip + '/%(title)s.%(ext)s')

                    if self.tab2_options.topLevelItemCount() >= 3:
                        self.tab2_options.topLevelItem(i).removeChild(self.tab2_options.topLevelItem(i).child(3))

                    self.tab2_options.blockSignals(False)

                    # self.tab2_download_lineedit.setText(location)
                    # self.tab2_download_lineedit.setToolTip(tooltip)

                    sub.parent().setCheckState(0, Qt.Checked)
                    sub.setCheckState(0, Qt.Checked)

                    self.write_setting(self.Settings)

            except Exception as  e:
                # print(e)
                traceback.print_exc()

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    @staticmethod
    def write_default_settings(All=False):
        if All == True:
            Settings = {}
            Settings['Settings'] = {}
            Settings['Other stuff'] = {
                'multidl_txt': ''
            }
            Settings['Settings']['Convert to audio'] = {
                "Active option": 0,
                "Command": "-x --audio-format {} --audio-quality 0",
                "dependency": None,
                "options": ['mp3'],
                "state": True,
                "tooltip": "Convert to selected audio format."
            }
            Settings['Settings']["Add thumbnail"] = {
                "Active option": 0,
                "Command": "--embed-thumbnail",
                "dependency": 'Convert to audio',
                "options": None,
                "state": True,
                "tooltip": "Include thumbnail on audio files."
            }
            Settings['Settings']['Ignore errors'] = {
                "Active option": 0,
                "Command": "-i",
                "dependency": None,
                "options": None,
                "state": True,
                "tooltip": "Ignores errors, and jumps to next element instead of stopping."
            }
            Settings['Settings']['Download location'] = {
                "Active option": 0,
                "Command": "-o {}",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Select download location."
            }
            Settings['Settings']['Strict file names'] = {
                "Active option": 0,
                "Command": "--restrict-filenames",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Sets strict naming, to prevent unsupported characters in names."
            }
            Settings['Settings']['Keep archive'] = {
                "Active option": 0,
                "Command": "--download-archive {}",
                "dependency": None,
                "options": ['Archive.txt'],
                "state": True,
                "tooltip": "Saves links to a textfile to avoid duplicate downloads later."
            }
            with open('Settings.json', 'w') as f:
                json.dump(Settings, f, indent=4, sort_keys=True)
            return Settings
        else:
            if os.path.isfile('Settings.json'):
                with open('Settings.json', 'r') as f:
                    return json.load(f)
            else:
                return GUI.write_default_settings(All=True)
    def check_settings_integrity(self):
        # Base info.
        BaseSettings = ['Convert to audio',
                        'Add thumbnail',
                        'Ignore errors',
                        'Download location',
                        'Strict file names',
                        'Keep archive']

        if not self.Settings:
            raise SettingsError('Empty settings file!')

        MissingSettings = []
        for option in BaseSettings:
            if not option in self.Settings['Settings']:
                MissingSettings.append(option)
        if MissingSettings:
            raise SettingsError('\n'.join(['Settingfile is corrupt/missing:','-'*20,*MissingSettings,'-'*20]))

        if not self.Settings['Settings']['Download location']['options']:
            self.Settings['Settings']['Download location']['options'] = [self.workDir+'/DL/%(title)s.%(ext)s']

        for option in self.Settings['Settings'].keys():
            if self.Settings['Settings'][option]['options'] is not None:
                if self.Settings['Settings'][option]['Active option'] >= len(self.Settings['Settings'][option]['options']):
                    self.Settings['Settings'][option]['Active option'] = 0

        self.write_setting(self.Settings)



    def update_setting(self, diction: dict, section: str, key: str, value):
        diction[section][key] = value
        self.write_setting(diction)

    def update_paramters(self, diction, setting, state):
        diction['Settings'][setting]['state'] = state
        self.write_setting(diction)

    def update_options(self, diction, setting, index):
        diction['Settings'][setting]['Active option'] = index
        self.write_setting(diction)

    def reset_settings(self):
        warning_window = QMessageBox(parent=self.main_tab)
        # confirm1.setStyleSheet(self.Style)
        warning_window.setWindowTitle('Warning!')
        warning_window.setText('Restart required!')
        warning_window.setWindowIcon(self.Alerticon)
        warning_window.setInformativeText(
            'To reset the settings, the program has to be restarted. Do you want to reset and exit?')
        warning_window.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result1 = warning_window.exec()
        if result1 == QMessageBox.Yes:
            self.write_default_settings(All=True)
            qApp.exit(GUI.EXIT_CODE_REBOOT)


    @staticmethod
    def write_setting(diction):
        with open('Settings.json', 'w') as f:
            json.dump(diction, f, indent=4, sort_keys=True)

    def paramchanger(self, item: QTreeWidgetItem):
        if item.data(0, 33) == 0:
            if item.checkState(0) == Qt.Checked:
                self.update_paramters(self.Settings, item.data(0, 32), True)
                if item.data(0, 32) == 'Download location':
                    for i in range(item.childCount()):
                        self.paramchanger(item.child(i))
            else:
                self.update_paramters(self.Settings, item.data(0, 32), False)
                if item.data(0, 32) == 'Download location':
                    self.tab2_download_lineedit.setText('DL')
                    self.tab2_download_lineedit.setToolTip('DL')
        elif item.data(0, 33) == 1:
            self.update_options(self.Settings, item.parent().data(0, 32), item.data(0, 35))
            if item.parent().data(0, 32) == 'Download location':
                if item.checkState(0) == Qt.Checked:
                    self.tab2_download_lineedit.setText(item.data(0, 0))
                    print('item data 32', item.data(0, 32))
                    self.tab2_download_lineedit.setToolTip(item.data(0, 32).replace('%(title)s.%(ext)s', ''))

    def locate_program_path(self, program):
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

    def color_text(self, text, color='darkorange', extra='bold', sections=None):
        text=text.replace('\n', '<br>')

        if not sections:

            string = ''.join(["""<span style=\"color:""" + str(color) + '; font-weight:' + extra + """;\" >""",
                            text,
                            "</span>"]
                            )
        else:
            worktext = text[sections[0]:sections[1]]
            string = ''.join([text[:sections[0]],
                        """<span style=\"color:""" + str(color) + '; font-weight:' + extra + """;\" >""",
                        worktext,
                        "</span>",
                        text[sections[1]:]]
                        )
        return string

    def dirinfo(self):

        Filedir = os.path.dirname(os.path.abspath(__file__))

        Debug = [self.color_text('\nYoutube-dl.exe path:'), self.youtube_dl_path,
                 self.color_text('Filedir:'), Filedir,
                 self.color_text('Workdir:'), self.workDir,
                 self.color_text('Youtube-dl working directory:'), self.program_workdir,
                 self.color_text('\nIcon paths:'),
                 self.checked_icon, self.unchecked_icon, self.alert_icon,
                 self.window_icon]

        for i in Debug:
            self.tab1_textbrowser.append(str(i))

        self.tab1_textbrowser.append(self.color_text('\nChecking if icons are in place:', 'darkorange', 'bold'))
        # Rich text uses <br> instead of \n
        # Color fuction takes care of it.

        for i in self.iconlist:
            if i is not None:
                try:
                    if os.path.isfile(str(i)):
                        self.tab1_textbrowser.append('Found: ' + os.path.split(i)[1])
                    else:
                        self.tab1_textbrowser.append('Missing in: ' + i)
                except IndexError:
                    if os.path.isfile(str(i)):
                        self.tab1_textbrowser.append('Found: ' + i)
                    else:
                        self.tab1_textbrowser.append('Missing in: ' + i)

    def setProgramWorkDir(self):
        try:
            work_dir = sys._MEIPASS
        except Exception:
            work_dir = os.path.abspath('.')
            print(work_dir)
        self.setWorkingDirectory(work_dir)
        return work_dir

    def update(self):
        self.tab1_textbrowser.clear()
        self.main_tab.setCurrentIndex(0)
        self.start(self.youtube_dl_path, ['-U'])

    # When the process is started/stopped then this runs.
    def slot_changed(self, newState):
        # If it's not running, start button is enabled, and stop button disabled.
        if newState == QProcess.NotRunning:
            self.tab1_start_btn.setDisabled(False)
            self.tab1_stop_btn.setDisabled(True)
            self.RUNNING = False

            self.tab1_textbrowser.append('\nDone\n')
            self.tab1_textbrowser.append(f'Error count: '
                                         f'{self.Errors if self.Errors ==0 else self.color_text(str(self.Errors),"darkorange","bold")}.')
            self.Errors = 0

        # Vise versa of the above.
        elif newState == QProcess.Running:
            self.tab1_start_btn.setDisabled(True)
            self.tab1_stop_btn.setDisabled(False)
            self.RUNNING = True

    def savefile_dialog(self):
        Location = QFileDialog.getExistingDirectory(parent=self.main_tab)
        if Location == '':
            pass
        elif os.path.exists(Location):
            self.testfunction(Location)

    def textfile_dialog(self):
        Location = \
            QFileDialog.getOpenFileName(parent=self.main_tab, filter='*.txt',
                                        caption='Select textfile with video links')[0]
        if Location == '':
            pass
        elif os.path.isfile(Location):
            if not self.SAVED:
                confirmchange = QMessageBox()
                confirmchange.setText('Selecting new textfile, this will load over the text in the download list tab!')
                confirmchange.setWindowIcon(self.Alerticon)
                confirmchange.setWindowTitle('Warning!')
                confirmchange.setInformativeText('Do you want to load over the unsaved changes?')
                confirmchange.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                result = confirmchange.exec()
                if result == QMessageBox.Yes:
                    self.update_setting(self.Settings, 'Other stuff', 'multidl_txt', Location)
                    self.tab4_txt_lineedit.setText(Location)
                    self.SAVED = True
                    self.load_text_from_file()

            else:
                self.update_setting(self.Settings, 'Other stuff', 'multidl_txt', Location)
                self.tab4_txt_lineedit.setText(Location)
                self.SAVED = True
                self.load_text_from_file()
        else:
            Message = QMessageBox()
            Message.setWindowIcon(self.Alerticon)
            Message.setWindowTitle('Error!')
            Message.setText('Could not find the file!')

            Message.exec()
            # Check if the checkbox is toggled, and disables the line edit if it is.
            #  Also disables start button if lineEdit is empty and checkbox is not checked

    def is_batch_dl_checked(self):
        self.tab1_lineedit.setDisabled(self.tab1_checkbox.isChecked())
        self.tab1_start_btn.setDisabled(
            (not (self.tab1_checkbox.checkState() == 2 or (self.tab1_lineedit.text() != '')) == True) or self.RUNNING)

    def slot(self):
        self.save_text_to_file()

    # The process for starting the download. Clears text edit.

    def format_in_list(self, command, option):
        splitcommand = command.split()
        for index, item in enumerate(splitcommand):
            if item == '{}':
                splitcommand[index] = item.format(option)
                return splitcommand
        return splitcommand

    def start_DL(self):
        self.tab1_textbrowser.clear()
        Command = []

        if self.tab1_checkbox.isChecked():
            Command += (' -a {txt}'.split())
            txt = self.Settings['Other stuff']['multidl_txt']
        else:
            Command.append('{txt}')
            txt = self.tab1_lineedit.text()

        print(txt)
        print(Command)

        for i in range(len(Command)):
            Command[i] = Command[i].format(txt=txt)
        print(Command)
        # print('1')

        for parameter, options in self.Settings['Settings'].items():
            # print(options['Command'])
            if parameter == 'Download location':
                if options['state']:
                    add = self.format_in_list(options['Command'],
                                              options['options'][options['Active option']])
                    Command += add
                else:
                    Command += ['-o', self.workDir + '/DL/%(title)s.%(ext)s']
            else:
                if options['state']:
                    add = self.format_in_list(options['Command'],
                                              options['options'][options['Active option']] if options[
                                                                                                  'options'] is not None or
                                                                                              options[
                                                                                                  'options'] else '')
                    Command += add
        try:
            if self.ffmpeg_path:
                Command += ['--ffmpeg-location',self.ffmpeg_path]
        except Exception as e:
            print(e)
        self.Errors = 0
        print(Command)
        self.start(self.youtube_dl_path, Command)
        self.tab1_textbrowser.append('Starting...\n')

    def start_download(self):
        """
        Remove later, doesn't work anymore.
        """

        self.tab1_textbrowser.clear()
        Command = ''
        A = self.read_settings()
        if A.getboolean('multidl', 'state'):
            Command += ' -a {DL}'
        else:
            Command += ' {DL}'
        for k in A['Default values']:
            try:
                if A.getboolean('Default values', k):
                    Command += '  ' + A.get('Parameters', k)
            except:
                self.tab1_textbrowser.append((
                    '<span style=\"color: darkorange; font-weight: bold;\">ERROR</span>: Parameter \'' + str(
                        k).capitalize() + '\' Skipped due to lacking or invalid entry in Paramters, in Settings.ini.\n'))
        if A.getboolean('multidl', 'state'):
            DL = (A.get('User Defined', 'txt_location').replace(' ', '[Space_Position]'))
        else:
            DL = self.tab1_lineedit.text()
        if A.getboolean('Default values', 'output'):
            DLto = str(A.get('User Defined', 'dl_location')).replace(' ', '[Space_Position]') + '%(title)s.%(ext)s'
        else:
            DLto = ''
            Command += ' -o "%(title)s.%(ext)s"'

        # print(Command)
        Command = Command.format(DL=DL, DLto=DLto)
        # print(Command)#DeBUG
        # print(Command.split()) #debUG
        Command = Command.split()
        for number, item in enumerate(Command):
            Command[number] = Command[number].replace('[Space_Position]', ' ')
        # self.edit.append(Command) #DebugGing
        # print(Command) # dEBUG
        self.start(self.youtube_dl_path, Command)

    def cmdoutput(self, info):
        if info.startswith('ERROR'):
            self.Errors += 1
        while info.startswith(' '):
            info = info[1:]

        regexp = re.compile('|'.join(map(re.escape, self.substrs)))

        return regexp.sub(lambda match: self.replace_dict[match.group(0)], info)

    # appends youtube-dl output to textedit (self.edit).
    def read_stdoutput(self):
        data = self.readAllStandardOutput().data()
        text = data.decode('utf-8', 'ignore').strip()
        text = self.cmdoutput(text)

        try:
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
            lastLine = self.tab1_textbrowser.textCursor().selectedText()

            # Check if a percentage has already been placed.
            if "%" in lastLine and 'ETA' in lastLine:
                self.tab1_textbrowser.textCursor().removeSelectedText()
                self.tab1_textbrowser.textCursor().deletePreviousChar()
                # Last line of text
                self.tab1_textbrowser.append(self.color_text(text.split("[download]")[-1][1:],
                                                             color='lawngreen',
                                                             extra='bold',
                                                             sections=[0,5]))
                if '100%' in text:
                    self.tab1_textbrowser.append('')

            else:
                if "%" in text and 'ETA' in text:
                    # Last line of text
                    self.tab1_textbrowser.append(self.color_text(text.split("[download]")[-1][1:],
                                                                 color='lightgreen',
                                                                 extra='bold',
                                                                 sections=[0,5]))
                elif '[download]' in text:
                    self.tab1_textbrowser.append(''.join([text.replace('[download] ',''), '\n']))
                else:
                    self.tab1_textbrowser.append(''.join([text,'\n']))

            if keepPos:
                scrollbar.setSliderPosition(place)
            else:
                scrollbar.setSliderPosition(scrollbar.maximum())

        except:
            traceback.print_exc()

    # Startup function, sets the startbutton to disabled, if lineEdit is empty, and disables the lineEdit if the textbox is checked.
    # Stop button is set to disabled, since no process is running.
    def enable_start(self):
        self.tab1_start_btn.setDisabled((self.tab1_lineedit.text() == "") or (self.RUNNING is True))
        self.tab1_lineedit.setDisabled(self.tab1_checkbox.isChecked() is True)
        self.tab1_stop_btn.setDisabled((self.RUNNING is False))
        self.is_batch_dl_checked()

    def load_text_from_file(self):
        if ((self.YTW_TextEdit.toPlainText() == '') or (not self.tab3_saveButton.isEnabled())) or self.SAVED:
            if os.path.isfile(self.tab4_txt_lineedit.text()):
                self.YTW_TextEdit.clear()
                with open(self.tab4_txt_lineedit.text(), 'r') as f:
                    for line in f.readlines():
                        self.YTW_TextEdit.append(line.strip())
                self.YTW_TextEdit.append('')
                self.YTW_TextEdit.setFocus()
                self.tab3_saveButton.setDisabled(True)
                self.SAVED = True
            else:
                if self.tab4_txt_lineedit.text() == '':
                    warning = 'No textfile selected!'
                else:
                    warning = 'Could not find file!'
                warning_window = QMessageBox(parent=self.main_tab)
                warning_window.setWindowIcon(self.Alerticon)
                warning_window.setWindowTitle('Error!')
                warning_window.setText(warning)

                warning_window.exec()
        else:
            if self.tab4_txt_lineedit.text() == '':
                self.SAVED = True
                self.load_text_from_file()
            else:
                warning_window = QMessageBox(parent=self.main_tab)
                warning_window.setText('Overwrite?')
                warning_window.setWindowIcon(self.Alerticon)
                warning_window.setInformativeText('Do you want to load over the unsaved changes?')
                warning_window.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                result = warning_window.exec()
                if result == QMessageBox.Yes:
                    self.SAVED = True
                    self.load_text_from_file()

    def save_text_to_file(self):
        if not self.tab4_txt_lineedit.text() == '':
            with open(self.tab4_txt_lineedit.text(), 'w') as f:
                for line in self.YTW_TextEdit.toPlainText():
                    f.write(line)
            self.tab3_saveButton.setDisabled(True)
            self.SAVED = True
        else:
            warning_window = QMessageBox(parent=self.main_tab)
            warning_window.setText('No textfile selected!')
            warning_window.setWindowTitle('Warning!')
            warning_window.setInformativeText('Do you want to create one?')
            warning_window.setWindowIcon(self.Alerticon)
            warning_window.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            result = warning_window.exec()
            if result == QMessageBox.Yes:
                Save = QFileDialog.getSaveFileName(parent=self.main_tab, caption='Save as', filter='*.txt')
                if not Save[0] == '':
                    print(Save[0])
                    with open(Save[0], 'w') as f:
                        for line in self.YTW_TextEdit.toPlainText():
                            f.write(line)
                            self.update_setting(self.Settings, 'Other stuff', 'multidl_txt', Save[0])
                    print('1')
                    self.tab4_txt_lineedit.setText(Save[0])
                    self.tab3_saveButton.setDisabled(True)
                    self.SAVED = True

    def enable_saving(self):
        self.tab3_saveButton.setDisabled(False)
        self.SAVED = False

    def confirm(self):
        if self.RUNNING:
            warning_window = QMessageBox(parent=self.main_tab)
            # confirm1.setStyleSheet(self.Style)
            warning_window.setWindowTitle('Still downloading!')
            warning_window.setText('Want to quit?')
            warning_window.setWindowIcon(self.Alerticon)
            warning_window.setInformativeText(
                'Do you want to close without letting youtube-dl finish? Will likely leave unwanted/incomplete files in the download location.')
            warning_window.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            result1 = warning_window.exec()
            if result1 != QMessageBox.Yes:
                return None

        if ((self.YTW_TextEdit.toPlainText() == '') or (not self.tab3_saveButton.isEnabled())) or self.SAVED:
            self.sendclose.emit()
        else:
            warning_window = QMessageBox(parent=self.main_tab)
            # confirm.setParent(self.main_tab)
            # confirm.setStyleSheet(self.Style)
            warning_window.setWindowTitle('Unsaved changes in list!')
            warning_window.setWindowIcon(self.Alerticon)
            warning_window.setText('Save?')
            warning_window.setInformativeText('Do you want to save before exiting?')
            warning_window.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            result = warning_window.exec()
            if result == QMessageBox.Yes:
                self.save_text_to_file()
                self.sendclose.emit()
            elif result == QMessageBox.Cancel:
                pass
            else:
                self.sendclose.emit()


class SettingsError(Exception):
    pass

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMessageBox
    EXIT_CODE = GUI.EXIT_CODE_REBOOT
    while EXIT_CODE == -123456789:
        try:
            app = QApplication(sys.argv)
            qProcess = GUI()

            EXIT_CODE = app.exec_()
            app= None
        except (SettingsError,json.decoder.JSONDecodeError) as e :
            A = QMessageBox.warning(None, 'Corrupt settings', ''.join([str(e),'\nRestore default settings?']), buttons=QMessageBox.Yes | QMessageBox.No)
            if A == QMessageBox.Yes:
                GUI.write_default_settings(True)
                EXIT_CODE = -123456789
            app = None

