import os
import re
import traceback
from collections import deque

from PyQt5.QtCore import QProcess, pyqtSignal, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy, QMenu, QTextBrowser

from utils.utilities import FONT_CONSOLAS, color_text


class Download(QProcess):
    getOutput = pyqtSignal()

    def __init__(self, working_dir: str, program_path: str, commands: list, info='', parent=None):
        """
        Download objects take commands, and will start a process on triggered.
        """
        super(Download, self).__init__(parent=parent)

        self.program_path = program_path

        self.commands = commands
        self.setWorkingDirectory(working_dir)
        self.setProcessChannelMode(QProcess.MergedChannels)
        self.readyReadStandardOutput.connect(self.process_output)
        self.stateChanged.connect(self.program_state_changed)

        self.status = 'In queue'
        self.progress = ''
        self.eta = ''
        self.filesize = ''
        self.speed = ''

        self.name = ''
        self.file_path = ''
        self.playlist = ''
        self.error_count = 0

        # Info channel
        self.info = info
        # Potential error for user
        self.potential_error_log = ''
        # Raw logs from program. TODO: Maybe add some info here when initializing, plus return code perhaps?
        self.debug_log = []
        self.done = False

        self.program_log = deque(maxlen=3)

    def program_state_changed(self, new_state):
        """Triggers actions when the QProcess stops"""
        if new_state == QProcess.NotRunning:
            self.done = True
            self.debug_log.append(f'Program closed with error code: {self.exitCode()}')
            if self.status not in ('Aborted', 'ERROR', 'Already Downloaded'):
                if self.exitCode() != 0:
                    self.status = 'ERROR'
                    self.progress = ''

                    if not self.info and self.potential_error_log:
                        self.info = self.potential_error_log
                    elif not self.info:
                        self.info = 'Unknown error'

                else:
                    self.status = 'Finished'
                    self.progress = '100%'
                self.eta = ''
                self.filesize = ''
                self.speed = ''

                self.getOutput.emit()

    def set_status_killed(self):
        """ When killed, set this state"""

        self.status = 'Aborted'
        self.progress = ''
        self.eta = ''
        self.filesize = ''
        self.speed = ''
        self.info = 'Aborted by user'

        self.done = True
        self.getOutput.emit()

    def start_dl(self):
        """ Starts program, youtube-dl.exe """
        if self.program_path is None:
            raise TypeError('Can\'t find youtube-dl executable')

        self.start(self.program_path, self.commands)
        self.status = 'Started'
        self.getOutput.emit()

    def process_output(self):
        """
        Reference used:
        https://github.com/MrS0m30n3/youtube-dl-gui/blob/master/youtube_dl_gui/downloaders.py
        """

        output = self.readAllStandardOutput().data().decode('utf-8', 'replace')

        if not output:
            return

        try:
            for line in output.split('\n'):
                self.debug_log.append(line)
                if not line:
                    continue

                stdout_with_spaces = line.split(' ')

                stdout = line.split()

                if not stdout:
                    continue

                self.program_log.append(line.split('\r')[-1].strip())

                stdout[0] = stdout[0].lstrip('\r')

                if stdout[0] == '[download]':
                    self.status = 'Downloading'

                    if stdout[1] == 'Destination:':
                        path, fullname = os.path.split(' '.join(stdout[2:]).strip("\""))
                        self.name = fullname
                        self.file_path = os.path.join(path, fullname)

                    # Get progress info
                    if '%' in stdout[1]:
                        if stdout[1] == '100%':
                            self.progress = '100%'
                            self.eta = ''
                            self.filesize = stdout[3]
                            self.speed = ''
                        else:
                            self.progress = stdout[1]
                            self.eta = stdout[7]
                            self.filesize = stdout[3]
                            self.speed = stdout[5]

                    # Get playlist info

                    if stdout[1] == 'Downloading' and stdout[2] == 'video':
                        self.playlist = stdout[3] + '/' + stdout[5]

                    # Remove the 'and merged' part from stdout when using ffmpeg to merge the formats
                    if stdout[-3] == 'downloaded' and stdout[-1] == 'merged':
                        stdout = stdout[:-2]
                        self.progress = '100%'

                    # Get file already downloaded status
                    if stdout[-1] == 'downloaded':
                        self.status = 'Already Downloaded'
                        self.info = ' '.join(stdout)
                        path, fullname = os.path.split(' '.join(stdout_with_spaces[1:-4]).strip("\""))
                        self.file_path = os.path.join(path, fullname)

                    if stdout[-3:] == ['recorded', 'in', 'archive']:
                        self.status = 'Already Downloaded'
                        self.info = ' '.join(stdout)
                        # Path not provided in output, possible manual fix later

                    # Get filesize abort status
                    if stdout[-1] == 'Aborting.':
                        self.status = 'Filesize Error'

                elif stdout[0] == '[hlsnative]':
                    # native hls extractor
                    # see: https://github.com/rg3/youtube-dl/blob/master/youtube_dl/downloader/hls.py#L54
                    self.status = 'Downloading'

                    if len(stdout) == 7:
                        segment_no = float(stdout[6])
                        current_segment = float(stdout[4])

                        # Get the percentage
                        percent = '{0:.1f}%'.format(current_segment / segment_no * 100)
                        self.progress = percent

                elif stdout[0] == '[ffmpeg]':
                    self.status = 'Post Processing'

                    if stdout[1] == 'Merging':
                        path, fullname = os.path.split(' '.join(stdout_with_spaces[4:]).strip("\""))
                        self.name = fullname
                        self.file_path = os.path.join(path, fullname)

                        # Get final extension ffmpeg post process simple (not file merge)
                    if stdout[1] == 'Destination:':
                        path, fullname = os.path.split(' '.join(stdout_with_spaces[2:]).strip("\""))
                        self.name = fullname
                        self.file_path = os.path.join(path, fullname)

                        # Get final extension after recoding process
                    if stdout[1] == 'Converting':
                        path, fullname = os.path.split(' '.join(stdout_with_spaces[8:]).strip("\""))
                        self.name = fullname
                        self.file_path = os.path.join(path, fullname)

                elif 'frame=' in stdout:
                    progress_pattern = re.compile(
                        r'(frame|fps|size|time|bitrate|speed)\s*\=\s*(\S+)'
                    )

                    items = {
                        key: value for key, value in progress_pattern.findall(line)
                    }
                    if not items:
                        continue

                    if not self.info.startswith('[ffmpeg download mode]'):
                        self.info = '[ffmpeg download mode] Progress shows the frame count' + self.info
                    self.speed = items.get('bitrate', self.speed)
                    self.progress = items.get('frame', self.progress)
                    self.filesize = items.get('size', self.filesize)

                elif stdout[0] == 'ERROR:':
                    self.status = 'ERROR'
                    self.error_count += 1
                    self.info = ' '.join(stdout) + f'\nTotal errors {self.error_count}'

                elif 'youtube-dl.exe: error:' in line:
                    self.potential_error_log += ' '.join(stdout).replace('youtube-dl.exe: ', '')
                self.getOutput.emit()
        except IndexError:
            traceback.print_exc()
        finally:
            self.getOutput.emit()


