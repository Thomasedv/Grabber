import json
import os.path
import re
import sys
import traceback
from collections import deque

from PyQt5.QtCore import QProcess, pyqtSignal, Qt, QMimeData
from PyQt5.QtGui import QFont, QKeySequence, QIcon, QTextCursor, QClipboard, QGuiApplication
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QLineEdit, \
    QShortcut, QFileDialog, QGridLayout, QTextBrowser, QTreeWidgetItem, qApp, QAction, QMenu, \
    QFrame, QDialog

from Modules.dialog import Dialog
from Modules.download_element import Download
from Modules.download_tab import MainTab
from Modules.parameterTree import ParameterTree
from Modules.tabWidget import Tabwidget
from utils.utilities import path_shortener, color_text, format_in_list, SettingsError


class GUI(QWidget):
    """
    Runnable class that makes a wrapper for youtube-dl.
    """
    sendClose = pyqtSignal()
    EXIT_CODE_REBOOT = -123456789

    def __init__(self):
        """
        GUI that wraps a youtube-dl.exe to download videos and more.
        """
        super(GUI, self).__init__()

        # starts checks
        self.initial_checks()

        # Builds GUI and everything related to that.
        self.build_gui()

        # Set the channel to merged.
        # self.setProcessChannelMode(QProcess.MergedChannels)

        # connects program output to the GUI part.
        # self.readyReadStandardOutput.connect(self.read_stdoutput)

    def initial_checks(self):
        """Loads settings and finds necessary files. Checks the setting file for errors."""
        self.settings = self.write_default_settings(reset=False)

        # Find resources.
        # Find youtube-dl
        self.youtube_dl_path = self.locate_program_path('youtube-dl.exe')
        self.ffmpeg_path = self.locate_program_path('ffmpeg.exe')
        self.program_workdir = self.get_program_working_directory().replace('\\', '/')
        self.workDir = os.getcwd().replace('\\', '/')
        self.license_path = self.resource_path('LICENSE')

        self.local_dl_path = ''.join([self.workDir, '/DL/'])

        self.check_settings_integrity()
        # NB! For stylesheet stuff, the slashes '\' in the path, must be replaced with '/'.
        # Use replace('\\', '/') on path.
        self.icon_list = []

        # Find icon paths
        self.unchecked_icon = self.resource_path('GUI\\Icon_unchecked.ico').replace('\\', '/')
        self.checked_icon = self.resource_path('GUI\\Icon_checked.ico').replace('\\', '/')
        self.alert_icon = self.resource_path('GUI\\Alert.ico').replace('\\', '/')
        self.window_icon = self.resource_path('GUI\\YTDLGUI.ico').replace('\\', '/')

        # Adding icons to list. For debug purposes.
        self.icon_list.append(self.unchecked_icon)
        self.icon_list.append(self.checked_icon)
        self.icon_list.append(self.alert_icon)
        self.icon_list.append(self.window_icon)

        # Creating icon objects for use in message windows.
        self.alertIcon = QIcon()
        self.windowIcon = QIcon()

        # Setting the icons image, using found paths.
        self.alertIcon.addFile(self.alert_icon)
        self.windowIcon.addFile(self.window_icon)

    def build_gui(self):
        """Generates the GUI elements, and hooks everything up."""
        # TODO: Separate the GUI elements into their own class/file.
        # Denotes if the process(youtube-dl) is running.
        self.RUNNING = False
        # Denotes if the textfile is saved.
        self.SAVED = True
        # Error count is provided after process quit.
        self.Errors = 0
        # Indicates if license is shown. (For license tab)
        self.license_shown = False

        # Downloda queue
        self.queue = deque()  # TODO: Move to init!

        self.active_download = None

        # Used later for checking the text feed from youtuibne-dl.
        # TODO: See what can be done with this part of the code. Why have this here?
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
                        QMenu::separator {{
                            height: 2px;
                        }}
                        QFrame#line {{
                            color: #303030;
                        }}
                        
                        QTabWidget::pane {{
                            border: none;
                        }}
                        
                        QMenu::item {{
                            border: none;
                            padding: 3px 20px 3px 5px
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
                            border: 1px solid transparent;
                            border-radius: 5px;
                            width: 60px;
                            height: 20px;
                        }}

                        QPushButton:disabled {{
                            border: 1px solid #303030;
                            background-color: transparent;
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

        ## Set font for tab 4.
        self.font = QFont()
        self.font.setFamily('Consolas')
        self.font.setPixelSize(13)

        # Sorts the parameters, so that favorite ones are added to the favorite widget.
        options = {k: v for k, v in self.settings['Settings'].items() if k not in self.settings['Favorites']}
        favorites = {i: self.settings['Settings'][i] for i in self.settings['Favorites']}

        ### Main widget. This will be the ones that holds everything.
        ## Create top level tab widget system for the UI.
        self.main_tab = Tabwidget()
        self.main_tab.onclose.connect(self.confirm)
        self.sendClose.connect(self.main_tab.closeE)

        ## Connecting stuff for tab 1.

        # Start buttons starts download

        self.tab1 = MainTab(self)

        self.tab1.start_btn.clicked.connect(self.queue_dl)
        # Stop button kills the process, aka youtube-dl.
        self.tab1.stop_btn.clicked.connect(self.stop_download)
        # Close button closes the window/process.
        self.tab1.close_btn.clicked.connect(self.main_tab.close)
        # When the check button is checked or unchecked, calls function checked.
        self.tab1.checkbox.stateChanged.connect(self.allow_start)
        # Connects actions to text changes and adds action to when you press Enter.
        self.tab1.lineedit.textChanged.connect(self.allow_start)
        # Starts downloading
        self.tab1.lineedit.returnPressed.connect(self.tab1.start_btn.click)

        ### Tab 2
        #  Building widget tab 2.

        # Button for browsing download location.
        self.tab2_browse_btn = QPushButton('Browse')

        # Label for the lineEdit.
        self.tab2_download_label = QLabel('Download to:')

        self.tab2_favlabel = QLabel('Favorites:')
        self.tab2_optlabel = QLabel('All settings:')

        # LineEdit for download location.
        self.tab2_download_lineedit = QLineEdit()
        self.tab2_download_lineedit.setReadOnly(True)

        if self.settings['Settings']['Download location']['options']:
            self.tab2_download_lineedit.setText('')
            self.tab2_download_lineedit.setToolTip(self.settings['Settings']['Download location']['options'][
                                                       self.settings['Settings']['Download location'][
                                                           'active option']].replace('%(title)s.%(ext)s', ''))
        else:
            # Should not be reachable anymore!
            self.tab2_download_lineedit.setText('DL')
            self.tab2_download_lineedit.setToolTip('Default download location.')

        # Sets up the parameter tree.
        self.tab2_options = ParameterTree(options)
        self.tab2_favorites = ParameterTree(favorites)
        self.tab2_favorites.favorite = True

        self.tab2_download_option = self.find_download_widget()
        self.custom_options()  # TODO: Refactor name to custom_option

        self.tab2_download_lineedit.setContextMenuPolicy(Qt.ActionsContextMenu)

        # Menu creation for tab2_download_lineedit
        menu = QMenu()
        # Makes an action for the tab2_download_lineedit
        open_folder_action = QAction('Open location', parent=self.tab2_download_lineedit)
        # open_folder_action.setEnabled(True)
        open_folder_action.triggered.connect(self.open_folder)

        copy_action = QAction('Copy', parent=self.tab2_download_lineedit)
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
        self.tab2_QV.addLayout(self.tab2_QH, stretch=0)

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

        self.grid.addWidget(self.tab2_favlabel, 1, 0)
        self.grid.addWidget(self.tab2_optlabel, 1, 1)
        self.grid.addWidget(self.frame, 2, 0)
        self.grid.addWidget(self.frame2, 2, 1)
        self.grid.addWidget(self.tab2_favorites, 3, 0, Qt.AlignTop)
        self.grid.addWidget(self.tab2_options, 3, 1, Qt.AlignTop)
        self.grid.setRowStretch(0, 0)
        self.grid.setRowStretch(1, 0)
        self.grid.setRowStretch(2, 0)
        self.grid.setRowStretch(3, 1)
        self.tab2_QV.addLayout(self.grid)

        # self.tab2_hdl_box = QHBoxLayout()
        # self.tab2_grid_layout.expandingDirections()
        # self.tab2_vdl_box = QVBoxLayout()
        # self.tab2_vdl_box.addWidget(self.tab2_options)
        # self.tab2_vdl_box.addStretch(1)
        # self.tab2_hdl_box.addLayout(self.tab2_vdl_box)
        # self.tab2_hdl_box.addWidget(self.tab2_favorites)

        # self.tab2_QV.addLayout(self.tab2_hdl_box)
        # self.tab2_QV.addStretch(1)

        # Create Qwidget for the layout for tab 2.
        self.tab2 = QWidget()
        # Adds the tab2 layout to the widget.
        self.tab2.setLayout(self.tab2_QV)

        ## Connection stuff tab 2.

        self.tab2_download_lineedit.addAction(open_folder_action)
        self.tab2_download_lineedit.addAction(copy_action)

        self.tab2_options.itemChanged.connect(self.parameter_updater)
        self.tab2_options.move_request.connect(self.move_item)
        self.tab2_options.itemRemoved.connect(self.item_removed)
        self.tab2_options.addOption.connect(self.add_option)

        self.tab2_favorites.itemChanged.connect(self.parameter_updater)
        self.tab2_favorites.move_request.connect(self.move_item)
        self.tab2_favorites.itemRemoved.connect(self.item_removed)
        self.tab2_favorites.addOption.connect(self.add_option)

        self.tab2_browse_btn.clicked.connect(self.savefile_dialog)

        ### Tab 3.

        ## Widget creation tab 3.
        # Create textedit
        self.tab3_textedit = QTextEdit()
        self.tab3_textedit.setObjectName('TextFileEdit')

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
        # TODO: Refactor settings to not have the section "Other stuff"
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

        ## TEST TAB ##
        if __name__ == '__main__':
            # Only shows if core.py is run, not when main.py is.
            pass

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

        if self.settings['Other stuff']['select_on_focus']:
            self.main_tab.gotfocus.connect(self.window_focus_event)
        else:
            self.tab1.lineedit.setFocus()

        # Other functionality.
        self.shortcut = QShortcut(QKeySequence("Ctrl+S"), self.tab3_textedit)
        self.shortcut.activated.connect(self.tab3_saveButton.click)

        # Check for youtube
        if self.youtube_dl_path is None:
            self.tab4_update_btn.setDisabled(True)
            self.tab1.textbrowser.append(color_text('\nNo youtube-dl.exe found! Add to path, '
                                                    'or make sure it\'s in the same folder as this program. '
                                                    'Then close and reopen this program.', 'darkorange', 'bold'))

        # Renames items for download paths, adds tooltip. Essentially handles how the widget looks at startup.
        self.download_name_handler()
        # Ensures widets are in correct state at startup and when tab1.lineedit is changed.
        self.allow_start()
        # Shows the main window.
        self.main_tab.show()
        # Connect after show!!
        self.main_tab.resizedByUser.connect(self.resize_contents)
        # Sets the lineEdit for youtube links and paramters as focus. For easier writing.

    def item_removed(self, item: QTreeWidgetItem, index):
        """Parent who had child removed. Updates settings and numbering of data 35"""
        del self.settings['Settings'][item.data(0, 0)]['options'][index]
        option = self.settings['Settings'][item.data(0, 0)]['active option']
        option -= 1 if option > 0 else 0
        if not item.childCount():
            item.setCheckState(0, Qt.Unchecked)
            self.need_parameters.append(item.data(0, 32))
        self.write_setting(self.settings)

    def design_option_dialog(self, name, description):
        """
        Creates dialog for user input
        """
        dialog = Dialog(self.main_tab, name, description)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.option.text()
        return None

    def add_option(self, item: QTreeWidgetItem):
        """
        Check if parameter has a possible option parameter, and lets the user add on if one exist.
        """
        if item.data(0, 32) == 'Download location':
            self.alert_message('Error!', 'Please use the browse button\nto select download location!', None)
        elif '{}' in self.settings['Settings'][item.data(0, 32)]['command']:

            item.treeWidget().blockSignals(True)
            parameter = self.design_option_dialog(item.text(0), item.toolTip(0))

            if parameter:
                new_option = ParameterTree.make_option(parameter.strip(),
                                                       item,
                                                       True,
                                                       1,
                                                       None,
                                                       None,
                                                       0)

                move = item.takeChild(item.indexOfChild(new_option))
                item.insertChild(0, move)

                self.settings['Settings'][item.data(0, 32)]['options'].insert(0, parameter)
                for i in range(len(self.settings['Settings'][item.data(0, 32)]['options'])):
                    item.child(i).setData(0, 35, i)
                    if i == 0:

                        item.child(i).setCheckState(0, Qt.Checked)
                        item.child(i).setFlags(item.flags() ^ Qt.ItemIsUserCheckable)
                    else:
                        item.child(i).setCheckState(0, Qt.Unchecked)
                        item.child(i).setFlags(item.flags() | Qt.ItemIsUserCheckable)

                item.treeWidget().update_size()

                self.write_setting(self.settings)
            item.treeWidget().blockSignals(False)

        else:
            self.alert_message('Error!', 'The specified option does not take arguments!', None)
            print('Doesn\'t have an option')

    def move_item(self, item: QTreeWidgetItem, favorite: bool):
        """ Move an time to or from the favorites tree. """
        # print(favorite)
        self.blockSignals(True)
        if favorite:
            self.tab2_options.addTopLevelItem(item)
            # print('remove')
            self.settings['Favorites'].remove(item.data(0, 0))
        else:
            # print(favorite)
            self.tab2_favorites.addTopLevelItem(item)
            self.settings['Favorites'].append(item.data(0, 0))
        self.tab2_favorites.update_size()
        self.tab2_options.update_size()
        self.write_setting(self.settings)

        if item.checkState(0) == Qt.Checked:
            item.setExpanded(True)
        else:
            item.setExpanded(False)
        self.blockSignals(False)

    def resize_contents(self):
        """ Resized parameterTree widgets in tab2 to the window."""
        size = self.main_tab.height() - (self.frame.height() + self.tab2_download_lineedit.height()
                                         + self.tab2_favlabel.height() + self.main_tab.tabBar().height() + 40)
        ParameterTree.max_size = size
        self.tab2_options.setFixedHeight(size)
        self.tab2_favorites.setFixedHeight(size)

    def window_focus_event(self):
        """ Selects text in tab1 line edit on window focus. """
        # self.tab2_options.max_size =
        if self.tab1.lineedit.isEnabled():
            self.tab1.lineedit.setFocus()
            self.tab1.lineedit.selectAll()

    def copy_to_cliboard(self):
        """ Adds text to clipboard. """
        mime = QMimeData()
        mime.setText(self.tab2_download_lineedit.text())
        board = QGuiApplication.clipboard()
        board.setMimeData(mime, mode=QClipboard.Clipboard)

    def open_folder(self):
        """ Opens a folder at specified location. """
        # noinspection PyCallByClass
        QProcess.startDetached('explorer {}'.format(self.tab2_download_lineedit.toolTip().replace("/", "\\")))

    def custom_options(self):
        """Creates a custom option for the parameterTree that is favorite. """
        self.tab2_favorites.blockSignals(True)

        parent = ParameterTree.make_option(self.settings['Other stuff']['custom']['command'],
                                           self.tab2_favorites,
                                           self.settings['Other stuff']['custom']['state'],
                                           2,
                                           self.settings['Other stuff']['custom']['tooltip'])
        self.tab2_favorites.update_size()
        parent.setFlags(parent.flags() | Qt.ItemIsEditable)
        self.tab2_favorites.blockSignals(False)

    def download_name_handler(self):
        """ Formats download names and removes the naming string for ytdl. """
        # TODO: Reforamt code to not save the naming sting to the settings, rather append it on download start.
        for item in (*self.tab2_options.topLevelItems(), *self.tab2_favorites.topLevelItems()):
            if item.data(0, 32) == 'Download location':
                item.treeWidget().blockSignals(True)
                for number in range(item.childCount()):
                    item.child(number).setData(0, 0, path_shortener(item.child(number).data(0, 0)))
                if item.checkState(0) == Qt.Checked:
                    for number in range(item.childCount()):
                        if item.child(number).checkState(0) == Qt.Checked:
                            self.tab2_download_lineedit.setText(item.child(number).data(0, 0))
                            break
                    else:
                        print('WARNING! No selected download item, this should not happen.... ')
                        print('You messed with the settings... didn\'t you?!')
                        # raise SettingsError('Error, no active option!')
                else:
                    self.tab2_download_lineedit.setText(path_shortener(self.local_dl_path))
                    self.tab2_download_lineedit.setToolTip(self.local_dl_path)
                item.treeWidget().blockSignals(False)
                break

    def find_download_widget(self):
        """ Finds the download widget. """
        # TODO: Refactor to check the settings file/object, not the parameterTrees.
        for item in self.tab2_favorites.topLevelItems():
            if item.data(0, 32) == 'Download location':
                return item
        for item in self.tab2_options.topLevelItems():
            if item.data(0, 32) == 'Download location':
                return item
        raise SettingsError('No download item found in settings.')

    def download_option_handler(self, full_path: str):
        """ Handles the download options. """
        # Adds new dl location to the tree and settings. Removes oldest one, if there is more than 3.
        # Remove try/except later.
        try:
            item = self.tab2_download_option
            if not full_path.endswith('/'):
                full_path += '/'
            short_path = path_shortener(full_path)
            names = [item.child(i).data(0, 0) for i in range(item.childCount())]
            # TODO: Remove the added thing to full_path below
            if short_path in names and full_path in self.settings['Settings']['Download location']['options']:
                self.alert_message('Warning', 'Option already exists!', '', question=False)
                return
            print('-' * 50)

            item.treeWidget().blockSignals(True)

            sub = ParameterTree.make_option(name=full_path,
                                            parent=item,
                                            checkstate=False,
                                            level=1,
                                            tooltip=full_path,
                                            dependency=None,
                                            subindex=None)
            sub.setData(0, 0, short_path)
            # print('sorting enabled?', item.treeWidget().isSortingEnabled())
            moving_sub = item.takeChild(item.indexOfChild(sub))

            item.insertChild(0, moving_sub)

            for number in range(item.childCount()):
                item.child(number).setData(0, 35, number)
                print(item.child(number).data(0, 0))

            if self.settings['Settings']['Download location']['options'] is None:
                self.settings['Settings']['Download location']['options'] = [full_path]
            else:
                self.settings['Settings']['Download location']['options'].insert(0, full_path)

            if item.childCount() >= 3:
                item.removeChild(item.child(3))

            item.treeWidget().update_size()

            item.treeWidget().setSortingEnabled(True)
            item.treeWidget().blockSignals(False)

            # self.tab2_download_lineedit.setText(location)
            # self.tab2_download_lineedit.setToolTip(tooltip)

            item.setCheckState(0, Qt.Checked)
            sub.setCheckState(0, Qt.Checked)

            self.write_setting(self.settings)
        except Exception as error:
            print(error)
            traceback.print_exc()

    @staticmethod
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    @staticmethod
    def write_default_settings(reset=False):
        """ Reads settings, or writes them in absent, or if instructed to. """
        if reset:
            settings = dict()
            settings['Profiles'] = {}
            settings['Favorites'] = []
            settings['Settings'] = {}
            settings['Other stuff'] = {
                'multidl_txt': '',
                'select_on_focus': True,
                'custom': {
                    "command": "Custom",
                    "state": False,
                    "tooltip": "Custom option, double click to edit."
                }
            }
            settings['Settings']['Convert to audio'] = {
                "active option": 0,
                "command": "-x --audio-format {}",
                "dependency": None,
                "options": ['mp3'],
                "state": False,
                "tooltip": "Convert video files to audio-only files\n"
                           "Requires ffmpeg, avconv and ffprobe or avprobe."
            }
            settings['Settings']["Add thumbnail"] = {
                "active option": 0,
                "command": "--embed-thumbnail",
                "dependency": 'Convert to audio',
                "options": None,
                "state": False,
                "tooltip": "Include thumbnail on audio files."
            }
            settings['Settings']['Audio quality'] = {
                "active option": 0,
                "command": "--audio-quality {}",
                "dependency": 'Convert to audio',
                "options": ['0', '5', '9'],
                "state": True,
                "tooltip": "Specify ffmpeg/avconv audio quality.\ninsert"
                           "a value between\n0 (better) and 9 (worse)"
                           "for VBR\nor a specific bitrate like 128K"
            }
            settings['Settings']['Ignore errors'] = {
                "active option": 0,
                "command": "-i",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Ignores errors, and jumps to next element instead of stopping."
            }
            settings['Settings']['Download location'] = {
                "active option": 0,
                "command": "-o {}",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Select download location."
            }
            settings['Settings']['Strict file names'] = {
                "active option": 0,
                "command": "--restrict-filenames",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Sets strict naming, to prevent unsupported characters in names."
            }
            settings['Settings']['Keep archive'] = {
                "active option": 0,
                "command": "--download-archive {}",
                "dependency": None,
                "options": ['Archive.txt'],
                "state": False,
                "tooltip": "Saves links to a textfile to avoid duplicate downloads later."
            }
            # settings['Settings']['Abort on error'] = {
            #     "active option": 0,
            #     "command": "--abort-on-error",
            #     "dependency": None,
            #     "options": None,
            #     "state": False,
            #     "tooltip": "Abort downloading of further videos if an error occurs."
            # }
            settings['Settings']['Force generic extractor'] = {
                "active option": 0,
                "command": "--force-generic-extractor",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Force extraction to use the generic extractor"
            }
            settings['Settings']['Use proxy'] = {
                "active option": 0,
                "command": "--proxy {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Use the specified HTTP/HTTPS/SOCKS proxy."
            }
            settings['Settings']['Socket timeout'] = {
                "active option": 0,
                "command": "--socket-timeout {}",
                "dependency": None,
                "options": [10, 60, 300],
                "state": False,
                "tooltip": "Time to wait before giving up, in seconds."
            }
            settings['Settings']['Source IP'] = {
                "active option": 0,
                "command": "--source-address {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Client-side IP address to bind to."
            }
            settings['Settings']['Force ipv4/6'] = {
                "active option": 0,
                "command": "--{}",
                "dependency": None,
                "options": ['force-ipv4', 'force-ipv6'],
                "state": False,
                "tooltip": "Make all connections via ipv4/6."
            }
            settings['Settings']['Geo bypass URL'] = {
                "active option": 0,
                "command": "--geo-verification-proxy {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Use this proxy to verify the IP address for some geo-restricted sites.\n"
                           "The default proxy specified by"
                           " --proxy (or none, if the options is not present)\nis used for the actual downloading."
            }
            settings['Settings']['Geo bypass country CODE'] = {
                "active option": 0,
                "command": "--geo-bypass-country {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Force bypass geographic restriction with explicitly provided\n"
                           "two-letter ISO 3166-2 country code (experimental)."
            }
            settings['Settings']['Playlist start'] = {
                "active option": 0,
                "command": "--playlist-start {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Playlist video to start at (default is 1)."
            }
            settings['Settings']['Playlist end'] = {
                "active option": 0,
                "command": "--playlist-end {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Playlist video to end at (default is last)."
            }
            settings['Settings']['Playlist items'] = {
                "active option": 0,
                "command": "--playlist-items {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Playlist video items to download.\n"
                           "Specify indices of the videos in the playlist "
                           "separated by commas like:\n\"1,2,5,8\" if you want to download videos "
                           "indexed 1, 2, 5, 8 in the playlist.\nYou can specify range:"
                           "\"1-3,7,10-13\"\nwill download the videos at index:\n1, 2, 3, 7, 10, 11, 12 and 13."
            }
            settings['Settings']['Match titles'] = {
                "active option": 0,
                "command": "--match-title {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Download only matching titles (regex or caseless sub-string)."
            }
            settings['Settings']['Reject titles'] = {
                "active option": 0,
                "command": "--reject-title {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Skip download for matching titles (regex or caseless sub-string)."
            }
            settings['Settings']['Max downloads'] = {
                "active option": 0,
                "command": "--max-downloads {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Abort after downloading a certain number of files."
            }
            settings['Settings']['Minimum size'] = {
                "active option": 0,
                "command": "--min-filesize {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Do not download any videos smaller than SIZE (e.g. 50k or 44.6m)."
            }
            settings['Settings']['Maximum size'] = {
                "active option": 0,
                "command": "--max-filesize {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Do not download any videos bigger than SIZE (e.g. 50k or 44.6m)."
            }
            settings['Settings']['No playlist'] = {
                "active option": 0,
                "command": "--no-playlist ",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Download only the video, if the URL refers to a video and a playlist."
            }
            settings['Settings']['Download speed limit'] = {
                "active option": 0,
                "command": "--limit-rate {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Maximum download rate in bytes per second (e.g. 50K or 4.2M)."
            }
            settings['Settings']['Retry rate'] = {
                "active option": 0,
                "command": "--retries {}",
                "dependency": None,
                "options": ['Implement later', 10, 15],
                "state": False,
                "tooltip": "Number of retries (default is 10), or \"infinite\"."
            }
            settings['Settings']['Download order'] = {
                "active option": 0,
                "command": "--playlist-{}",
                "dependency": None,
                "options": ['reverse', 'random'],
                "state": False,
                "tooltip": "Download playlist videos in reverse/random order."
            }
            settings['Settings']['Prefer native/ffmpeg'] = {
                "active option": 0,
                "command": "--hls-prefer-{}",
                "dependency": None,
                "options": ['ffmpeg', 'native'],
                "state": False,
                "tooltip": "Use the native HLS downloader instead of ffmpeg, or vice versa."
            }
            settings['Settings']['Don\'t overwrite files'] = {
                "active option": 0,
                "command": "--no-overwrites",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Do not overwrite files"
            }
            settings['Settings']['Don\'t continue files'] = {
                "active option": 0,
                "command": "--no-continue",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Do not resume partially downloaded files."
            }
            settings['Settings']['Don\'t use .part files'] = {
                "active option": 0,
                "command": "--no-part",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Do not use .part files - write directly into output file."
            }
            settings['Settings']['Verbose'] = {
                "active option": 0,
                "command": "--verbose",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Print various debugging information."
            }
            settings['Settings']['Custom user agent'] = {
                "active option": 0,
                "command": "--user-agent {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Specify a custom user agent."
            }
            settings['Settings']['Custom referer'] = {
                "active option": 0,
                "command": "--referer {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Specify a custom referer, use if the video access is restricted to one domain."
            }
            settings['Settings']['Min sleep interval'] = {
                "active option": 0,
                "command": "--sleep-interval {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Number of seconds to sleep before each download;\nwhen used "
                           "alone or a lower bound of a range for randomized sleep before each\n"
                           "download when used along with max sleep interval."
            }
            settings['Settings']['Max sleep interval'] = {
                "active option": 0,
                "command": "--max-sleep-interval {}",
                "dependency": "Min sleep interval",
                "options": [],
                "state": False,
                "tooltip": "Upper bound of a range for randomized sleep before each download\n"
                           "(maximum possible number of seconds to sleep).\n"
                           "Must only be used along with --min-sleep-interval."
            }
            settings['Settings']['Video format'] = {
                "active option": 0,
                "command": "--format {}",
                "dependency": None,
                "options": ["Implement later"],
                "state": False,
                "tooltip": "Video format code."
            }
            settings['Settings']['Write subtitle file'] = {
                "active option": 0,
                "command": "--write-sub",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Write subtitle file."
            }
            settings['Settings']['Recode video'] = {
                "active option": 0,
                "command": "--recode-video {}",
                "dependency": None,
                "options": ['mp4', 'flv', 'ogg', 'webm', 'mkv', 'avi'],
                "state": False,
                "tooltip": "Encode the video to another format if necessary.\n"
                           "Currently supported: mp4|flv|ogg|webm|mkv|avi."
            }
            settings['Settings']['No post overwrite'] = {
                "active option": 0,
                "command": "--no-post-overwrites",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Do not overwrite post-processed files;\n"
                           "the post-processed files are overwritten by default."
            }
            settings['Settings']['Embed subs'] = {
                "active option": 0,
                "command": "--embed-subs",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Embed subtitles in the video (only for mp4, webm and mkv videos)"
            }
            settings['Settings']['Add metadata'] = {
                "active option": 0,
                "command": "--add-metadata",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Write metadata to the video file."
            }
            settings['Settings']['Metadata from title'] = {
                "active option": 0,
                "command": "--metadata-from-title {}",
                "dependency": None,
                "options": [],
                "state": False,
                "tooltip": "Parse additional metadata like song title /"
                           "artist from the video title.\nThe format"
                           "syntax is the same as --output.\nRegular "
                           "expression with named capture groups may"
                           "also be used.\nThe parsed parameters replace "
                           "existing values.\n\n"
                           "Example:\n\"%(artist)s - %(title)s\" matches a"
                           "title like \"Coldplay - Paradise\".\nExample"
                           "(regex):\n\"(?P<artist>.+?) - (?P<title>.+)\""
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
        """ Checks the setttings for errors or missing data. """

        base_sections = ['Profiles', 'Favorites', 'Settings', 'Other stuff']
        # TODO: Check if fully abandonded list. Remove if so.
        base_settings = ['Convert to audio',
                         'Add thumbnail',
                         'Ignore errors',
                         'Download location',
                         'Strict file names',
                         'Keep archive']
        base_keys = ['command',
                     'dependency',
                     'options',
                     'state',
                     'tooltip']

        if not self.settings:
            raise SettingsError('Empty settings file!')

        missing_settings = {}
        self.need_parameters = []

        for section in base_sections:
            if section not in self.settings:
                missing_settings[section] = []

        for setting, option in self.settings['Settings'].items():
            # setting: The name of the setting, like "Ignore errors"
            # option: The dict which contains the base keys.
            # key (Define below): is a key in the base settings

            # print(setting)
            # print(option)
            for key in base_keys:
                # Check if all base keys are in the options.
                if key not in option.keys():
                    # Check if the current setting has already logged a missing key
                    # If it hasn't, create an entry in the missing_settings dict, as a list.
                    # If it's there, then add the key to the missing list.
                    if setting not in missing_settings.keys():
                        missing_settings[setting] = [key]
                    else:
                        missing_settings[setting].append(key)
                # Check if the current setting is missing options for the command, when needed.
                # Disable the setting by default. Possibly alert the user.
                elif key == 'command':
                    if '{}' in option[key]:
                        if not option['options']:
                            # print(f'{setting} currently lacks any valid options!')
                            if 'state' in option.keys() and setting != 'Download location':
                                self.settings['Settings'][setting]['state'] = False
                                # Add to a list over options to add setting to.
                                self.need_parameters.append(setting)

            #
            # if option not in self.settings['Settings']:
            #     missing_settings[option] = []
            # else:
            #     for key in base_keys:
            #         if key not in self.settings['Settings'][option]:
            #             if option not in missing_settings.keys():
            #                 missing_settings[option] = [key]
            #             else:
            #                 missing_settings[option].append(key)

        if missing_settings:
            raise SettingsError('\n'.join(['Settings file is corrupt/missing:',
                                           '-' * 20,
                                           *[f'{key}:\n - {", ".join(value)}' if value
                                             else f"{key}" for key, value in missing_settings.items()],
                                           '-' * 20]))

        if not self.settings['Settings']['Download location']['options']:
            # Checks for a download setting, set the current path to that.
            self.settings['Settings']['Download location']['options'] = [self.workDir + '/DL/%(title)s.%(ext)s']

        try:
            # Checks if the active option is valid, if not reset to the first item.
            for setting in self.settings['Settings'].keys():
                if self.settings['Settings'][setting]['options'] is not None:
                    # Check if active option is a valid number.
                    if not (0 <= self.settings['Settings'][setting]['active option'] < len(
                            self.settings['Settings'][setting]['options'])):
                        self.settings['Settings'][setting]['active option'] = 0
        # Catch if the setting is missing for needed options.
        except KeyError as error:
            raise SettingsError(f'{setting} is missing a needed option {error}.')
        # Catches mutiple type errors.
        except TypeError as error:
            raise SettingsError(f'An unexpected type was encountered for setting:\n - {setting}\n -- {error}')

        self.write_setting(self.settings)

    def update_setting(self, diction: dict, section: str, key: str, value):
        diction[section][key] = value
        self.write_setting(diction)

    def update_parameters(self, diction, setting, state):
        diction['Settings'][setting]['state'] = state
        self.write_setting(diction)

    def update_options(self, diction, setting, index):
        if setting in diction['Settings'].keys():
            diction['Settings'][setting]['active option'] = index
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
            if item.data(0, 32) in self.need_parameters:
                result = self.alert_message('Warning!', 'This parameter needs an option!', 'There are no options!\n'
                                                                                           'Would you make one?', True)
                if result == QMessageBox.Yes:
                    item.treeWidget().blockSignals(True)

                    title = self.design_option_dialog(item.text(0), item.toolTip(0))
                    if title:
                        ParameterTree.make_option(title, item, True, 1, None, None, 0)

                        self.need_parameters.remove(item.data(0, 32))
                        self.update_setting(self.settings['Settings'], item.data(0, 32), 'options', [title])

                    else:
                        item.setCheckState(0, Qt.Unchecked)

                    item.treeWidget().blockSignals(False)

                else:
                    item.treeWidget().blockSignals(True)
                    item.setCheckState(0, Qt.Unchecked)
                    item.treeWidget().blockSignals(False)
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
                item.setData(0, 0, 'Custom command double click to change')
                item.setCheckState(0, Qt.Unchecked)
            elif item.data(0, 0) in ('custom', 'Custom'):
                item.setCheckState(0, Qt.Unchecked)
            self.settings['Other stuff']['custom']['command'] = item.data(0, 0)
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

    def dir_info(self):

        file_dir = os.path.dirname(os.path.abspath(__file__))

        debug = [color_text('\nYoutube-dl.exe path:'), self.youtube_dl_path,
                 color_text('Filedir:'), file_dir,
                 color_text('Workdir:'), self.workDir,
                 color_text('Youtube-dl working directory:'), self.program_workdir,
                 color_text('\nIcon paths:'),
                 self.checked_icon, self.unchecked_icon, self.alert_icon,
                 self.window_icon]

        for i in debug:
            self.tab1.textbrowser.append(str(i))

        self.tab1.textbrowser.append(color_text('\nChecking if icons are in place:', 'darkorange', 'bold'))

        for i in self.icon_list:
            if i is not None:
                try:
                    if os.path.isfile(str(i)):
                        self.tab1.textbrowser.append(''.join(['Found:', os.path.split(i)[1]]))
                    else:
                        self.tab1.textbrowser.append(''.join(['Missing in:', i]))
                except IndexError:
                    if os.path.isfile(str(i)):
                        self.tab1.textbrowser.append(''.join(['Found: ', i]))
                    else:
                        self.tab1.textbrowser.append(''.join(['Missing in:', i]))

        self.main_tab.setCurrentIndex(0)

    def get_program_working_directory(self):
        try:
            work_dir = sys._MEIPASS
        except AttributeError:
            work_dir = os.path.abspath('.')

        return work_dir

    def update_youtube_dl(self):
        self.tab1.textbrowser.clear()
        self.main_tab.setCurrentIndex(0)
        download_item = Download(self.program_workdir, self.youtube_dl_path, ['-U', '--encoding', 'utf-8'], self)
        download_item.readyReadStandardOutput.connect(lambda: self.read_stdoutput(download_item))
        download_item.stateChanged.connect(self.program_state_changed)

        self.tab1.start_btn.setDisabled(True)
        self.queue.append(download_item)
        self.queue_handler()

    def queue_handler(self, process_finished=False):
        if not self.RUNNING or process_finished:
            if self.queue:
                download = self.queue.popleft()
                self.tab1.queue_label.setText(f'Items in queue: {len(self.queue):5}')
                self.active_download = download
                download.start_dl()

                self.set_running(True)
            else:
                self.set_running(False)
                self.tab1.textbrowser.append('\nDone\n')
                self.tab1.textbrowser.append(f'Error count: '
                                             f'{self.Errors if self.Errors ==0 else color_text(str(self.Errors),"darkorange","bold")}.')
                self.Errors = 0
        self.tab1.queue_label.setText(f'Items in queue: {len(self.queue):3}')

    def set_running(self, running=False):
        self.RUNNING = running
        self.tab1.stop_btn.setEnabled(self.RUNNING)
        # When something is downloading add program wide changes here.

    # When the current download is started/stopped then this runs.
    def program_state_changed(self, new_state):
        if new_state == QProcess.NotRunning:
            self.active_download.disconnect()
            self.queue_handler(process_finished=True)
        elif new_state == QProcess.Running:
            self.tab1.textbrowser.append(color_text('Starting...\n', 'lawngreen', 'normal', sections=(0, 8)))

        return

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
            self.alert_message('Error!', 'Could not find file!', '')
            # Check if the checkbox is toggled, and disables the line edit if it is.
            #  Also disables start button if lineEdit is empty and checkbox is not checked

    def queue_dl(self):
        if not self.RUNNING:
            self.tab1.textbrowser.clear()

        command = []

        if self.tab1.checkbox.isChecked():
            if self.tab4_txt_lineedit.text() == '':
                self.alert_message('Error!', 'No textfile selected!', '')
                self.tab1.textbrowser.append('No textfile selected...\n\nNo download queued!')
                return

            txt = self.settings['Other stuff']['multidl_txt']
            command += ['-a', f'{txt}']
        else:
            txt = self.tab1.lineedit.text()
            command.append(f'{txt}')

        # for i in range(len(command)):
        #    command[i] = command[i].format(txt=txt)'
        file_name_format = '%(title)s.%(ext)s'

        for parameter, options in self.settings['Settings'].items():
            if parameter == 'Download location':
                if options['state']:
                    add = format_in_list(options['command'],
                                         options['options'][options['active option']] + file_name_format)
                    command += add
                else:
                    command += ['-o', self.local_dl_path + file_name_format]

            elif parameter == 'Keep archive':
                if options['state']:
                    add = format_in_list(options['command'],
                                         os.path.join(self.workDir, options['options'][options['active option']]))
                    command += add
            else:
                if options['state']:
                    add = format_in_list(options['command'],
                                         options['options'][
                                             options['active option']] if options['options'] is not None
                                                                          or options['options'] else '')
                    command += add

        if self.settings['Other stuff']['custom']['state']:
            if self.settings['Other stuff']['custom']['command'] not in (
                    'Custom command double click to change', 'Custom'):
                command += self.settings['Other stuff']['custom']['command'].split()

        # Sets encoding to utf-8, allowing better character support in output stream.
        command += ['--encoding', 'utf-8']

        if self.ffmpeg_path is not None:
            command += ['--ffmpeg-location', self.ffmpeg_path]

        download_item = Download(self.program_workdir, self.youtube_dl_path, command, self)
        download_item.readyReadStandardOutput.connect(lambda: self.read_stdoutput(download_item))
        download_item.stateChanged.connect(self.program_state_changed)

        self.tab1.start_btn.setDisabled(True)
        self.queue.append(download_item)
        self.queue_handler()

    def stop_download(self):
        if len(self.queue):
            result = self.alert_message('Stop all?', 'Stop all pending downloads too?', '', True, True)
            if result == QMessageBox.Yes:
                for i in self.queue:
                    i.disconnect()
                    del i
                self.queue.clear()
                self.active_download.kill()
                self.tab1.textbrowser.append('Cancelling all downloads...')
            elif result == QMessageBox.No:
                self.active_download.kill()
                self.tab1.textbrowser.append('Cancelling download...')
            elif result == QMessageBox.Cancel:
                return
        else:
            if self.active_download is not None:
                self.active_download.kill()
            else:
                self.alert_message('Alert', 'stop was called withou without and active process!', '')

    def cmdoutput(self, info):
        if info.startswith('ERROR'):
            self.Errors += 1
            info = info.replace('ERROR', '<span style=\"color: darkorange; font-weight: bold;\">ERROR</span>')
        info = re.sub(r'\s+$', '', info, 0, re.M)
        info = re.sub(' +', ' ', info)
        regexp = re.compile('|'.join(map(re.escape, self.substrs)))

        return regexp.sub(lambda match: self.replace_dict[match.group(0)], info)

    # appends youtube-dl output to tab1.textbrowser.
    def read_stdoutput(self, download_item: Download):
        data = download_item.readAllStandardOutput().data()
        text = data.decode('utf-8', 'replace').strip()
        text = self.cmdoutput(text)
        # print(text)

        scrollbar = self.tab1.textbrowser.verticalScrollBar()
        place = scrollbar.sliderPosition()

        if place == scrollbar.maximum():
            keep_position = False
        else:
            keep_position = True

        # get the last line of QTextEdit
        self.tab1.textbrowser.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)
        self.tab1.textbrowser.moveCursor(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
        self.tab1.textbrowser.moveCursor(QTextCursor.End, QTextCursor.KeepAnchor)
        last_line = self.tab1.textbrowser.textCursor().selectedText()

        # Check if a percentage has already been placed.
        if "%" in last_line and 'ETA' in last_line:
            self.tab1.textbrowser.textCursor().removeSelectedText()
            self.tab1.textbrowser.textCursor().deletePreviousChar()
            # Last line of text
            self.tab1.textbrowser.append(color_text(text.split("[download]")[-1][1:],
                                                    color='lawngreen',
                                                    weight='bold',
                                                    sections=(0, 5)))
            if '100%' in text:
                self.tab1.textbrowser.append('')

        else:
            if "%" in text and 'ETA' in text:
                # Last line of text
                self.tab1.textbrowser.append(color_text(text.split("[download]")[-1][1:],
                                                        color='lawngreen',
                                                        weight='bold',
                                                        sections=(0, 5)))
            elif '[download]' in text:
                self.tab1.textbrowser.append(''.join([text.replace('[download] ', ''), '\n']))
            else:
                self.tab1.textbrowser.append(''.join([text, '\n']))

        # Prevents some leftover highlighted text on errors and such.
        self.tab1.textbrowser.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)

        # Ensures slider position is kept when not at bottom, and stays at bottom with new text where there.
        if keep_position:
            scrollbar.setSliderPosition(place)
        else:
            scrollbar.setSliderPosition(scrollbar.maximum())

    # Startup function, sets the startbutton to disabled, if lineEdit is empty,
    # And disables the lineEdit if the textbox is checked.
    # Stop button is set to disabled, since no process is running.
    def allow_start(self):
        self.tab1.stop_btn.setDisabled(not self.RUNNING)
        self.tab1.lineedit.setDisabled(self.tab1.checkbox.isChecked())
        self.tab1.start_btn.setDisabled(self.tab1.lineedit.text() == '')

    def load_text_from_file(self):
        if self.tab3_textedit.toPlainText() or (not self.tab3_saveButton.isEnabled()) or self.SAVED:
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
        # TODO: Do proper path check before trying to open file handler.
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
        if self.RUNNING or len(self.queue):
            result = self.alert_message('Want to quit?',
                                        'Still downloading!',
                                        'Do you want to close without letting youtube-dl finish? '
                                        'Will likely leave unwanted/incomplete files in the download folder.',
                                        question=True)
            if result != QMessageBox.Yes:
                return None

        if ((self.tab3_textedit.toPlainText() == '') or (not self.tab3_saveButton.isEnabled())) or self.SAVED:
            self.sendClose.emit()
        else:
            result = self.alert_message('Unsaved changes in list!',
                                        'Save?',
                                        'Do you want to save before exiting?',
                                        question=True,
                                        allow_cancel=True)
            if result == QMessageBox.Yes:
                self.save_text_to_file()
                self.sendClose.emit()
            elif result == QMessageBox.Cancel:
                pass
            else:
                self.sendClose.emit()

    def read_license(self):
        if not self.license_shown:
            self.tab4_abouttext_textedit.clear()
            with open(self.license_path, 'r') as f:
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
        self.tab1.lineedit.selectAll()


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMessageBox

    while True:
        try:
            app = QApplication(sys.argv)
            qProcess = GUI()

            EXIT_CODE = app.exec()
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
