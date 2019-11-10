import json
import os
import sys

from PyQt5.QtCore import QProcess, pyqtSignal, Qt, QMimeData
from PyQt5.QtGui import QKeySequence, QIcon, QClipboard, QGuiApplication
from PyQt5.QtWidgets import QShortcut, QFileDialog, QTreeWidgetItem, qApp, QDialog, QApplication, QMessageBox, \
    QTabWidget, QListWidgetItem

from Modules import Dialog, Download, MainTab, ParameterTree, MainWindow, AboutTab, Downloader, ParameterTab, TextTab
from Modules.download_element import ProcessListItem, MockDownload
from utils.filehandler import FileHandler
from utils.utilities import path_shortener, color_text, format_in_list, SettingsError, get_stylesheet, \
    get_win_accent_color, ProfileLoadError, LessNiceDict


class GUI(MainWindow):
    """
    Runnable class that makes a wrapper for youtube-dl.
    """
    sendClose = pyqtSignal()
    EXIT_CODE_REBOOT = -123456789

    def __init__(self):
        """
        GUI that wraps a youtube-dl.exe to download videos and more.
        """
        super().__init__()

        # starts checks
        self.initial_checks()

        # Holds temp passwords
        self._temp = LessNiceDict()

        # Builds GUI and everything related to that.
        self.build_gui()

    def initial_checks(self):
        """Loads settings and finds necessary files. Checks the setting file for errors."""
        QApplication.setEffectEnabled(Qt.UI_AnimateCombo, False)

        self._debug = None
        self.file_handler = FileHandler()
        self.settings = self.file_handler.load_settings()
        self.downloader = Downloader(self.file_handler)
        # Find resources.
        # Find youtube-dl

        self.youtube_dl_path = self.file_handler.find_exe('youtube-dl.exe')
        self.ffmpeg_path = self.file_handler.find_exe('ffmpeg.exe')
        self.program_workdir = self.file_handler.work_dir
        self.license_path = self.file_handler.find_file('LICENSE')

        self.local_dl_path = self.file_handler.work_dir + '/DL/'

        # NB! For stylesheet stuff, the slashes '\' in the path, must be replaced with '/'.
        # Using replace('\\', '/') on path. Done by file handler!
        self.icon_list = []

        # TODO: Turn into dict comprehension??
        # Find icon paths
        self.unchecked_icon = self.file_handler.find_file('GUI\\Icon_unchecked.ico')
        self.checked_icon = self.file_handler.find_file('GUI\\Icon_checked.ico')
        self.alert_icon = self.file_handler.find_file('GUI\\Alert.ico')
        self.window_icon = self.file_handler.find_file('GUI\\YTDLGUI.ico')
        self.down_arrow_icon = self.file_handler.find_file('GUI\\down-arrow2.ico')
        self.down_arrow_icon_clicked = self.file_handler.find_file('GUI\\down-arrow2-clicked.ico')

        # Adding icons to list. For debug purposes.
        self.icon_list.append(self.unchecked_icon)
        self.icon_list.append(self.checked_icon)
        self.icon_list.append(self.alert_icon)
        self.icon_list.append(self.window_icon)
        self.icon_list.append(self.down_arrow_icon)
        self.icon_list.append(self.down_arrow_icon_clicked)

        # Creating icon objects for use in message windows.
        self.alertIcon = QIcon()
        self.windowIcon = QIcon()

        # Setting the icons image, using found paths.
        self.alertIcon.addFile(self.alert_icon)
        self.windowIcon.addFile(self.window_icon)

    def build_gui(self):
        """Generates the GUI elements, and hooks everything up."""

        # Indicates if license is shown. (For license tab)
        # TODO: Move to license tab?
        self.license_shown = False

        # Sorts the parameters, so that favorite ones are added to the favorite widget.
        favorites = {i: self.settings[i] for i in self.settings.get_favorites()}
        options = {k: v for k, v in self.settings.parameters.items() if k not in favorites}

        # Main widget. This will be the ones that holds everything.
        # Create top level tab widget system for the UI.
        self.tab_widget = QTabWidget(self)

        self.onclose.connect(self.confirm)
        self.sendClose.connect(self.closeE)

        # Connecting stuff for tab 1.
        # Start buttons starts download

        self.tab1 = MainTab(self.settings, self)

        self.tab1.start_btn.clicked.connect(self.queue_dl)
        # Stop button kills the process, aka youtube-dl.
        self.tab1.stop_btn.clicked.connect(self.stop_download)
        # Close button closes the window/process.
        self.tab1.close_btn.clicked.connect(self.close)
        # Clears finished items in the download list

        # When the check button is checked or unchecked, calls function checked.
        self.tab1.checkbox.stateChanged.connect(self.allow_start)
        # Connects actions to text changes and adds action to when you press Enter.
        self.tab1.url_input.textChanged.connect(self.allow_start)

        # Queue downloading
        self.tab1.url_input.returnPressed.connect(self.tab1.start_btn.click)

        # Change profile
        self.tab1.profile_dropdown.currentTextChanged.connect(self.load_profile)
        # Delete profile
        self.tab1.profile_dropdown.deleteItem.connect(self.delete_profile)

        # Tab 2
        self.tab2 = ParameterTab(options, favorites, self.settings, self)
        # Adds the tab2 layout to the widget.

        # Connection stuff tab 2.
        self.tab2.open_folder_action.triggered.connect(self.open_folder)
        self.tab2.copy_action.triggered.connect(self.copy_to_cliboard)

        self.tab2.options.itemChanged.connect(self.parameter_updater)
        self.tab2.options.move_request.connect(self.move_item)
        self.tab2.options.itemRemoved.connect(self.item_removed)
        self.tab2.options.addOption.connect(self.add_option)

        self.tab2.favorites.itemChanged.connect(self.parameter_updater)
        self.tab2.favorites.move_request.connect(self.move_item)
        self.tab2.favorites.itemRemoved.connect(self.item_removed)
        self.tab2.favorites.addOption.connect(self.add_option)

        self.tab2.browse_btn.clicked.connect(self.savefile_dialog)
        self.tab2.save_profile_btn.clicked.connect(self.save_profile)

        # Tab 3.
        # Tab creation.
        self.tab3 = TextTab(parent=self)

        # Connecting stuff tab 3.

        # When loadbutton is clicked, launch load textfile.
        self.tab3.loadButton.clicked.connect(self.load_text_from_file)
        # When savebutton clicked, save text to document.
        self.tab3.saveButton.clicked.connect(self.save_text_to_file)

        # Tab 4
        # Button to browse for .txt file to download files.
        self.tab4 = AboutTab(self.settings, parent=self)

        ## Connecting stuff tab 4.

        # Starts self.update_youtube_dl, locate_program_path checks for updates.
        self.tab4.update_btn.clicked.connect(self.update_youtube_dl)
        self.tab4.dirinfo_btn.clicked.connect(self.dir_info)
        self.tab4.reset_btn.clicked.connect(self.reset_settings)
        self.tab4.license_btn.clicked.connect(self.read_license)
        self.tab4.location_btn.clicked.connect(self.textfile_dialog)
        self.tab4.debug_info.clicked.connect(self.toggle_debug)
        self.tab4.dl_mode_btn.clicked.connect(self.toggle_modes)

        # Future tab creation here! Currently 4 tabs
        # TODO: Move stylesheet applying to method, make color picking dialog to customize in realtime
        if self.settings.user_options['use_win_accent']:
            try:
                color = get_win_accent_color()
                bg_color = f"""
                QMainWindow {{
                    background-color: {color};
                }}
                QTabBar {{
                    background-color: {color};
                }}"""
            except (OSError, PermissionError):
                bg_color = ''
        else:
            bg_color = ''

        self.style_with_options = bg_color + f"""
                                QCheckBox::indicator:unchecked {{
                                    image: url({self.unchecked_icon});
                                }}

                                QCheckBox::indicator:checked {{
                                    image: url({self.checked_icon});
                                }}
                                QComboBox::down-arrow {{
                                    border-image: url({self.down_arrow_icon});
                                    height: {self.tab1.profile_dropdown.iconSize().height()}px;
                                    width: {self.tab1.profile_dropdown.iconSize().width()}px;
                                }}

                                QComboBox::down-arrow::on {{
                                    image: url({self.down_arrow_icon_clicked});
                                    height: {self.tab1.profile_dropdown.iconSize().height()}px;
                                    width: {self.tab1.profile_dropdown.iconSize().width()}px;
                                    
                                }}
                                
                                QTreeWidget::indicator:checked {{
                                    image: url({self.checked_icon});
                                }}
                                
                                QTreeWidget::indicator:unchecked {{
                                    image: url({self.unchecked_icon});
                                }}
                                
                                QTreeWidget::branch {{
                                    image: none;
                                    border-image: none;    
                                }}
                                
                                QTreeWidget::branch:has-siblings:!adjoins-item {{
                                    image: none;
                                    border-image: none;
                                }}
                                
                                QTreeWidget::branch:has-siblings:adjoins-item {{
                                    border-image: none;
                                    image: none;
                                }}
                                
                                QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {{
                                    border-image: none;
                                    image: none;
                                }}
                                
                                """

        # Configuration main widget.
        # Adds tabs to the tab widget, and names the tabs.
        self.tab_widget.addTab(self.tab1, 'Main')
        self.tab_widget.addTab(self.tab2, 'Param')
        self.tab_widget.addTab(self.tab3, 'List')
        self.tab_widget.addTab(self.tab4, 'About')
        # Sets the styling for the GUI, everything from buttons to anything. ##
        self.setStyleSheet(get_stylesheet() + self.style_with_options)

        # Set window title.
        self.setWindowTitle('Grabber')
        self.setWindowIcon(self.windowIcon)
        # Set base size.
        self.setMinimumWidth(340)
        self.setMinimumHeight(400)

        if self.settings.user_options['select_on_focus']:
            self.gotfocus.connect(self.window_focus_event)
        else:
            self.tab1.url_input.setFocus()

        # Other functionality.
        self.shortcut = QShortcut(QKeySequence("Ctrl+S"), self.tab3.textedit)
        self.shortcut.activated.connect(self.tab3.saveButton.click)

        # Check for youtube
        if self.youtube_dl_path is None:
            self.tab4.update_btn.setDisabled(True)
            self.alert_message('Warning!', '\nNo youtube-dl.exe found! Add to path, '
                                           'or make sure it\'s in the same folder as this program. '
                                           'Then close and reopen this program.', '')
        # Sets the download items tooltips to the full file path.
        self.download_name_handler()

        # Ensures widets are in correct state at startup and when tab1.lineedit is changed.
        self.allow_start()
        # Shows the main window.
        self.setCentralWidget(self.tab_widget)

        self.show()

        # Connect after show!!
        self.resizedByUser.connect(self.resize_contents)
        # To make sure the window is updated on first enter
        # if resized before tab2 is shown, i'll be blank.

        self.downloader.stateChanged.connect(self.allow_start)
        self.tab_widget.currentChanged.connect(self.resize_contents)

        # Sets the lineEdit for youtube links and paramters as focus. For easier writing.

    def toggle_debug(self):
        self._debug = not self._debug

        self.tab4.debug_info.setText(f'Debug:\n{self._debug}')
        for i in self.tab1.process_list.iter_items():
            i.toggle_debug(self._debug)

    def toggle_modes(self):
        if self.downloader.RUNNING or self.downloader.has_pending():
            self.alert_message('Action failed',
                               'Mode was not changed',
                               "Unable to toggle between download mode with active downloads!")
            return

        else:
            parallel = not self.settings.user_options['parallel']
            self.settings.user_options['parallel'] = parallel
            self.tab4.dl_mode_btn.setText("Singular" if not parallel else "Parallel")
            self.downloader.set_mode(parallel=parallel)

    def save_profile(self):
        dialog = Dialog(self.tab_widget, 'Name profile', 'Give a name to the profile!')
        if dialog.exec() != QDialog.Accepted:
            return
        elif dialog.option.text() in ('Custom', 'None'):
            self.alert_message('Error', 'This profile name is not allowed!', '')

        profile_name = dialog.option.text()

        if profile_name in self.settings.profiles:
            result = self.alert_message('Overwrite profile?',
                                        f'Do you want to overwrite profile:',
                                        f'{profile_name}'.center(45),
                                        True)
            if result != QMessageBox.Yes:
                return

        self.tab1.profile_dropdown.blockSignals(True)
        self.tab1.profile_dropdown.setDisabled(False)

        if self.tab1.profile_dropdown.findText(profile_name) == -1:
            self.tab1.profile_dropdown.addItem(profile_name)
        self.tab1.profile_dropdown.setCurrentText(profile_name)
        self.tab1.profile_dropdown.removeItem(self.tab1.profile_dropdown.findText('None'))
        self.tab1.profile_dropdown.removeItem(self.tab1.profile_dropdown.findText('Custom'))
        self.tab1.profile_dropdown.blockSignals(False)

        self.settings.create_profile(profile_name)

        self.file_handler.save_settings(self.settings.get_settings_data)
        self.file_handler.save_profiles(self.settings.get_profiles_data)

    def load_profile(self):
        try:
            profile_name = self.tab1.profile_dropdown.currentText()

            if profile_name in ('None', 'Custom'):
                return

            success = self.settings.change_profile(profile_name)

            if not success:
                self.alert_message('Error',
                                   'Failed to find profile',
                                   f'The profile "{profile_name}" was not found!')
                return

            favorites = {i: self.settings[i] for i in self.settings.get_favorites()}
            options = {k: v for k, v in self.settings.parameters.items() if k not in favorites}

            self.tab2.options.load_profile(options)
            self.tab2.favorites.load_profile(favorites)
            self.tab2.find_download_widget()
            self.download_name_handler()

            self.tab1.profile_dropdown.blockSignals(True)
            self.tab1.profile_dropdown.removeItem(self.tab1.profile_dropdown.findText('None'))
            self.tab1.profile_dropdown.removeItem(self.tab1.profile_dropdown.findText('Custom'))
            self.tab1.profile_dropdown.blockSignals(False)

            self.file_handler.save_settings(self.settings.get_settings_data)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def delete_profile(self):
        index = self.tab1.profile_dropdown.currentIndex()
        text = self.tab1.profile_dropdown.currentText()
        if text in ('Custom', 'None'):
            return

        self.settings.delete_profile(text)

        self.tab1.profile_dropdown.blockSignals(True)
        self.tab1.profile_dropdown.removeItem(index)
        self.tab1.profile_dropdown.addItem('Custom')
        self.tab1.profile_dropdown.setCurrentText('Custom')
        self.tab1.profile_dropdown.blockSignals(False)

        self.file_handler.save_settings(self.settings.get_settings_data)

    def item_removed(self, item: QTreeWidgetItem, index):
        """Parent who had child removed. Updates settings and numbering of get_settings_data 35"""
        self.settings.remove_parameter_option(item.data(0, 0), index)
        if not item.childCount():
            item.setCheckState(0, Qt.Unchecked)

        self.file_handler.save_settings(self.settings.get_settings_data)

    def design_option_dialog(self, name, description):
        """
        Creates dialog for user input
        # TODO: Use this method where possible
        """
        dialog = Dialog(self.tab_widget, name, description)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.option.text()
        return None

    def add_option(self, item: QTreeWidgetItem):
        """
        Check if parameter has a possible option parameter, and lets the user add on if one exist.
        """
        if item.data(0, 32) == 'Download location':
            self.alert_message('Error!', 'Please use the browse button\nto select download location!', None)

        if item.data(0, 33) == 2:
            self.alert_message('Error!', 'Custom option does not take a command!', None)

        # TODO: Standardise setting an parameter to checked, and updating to expanded state.
        elif '{}' in self.settings[item.data(0, 32)]['command']:

            item.treeWidget().blockSignals(True)
            option = self.design_option_dialog(item.text(0), item.toolTip(0))

            if option:
                if option in self.settings[item.data(0, 32)]['options']:
                    self.alert_message('Error', 'That option already exsists!', '')
                    item.treeWidget().blockSignals(False)
                    return

                new_option = ParameterTree.make_option(option.strip(),
                                                       item,
                                                       True,
                                                       1,
                                                       None,
                                                       None,
                                                       0)

                move = item.takeChild(item.indexOfChild(new_option))
                item.insertChild(0, move)

                self.settings.add_parameter_option(item.data(0, 32), option)

                for i in range(len(self.settings[item.data(0, 32)]['options'])):
                    child = item.child(i)
                    child.setData(0, 35, i)
                    if i == 0:
                        child.setCheckState(0, Qt.Checked)
                        child.setFlags(child.flags() ^ Qt.ItemIsUserCheckable)
                    else:
                        child.setCheckState(0, Qt.Unchecked)
                        child.setFlags(child.flags() | Qt.ItemIsUserCheckable)

                item.setCheckState(0, Qt.Checked)
                item.setExpanded(True)
                item.treeWidget().update_size()
                try:
                    self.settings.need_parameters.remove(item.data(0, 32))
                except ValueError:
                    pass

                self.file_handler.save_settings(self.settings.get_settings_data)

            item.treeWidget().blockSignals(False)

        else:
            self.alert_message('Error!', 'The specified option does not take arguments!', None)
            # print('Doesn\'t have an option')

    def move_item(self, item: QTreeWidgetItem, favorite: bool):
        """ Move an time to or from the favorites tree. """

        if favorite:
            tree = self.tab2.options
            self.settings.user_options['favorites'].remove(item.data(0, 0))
        else:
            tree = self.tab2.favorites
            self.settings.user_options['favorites'].append(item.data(0, 0))

        tree.blockSignals(True)
        tree.addTopLevelItem(item)

        self.tab2.options.update_size()
        self.tab2.favorites.update_size()

        self.file_handler.save_settings(self.settings.get_settings_data)

        if item.checkState(0) == Qt.Checked:
            item.setExpanded(True)
        else:
            item.setExpanded(False)

        tree.blockSignals(False)

    def resize_contents(self):
        """ Resized parameterTree widgets in tab2 to the window."""
        if self.tab_widget.currentIndex() == 0:
            self.tab1.process_list.setMinimumWidth(self.window().width() - 18)
        elif self.tab_widget.currentIndex() == 1:
            size = self.height() - (self.tab2.frame.height() + self.tab2.download_lineedit.height()
                                    + self.tab2.favlabel.height() + self.tab_widget.tabBar().height() + 40)
            ParameterTree.max_size = size
            self.tab2.options.setFixedHeight(size)
            self.tab2.favorites.setFixedHeight(size)

    def window_focus_event(self):
        """ Selects text in tab1 line edit on window focus. """
        # self.tab2.options.max_size =
        if self.tab1.url_input.isEnabled():
            self.tab1.url_input.setFocus()
            self.tab1.url_input.selectAll()

    def copy_to_cliboard(self):
        """ Adds text to clipboard. """
        mime = QMimeData()
        mime.setText(self.tab2.download_lineedit.text())
        board = QGuiApplication.clipboard()
        board.setMimeData(mime, mode=QClipboard.Clipboard)

    def open_folder(self):
        """ Opens a folder at specified location. """
        # noinspection PyCallByClass
        QProcess.startDetached('explorer {}'.format(self.tab2.download_lineedit.toolTip().replace("/", "\\")))

    def download_name_handler(self):
        """ Formats download names and removes the naming string for ytdl. """
        item = self.tab2.download_option

        item.treeWidget().blockSignals(True)
        for number in range(item.childCount()):
            path = self.settings['Download location']['options'][number]
            item.child(number).setToolTip(0, path)
            item.child(number).setText(0, path_shortener(path))

        if item.checkState(0) == Qt.Checked:
            for number in range(item.childCount()):
                if item.child(number).checkState(0) == Qt.Checked:
                    self.tab2.download_lineedit.setText(item.child(number).data(0, 0))
                    self.tab2.download_lineedit.setToolTip(item.child(number).data(0, 32))
                    break
            else:
                # TODO: Add error handling here
                print('WARNING! No selected download item, this should not happen.... ')
                print('You messed with the settings... didn\'t you?!')
                # raise SettingsError('Error, no active option!')
        else:
            self.tab2.download_lineedit.setText(path_shortener(self.local_dl_path))
            self.tab2.download_lineedit.setToolTip(self.local_dl_path)
        item.treeWidget().blockSignals(False)

    def download_option_handler(self, full_path: str):
        """ Handles the download options. """
        # Adds new dl location to the tree and settings. Removes oldest one, if there is more than 3.
        # Remove try/except later.

        item = self.tab2.download_option

        if not full_path.endswith('/'):
            full_path += '/'
        short_path = path_shortener(full_path)
        names = [item.child(i).data(0, 0) for i in range(item.childCount())]

        if short_path in names and full_path in self.settings['Download location']['options']:
            self.alert_message('Warning', 'Option already exists!', '', question=False)
            return

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

        # Take item from one tree and insert in another.
        moving_sub = item.takeChild(item.indexOfChild(sub))
        item.insertChild(0, moving_sub)

        # Renumber the items, to give then the right index.
        for number in range(item.childCount()):
            item.child(number).setData(0, 35, number)

        if self.settings['Download location']['options'] is None:
            self.settings['Download location']['options'] = [full_path]
        else:
            self.settings.add_parameter_option('Download location', full_path)

        item.treeWidget().update_size()

        item.treeWidget().setSortingEnabled(True)
        item.treeWidget().blockSignals(False)

        # self.tab2.download_lineedit.setText(location)
        # self.tab2.download_lineedit.setToolTip(tooltip)
        try:
            self.settings.need_parameters.remove(item.data(0, 32))
        except ValueError:
            pass

        item.setCheckState(0, Qt.Checked)
        sub.setCheckState(0, Qt.Checked)

        self.file_handler.save_settings(self.settings.get_settings_data)

    # TODO: Show queue option

    def reset_settings(self):
        result = self.alert_message('Warning!',
                                    'Restart required!',
                                    'To reset the settings, '
                                    'the program has to be restarted. '
                                    'Do you want to reset and restart?',
                                    question=True)

        if result == QMessageBox.Yes:
            self.settings = self.file_handler.load_settings(reset=True)
            qApp.exit(GUI.EXIT_CODE_REBOOT)

    def parameter_updater(self, item: QTreeWidgetItem, col=None, save=True):
        """Handles updating the options for a parameter."""
        if 'Custom' != self.tab1.profile_dropdown.currentText():
            self.tab1.profile_dropdown.addItem('Custom')
            self.tab1.profile_dropdown.setCurrentText('Custom')
            self.settings.user_options['current_profile'] = ''

        if item.data(0, 33) == 0:
            if item.data(0, 32) in self.settings.need_parameters:
                result = self.alert_message('Warning!', 'This parameter needs an option!', 'There are no options!\n'
                                                                                           'Would you make one?', True)
                if result == QMessageBox.Yes:
                    self.add_option(item)
                else:
                    item.treeWidget().blockSignals(True)
                    item.setCheckState(0, Qt.Unchecked)
                    item.treeWidget().blockSignals(False)
                    item.treeWidget().check_dependency(item)

            if item.checkState(0) == Qt.Checked:
                self.settings[item.data(0, 32)]['state'] = True
                if item.data(0, 32) == 'Download location':
                    for i in range(item.childCount()):
                        self.parameter_updater(item.child(i), save=False)

            else:
                self.settings[item.data(0, 32)]['state'] = False
                if item.data(0, 32) == 'Download location':
                    self.tab2.download_lineedit.setText(path_shortener(self.local_dl_path))
                    self.tab2.download_lineedit.setToolTip(self.local_dl_path)

        elif item.data(0, 33) == 1:
            # Settings['Settings'][Name of setting]['active option']] = index of child
            self.settings[item.parent().data(0, 32)]['active option'] = item.data(0, 35)
            if item.parent().data(0, 32) == 'Download location':
                if item.checkState(0) == Qt.Checked:
                    self.tab2.download_lineedit.setText(item.data(0, 0))
                    self.tab2.download_lineedit.setToolTip(item.data(0, 32))

        if save:
            self.file_handler.save_settings(self.settings.get_settings_data)

    def dir_info(self):
        # TODO: Print this info to GUI.
        file_dir = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
        debug = [color_text('Youtube-dl.exe path: ') + self.youtube_dl_path,
                 color_text('ffmpeg.exe path: ') + self.ffmpeg_path,
                 color_text('Filedir: ') + file_dir,
                 color_text('Workdir: ') + self.file_handler.work_dir,
                 color_text('Youtube-dl working directory: ') + self.program_workdir]

        debug += [color_text('\nIcon paths:'), *self.icon_list]

        debug += [color_text('\nChecking if icons are in place:', 'darkorange', 'bold')]

        for i in self.icon_list:
            if i is not None:
                if self.file_handler.is_file(str(i)):
                    try:
                        debug.append(f'Found: {os.path.split(i)[1]}')
                    except IndexError:
                        debug.append(f'Found: {i}')

        if self.icon_list.count(None):
            debug.append(color_text(f'Missing {self.icon_list.count(None)} icon file(s)!'))

        debug_info = '<br>'.join([text.replace('\n', '<br>') for text in debug if text is not None])
        mock_download = MockDownload(info=debug_info)
        self.add_download_to_gui(mock_download)

        self.tab_widget.setCurrentIndex(0)

    def update_youtube_dl(self):
        update = Download(self.program_workdir,
                          self.youtube_dl_path,
                          ['-U', '--encoding', 'utf-8'],
                          info='Youtube-dl update',
                          parent=self)
        self.tab_widget.setCurrentIndex(0)  # Go to main
        self.add_download_to_gui(update)
        self.downloader.queue_dl(update)

    def savefile_dialog(self):
        location = QFileDialog.getExistingDirectory(parent=self.tab_widget)

        if location == '':
            pass
        elif os.path.exists(location):
            self.download_option_handler(location)
        else:
            self.alert_message('Error', 'Could not find the specified folder.'
                                        '\nReport this on githib if it keeps happening.')

    def textfile_dialog(self):
        location = \
            QFileDialog.getOpenFileName(parent=self.tab_widget, filter='*.txt',
                                        caption='Select textfile with video links')[0]
        if location == '':
            pass
        elif self.file_handler.is_file(location):
            if not self.tab3.SAVED:
                result = self.alert_message('Warning!',
                                            'Selecting new textfile,'
                                            ' this will load over the text in the download list tab!',
                                            'Do you want to load over the unsaved changes?',
                                            question=True)

                if result == QMessageBox.Yes:
                    self.settings.user_options['multidl_txt'] = location
                    self.tab4.textbrowser.setText(location)
                    self.tab3.SAVED = True
                    self.load_text_from_file()

                    self.file_handler.save_settings(self.settings.get_settings_data)
            else:
                self.settings.user_options['multidl_txt'] = location
                self.tab4.textbrowser.setText(location)
                self.tab3.SAVED = True
                self.load_text_from_file()

                self.file_handler.save_settings(self.settings.get_settings_data)
        else:
            self.alert_message('Error!', 'Could not find file!', '')
            # Check if the checkbox is toggled, and disables the line edit if it is.
            #  Also disables start button if lineEdit is empty and checkbox is not checked

    def queue_dl(self):
        command = []

        if self.tab1.checkbox.isChecked():
            if self.tab4.txt_lineedit.text() == '':
                self.alert_message('Error!', 'No textfile selected!', '')
                return

            txt = self.settings.user_options['multidl_txt']
            command += ['-a', f'{txt}']
        else:
            txt = self.tab1.url_input.text()
            command.append(f'{txt}')

        # for i in range(len(command)):
        #    command[i] = command[i].format(txt=txt)'
        # TODO: Let user pick naming format
        file_name_format = '%(title)s.%(ext)s'

        for parameter, options in self.settings.parameters.items():
            if parameter == 'Download location':
                if options['state']:
                    add = format_in_list(options['command'],
                                         self.settings.get_active_setting(parameter) + file_name_format)
                    command += add
                else:
                    command += ['-o', self.local_dl_path + file_name_format]

            elif parameter == 'Keep archive':
                if options['state']:
                    add = format_in_list(options['command'],
                                         os.path.join(os.getcwd(), self.settings.get_active_setting(parameter)))
                    command += add
            elif parameter == 'Username':
                if options['state']:
                    option = self.settings.get_active_setting(parameter)
                    if hash(option) in self._temp:
                        _password = self._temp[hash(option)]
                    else:
                        dialog = Dialog(self,
                                        'Password',
                                        f'Input you password for the account "{option}".',
                                        allow_empty=True,
                                        password=True)

                        if dialog.exec_() == QDialog.Accepted:
                            self._temp[hash(option)] = _password = dialog.option.text()
                        else:
                            self.alert_message('Error', color_text('ERROR: No password was entered.', sections=(0, 6)),
                                               '')
                            return

                    add = format_in_list(options['command'], option)
                    add += ['--password', _password]

                    command += add

            else:
                if options['state']:
                    if self.settings.get_active_setting(parameter):
                        option = self.settings.get_active_setting(parameter)
                    else:
                        option = ''
                    add = format_in_list(options['command'], option)
                    command += add

        # Sets encoding to utf-8, allowing better character support in output stream.
        command += ['--encoding', 'utf-8']

        if self.ffmpeg_path is not None:
            command += ['--ffmpeg-location', self.ffmpeg_path]

        download = Download(self.program_workdir, self.youtube_dl_path, command, parent=self)

        self.add_download_to_gui(download, tooltip=f'URL: {txt}')
        self.downloader.queue_dl(download)

    def add_download_to_gui(self, download, tooltip=''):
        scrollbar = self.tab1.process_list.verticalScrollBar()
        place = scrollbar.sliderPosition()
        go_bottom = (place == scrollbar.maximum())

        slot = QListWidgetItem(parent=self.tab1.process_list)
        gui_progress = ProcessListItem(download, slot, debug=self._debug, tooltip=tooltip)

        self.tab1.process_list.addItem(slot)
        self.tab1.process_list.setItemWidget(slot, gui_progress)

        gui_progress.adjust()
        self.tab1.process_list.resize(self.tab1.process_list.size())

        if go_bottom:
            self.tab1.process_list.scrollToBottom()

        gui_progress.stat_update()

    def stop_download(self):
        parallel = self.settings.user_options['parallel']
        if parallel and self.downloader.many_active():
            result = self.alert_message('Stop all?',
                                        'Parallel mode stops all pending and active donwloads!',
                                        'Do you want to continue?', True, True)
            if result == QMessageBox.Yes:
                self.downloader.stop_download(True)
        elif parallel:
            self.downloader.stop_download()

        elif self.downloader.has_pending():
            result = self.alert_message('Stop all?', 'Stop all pending downloads too?', '', True, True)
            if result == QMessageBox.Cancel:
                return
            else:
                self.downloader.stop_download(all_dls=(result == QMessageBox.Yes))
        else:
            self.downloader.stop_download()

    def allow_start(self):
        """ Adjusts buttons depending on users input and program state """
        self.tab1.stop_btn.setDisabled(not self.downloader.RUNNING)
        self.tab1.url_input.setDisabled(self.tab1.checkbox.isChecked())
        if not self.tab1.timer.isActive():
            self.tab1.start_btn.setDisabled(self.tab1.url_input.text() == '' and not self.tab1.checkbox.isChecked())

    # TODO: Move to tab 3?
    def load_text_from_file(self):
        if self.tab3.textedit.toPlainText() or (not self.tab3.saveButton.isEnabled()) or self.tab3.SAVED:
            content = self.file_handler.read_textfile(self.settings.user_options['multidl_txt'])
            if content is not None:
                self.tab3.textedit.clear()
                for line in content.split():
                    self.tab3.textedit.append(line.strip())

                self.tab3.textedit.append('')
                self.tab3.textedit.setFocus()
                self.tab3.saveButton.setDisabled(True)
                self.tab3.SAVED = True

            else:
                if self.settings.user_options['multidl_txt']:
                    warning = 'No textfile selected!'
                else:
                    warning = 'Could not find file!'
                self.alert_message('Error!', warning, '')
        else:
            if self.tab4.txt_lineedit.text() == '':
                self.tab3.SAVED = True
                self.load_text_from_file()
            else:
                result = self.alert_message('Warning',
                                            'Overwrite?',
                                            'Do you want to load over the unsaved changes?',
                                            question=True)
                if result == QMessageBox.Yes:
                    self.tab3.SAVED = True
                    self.load_text_from_file()

    def save_text_to_file(self):
        # TODO: Implement Ctrl+L for loading of files.
        if self.settings.user_options['multidl_txt']:
            self.file_handler.write_textfile(self.settings.user_options['multidl_txt'],
                                             self.tab3.textedit.toPlainText())

            self.tab3.saveButton.setDisabled(True)
            self.tab3.SAVED = True

        else:
            result = self.alert_message('Warning!',
                                        'No textfile selected!',
                                        'Do you want to create one?',
                                        question=True)

            if result == QMessageBox.Yes:
                save_path = QFileDialog.getSaveFileName(parent=self.tab_widget, caption='Save as', filter='*.txt')
                if not save_path[0]:
                    self.file_handler.write_textfile(save_path[0],
                                                     self.tab3.textedit.toPlainText())
                    self.settings.user_options['multidl_txt'] = save_path[0]
                    self.file_handler.save_settings(self.settings.get_settings_data)

                    self.tab4.txt_lineedit.setText(self.settings.user_options['multidl_txt'])
                    self.tab3.saveButton.setDisabled(True)
                    self.tab3.SAVED = True

    def alert_message(self, title, text, info_text, question=False, allow_cancel=False):
        """ A quick dialog for providing warnings or asking for user questions."""
        warning_window = QMessageBox(parent=self)
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

    def confirm(self):

        def do_proper_shutdown():
            """Ensures that the settings are saved properly before exiting!"""

            nonlocal self
            self.hide()
            self.file_handler.force_save = True
            self.file_handler.save_settings(self.settings.get_settings_data)
            self.file_handler.save_profiles(self.settings.get_profiles_data)
            
            self.sendClose.emit()

        # If something is still running
        if self.downloader.RUNNING:
            result = self.alert_message('Want to quit?',
                                        'Still downloading!',
                                        'Do you want to close without letting youtube-dl finish? '
                                        'Will likely leave unwanted/incomplete files in the download folder.',
                                        question=True)
            if result != QMessageBox.Yes:
                return None

        # Nothing is unsaved in textbox
        if ((self.tab3.textedit.toPlainText() == '') or (not self.tab3.saveButton.isEnabled())) or self.tab3.SAVED:
            do_proper_shutdown()

        else:
            result = self.alert_message('Unsaved changes in list!',
                                        'The download list has unsaved changes!',
                                        'Do you want to save before exiting?',
                                        question=True,
                                        allow_cancel=True)
            if result == QMessageBox.Yes:
                self.save_text_to_file()

            elif result == QMessageBox.Cancel:
                return

            do_proper_shutdown()

    def read_license(self):
        if not self.license_shown:
            content = self.file_handler.read_textfile(self.license_path)
            if content is None:
                self.alert_message('Error!', 'Failed to read textfile!')
                return
            self.tab4.abouttext_textedit.clear()
            self.tab4.abouttext_textedit.append(content)
            self.license_shown = True
        else:
            self.tab4.set_standard_text()
            self.license_shown = False


if __name__ == '__main__':
    while True:
        try:
            app = QApplication(sys.argv)
            program = GUI()

            EXIT_CODE = app.exec_()
            app = None

            if EXIT_CODE == GUI.EXIT_CODE_REBOOT:
                continue

        except (SettingsError, ProfileLoadError, json.decoder.JSONDecodeError) as e:
            if isinstance(e, ProfileLoadError):
                file = 'profiles file'
            else:
                file = 'settings file'

            warning = QMessageBox.warning(None,
                                          f'Corruption of {file}!',
                                          ''.join([str(e), '\nRestore to defaults?']),
                                          buttons=QMessageBox.Yes | QMessageBox.No)

            if warning == QMessageBox.Yes:
                filehandler = FileHandler()
                if isinstance(e, ProfileLoadError):
                    filehandler.save_profiles({})
                else:
                    setting = filehandler.load_settings(reset=True)
                    filehandler.save_settings(setting.get_settings_data)

                app = None  # Ensures the app instance is properly removed!
                continue

        break