class MockDownload(Download):
    """Used for showing debug info"""
    def __init__(self, info, parent=None):
        super(MockDownload, self).__init__('', '', [], info=info, parent=parent)
        self.status = 'Debug Info'
        self.done = True

    def process_output(self):
        pass


class ProcessListItem(QWidget):
    """ ListItem that shows attached process state"""
    def __init__(self, process: Download, slot, debug=False, parent=None, tooltip=''):
        super(ProcessListItem, self).__init__(parent=parent)
        self.process = process
        self.slot = slot
        self.process.getOutput.connect(self.stat_update)
        self.line = QHBoxLayout()
        self.setFocusPolicy(Qt.NoFocus)
        # self.setStyleSheet()
        self._open_window = None

        self.status_box = QLabel(color_text(self.process.status, color='lawngreen'))
        self.status_box.setContextMenuPolicy(Qt.CustomContextMenu)
        self.status_box.customContextMenuRequested.connect(self.open_info_menu)

        self.progress = QLabel(parent=self)
        self.progress.setAlignment(Qt.AlignCenter)
        self.eta = QLabel('', parent=self)
        self.eta.setAlignment(Qt.AlignCenter)
        self.speed = QLabel(parent=self)
        self.speed.setAlignment(Qt.AlignCenter)
        self.filesize = QLabel(parent=self)
        self.filesize.setAlignment(Qt.AlignCenter)
        self.playlist = QLabel(parent=self)
        self.playlist.setAlignment(Qt.AlignCenter)
        font_size_pixels = FONT_CONSOLAS.pixelSize()

        self.status_box.setBaseSize(20 * font_size_pixels, self.sizeHint().height())

        self.progress.setFixedWidth(5 * font_size_pixels)
        self.eta.setFixedWidth(4 * font_size_pixels)
        self.speed.setFixedWidth(6 * font_size_pixels)
        self.filesize.setFixedWidth(6 * font_size_pixels)
        self.playlist.setFixedWidth(6 * font_size_pixels)

        self.line.addWidget(self.progress, 0)
        self.line.addWidget(self.eta, 0)
        self.line.addWidget(self.speed, 0)
        self.line.addWidget(self.filesize, 0)
        self.line.addWidget(self.playlist, 0)

        self.line2 = QHBoxLayout()
        self.line2.addWidget(self.status_box, 0)
        self.line2.addStretch(1)
        self.line2.addLayout(self.line, 1)

        self.info_label_in_layout = False
        self.info_label = QLabel('', parent=self)
        self.info_label.setToolTip(tooltip)
        self.info_label.setWordWrap(True)
        self.info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.info_label.hide()
        self.info_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.info_label.customContextMenuRequested.connect(self.open_file_menu)

        self.vline = QVBoxLayout()
        self.vline.addLayout(self.line2, 0)
        self.vline.addWidget(self.info_label, 1)
        self.setLayout(self.vline)

        self.progress.setStyleSheet(f'background: {"#484848" if self.process.progress else "#303030"}')
        self.eta.setStyleSheet(f'background: {"#484848" if self.process.eta else "#303030"}')
        self.speed.setStyleSheet(f'background: {"#484848" if self.process.speed else "#303030"}')
        self.filesize.setStyleSheet(f'background: {"#484848" if self.process.filesize else "#303030"}')
        self.playlist.setStyleSheet(f'background: {"#484848" if self.process.playlist else "#303030"}')

        self._debug = debug

    def open_file(self):
        if self.is_running() or not self.process.file_path or self.process.status == 'ERROR':
            old_text = self.info_label.text()
            if old_text.endswith('\nNo file to open!'):
                return

            self.info_label.setText(old_text + '\nNo file to open!')
            self.adjust()
            return

        try:
            # Windows specific implementation
            QProcess.startDetached('explorer', ['/select,', self.process.file_path])
        except:
            self.info_label.setText(self.info_label.text() + '\nFailed to open in explorer')
            # Print failed to open file to user!

    def open_file_menu(self, event):
        if self.process.status in ('ERROR', 'Aborted', 'Filesize Error'):
            return
        menu = QMenu(self.sender())
        menu.addAction('Open folder', self.open_file)
        menu.exec(QCursor.pos())

    def open_info_menu(self, event):
        menu = QMenu(self.sender())
        menu.addAction('Show complete log', self.open_log)
        menu.exec(QCursor.pos())

    def open_log(self):
        info_log = QTextBrowser()
        info_log.setObjectName('TextFileEdit')
        info_log.setStyleSheet(self.window().styleSheet())
        info_log.setWindowTitle('Raw output')
        # Sets value to None when closed
        info_log.closeEvent = lambda _, inflog=info_log: setattr(self, '_open_window', None)

        # If a window already has been opened
        if self._open_window is not None:
            try:
                self._open_window.close()
            except:
                pass
        self._open_window = info_log

        info_log.setText('\n'.join(self.process.debug_log))
        info_log.show()

    def toggle_debug(self, debug_state):
        self._debug = debug_state
        self.stat_update()

    def adjust(self):
        self.setFixedHeight(self.sizeHint().height())
        self.info_label.setFixedWidth(self.parent().width() - 18)
        self.slot.setSizeHint(self.sizeHint())

    def resizeEvent(self, event) -> None:
        super(ProcessListItem, self).resizeEvent(event)
        self.adjust()

    def is_running(self):
        return not self.process.done

    def stat_update(self):
        def show_infolabel():
            nonlocal self
            if not self.info_label_in_layout:
                self.info_label.show()
                self.info_label_in_layout = True

        if self._open_window is not None:
            self._open_window.setText('\n'.join(self.process.debug_log))

        self.status_box.setText(color_text(self.process.status, color='lawngreen'))
        self.progress.setText(color_text(self.process.progress, color='lawngreen'))
        self.eta.setText(self.process.eta)
        self.speed.setText(self.process.speed)
        self.filesize.setText(self.process.filesize)
        self.playlist.setText(self.process.playlist)

        self.progress.setStyleSheet(f'background: {"#484848" if self.process.progress else "#303030"}')
        self.eta.setStyleSheet(f'background: {"#484848" if self.process.eta else "#303030"}')
        self.speed.setStyleSheet(f'background: {"#484848" if self.process.speed else "#303030"}')
        self.filesize.setStyleSheet(f'background: {"#484848" if self.process.filesize else "#303030"}')
        self.playlist.setStyleSheet(f'background: {"#484848" if self.process.playlist else "#303030"}')

        if self.process.status == 'ERROR':
            show_infolabel()

            self.status_box.setText(color_text(self.process.status))
            self.info_label.setText(f'{self.process.name if self.process.name else "Process"}'
                                    f' failed with message:\n{self.process.info.replace("ERROR:", "").lstrip()}')
        elif self.process.status == 'Aborted':
            self.status_box.setText(color_text(self.process.status))
            show_infolabel()
            name = ' | ' + self.process.name if self.process.name else ''
            self.info_label.setText(self.process.info + name)

        elif self.process.info or self._debug or self.process.name:
            # Shows the info label if there is debug info, or if any other field has info
            if self._debug and not any((self.process.info, self.process.name)):
                if self.process.program_log:
                    show_infolabel()
            else:
                show_infolabel()

            content = []

            if self.process.name:
                content.append(self.process.name.strip())

            if self.process.info:
                content.append(self.process.info.replace("[download] ", ""))

            if self._debug:
                content += ['<br>Debug info:<br>'] + list(self.process.program_log)

            self.info_label.setText('<br>'.join(content))

        self.adjust()
