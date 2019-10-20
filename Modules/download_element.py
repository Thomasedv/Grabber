import os
import traceback

from PyQt5.QtCore import QProcess, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy

from utils.utilities import FONT_CONSOLAS, color_text


class Download(QProcess):
    getOutput = pyqtSignal()

    def __init__(self, working_dir: str, program_path: str, commands: list, parent=None):
        """
        Download objects take required elements, and will start a process on command.
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
        self.playlist = ''
        self.error_log = ''
        self.pot_error_log = ''

    def get_status(self):
        return self.status, self.progress, self.eta, self.filesize, self.speed

    def program_state_changed(self, new_state):
        print(new_state)
        if new_state == QProcess.NotRunning:
            if self.status not in ('Aborted', 'ERROR', 'Already Downloaded'):
                if self.exitCode() != 0:
                    self.status = 'ERROR'
                    self.progress = ''

                    if not self.error_log and self.pot_error_log:
                        self.error_log = self.pot_error_log
                    elif not self.error_log:
                        self.error_log = 'Unknown error'

                else:
                    self.status = 'Finished'
                    self.progress = '100%'
                self.eta = ''
                self.filesize = ''
                self.speed = ''
                self.getOutput.emit()

    def set_status_killed(self):
        self.status = 'Aborted'
        self.progress = ''
        self.eta = ''
        self.filesize = ''
        self.speed = ''
        self.error_log = 'Aborted by user'
        self.getOutput.emit()

    def start_dl(self):
        if self.program_path is None:
            raise TypeError('Can\'t find youtube-dl executable')

        self.start(self.program_path, self.commands)
        self.status = 'Started'
        print(self.exitCode())


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
                print(line)
                if not line:
                    continue

                stdout_with_spaces = line.split(' ')

                stdout = line.split()

                if not stdout:
                    continue

                stdout[0] = stdout[0].lstrip('\r')

                if stdout[0] == '[download]':
                    self.status = 'Downloading'

                    if stdout[1] == 'Destination:':
                        path, fullname = os.path.split(' '.join(stdout[2:]).strip("\""))
                        self.name = fullname

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
                        self.error_log = ' '.join(stdout)

                    if stdout[-3:] == ['recorded', 'in', 'archive']:
                        self.status = 'Already Downloaded'
                        self.error_log = ' '.join(stdout)

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
                        self.status = percent

                elif stdout[0] == '[ffmpeg]':
                    self.status = 'Post Processing'

                    if stdout[1] == 'Merging':
                        path, fullname = os.path.split(' '.join(stdout_with_spaces[4:]).strip("\""))
                        self.name = fullname

                        # Get final extension ffmpeg post process simple (not file merge)
                    if stdout[1] == 'Destination:':
                        path, fullname = os.path.split(' '.join(stdout_with_spaces[2:]).strip("\""))
                        self.name = fullname

                        # Get final extension after recoding process
                    if stdout[1] == 'Converting':
                        path, fullname = os.path.split(' '.join(stdout_with_spaces[8:]).strip("\""))
                        self.name = fullname

                elif stdout[0] == 'ERROR:':
                    self.status = 'ERROR'
                    self.error_log += ' '.join(stdout)

                elif 'youtube-dl.exe: error:' in line:
                    self.pot_error_log += ' '.join(stdout).replace('youtube-dl.exe: ', '')
                self.getOutput.emit()
        except IndexError:
            traceback.print_exc()


class ProcessListItem(QWidget):
    def __init__(self, process: Download, slot, parent=None):
        super(ProcessListItem, self).__init__(parent=parent)
        self.process = process
        self.slot = slot
        self.process.getOutput.connect(self.stat_update)
        self.line = QHBoxLayout()
        self.setFocusPolicy(Qt.NoFocus)
        # self.setStyleSheet()

        self.status_box = QLabel(color_text('In queue', color='lawngreen'))
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

        self.progress.setFixedWidth(5 * font_size_pixels)
        self.eta.setFixedWidth(4 * font_size_pixels)
        self.speed.setFixedWidth(6 * font_size_pixels)
        self.filesize.setFixedWidth(6 * font_size_pixels)
        self.playlist.setFixedWidth(4 * font_size_pixels)

        self.line.addWidget(self.status_box, 1)
        self.line.addWidget(self.progress, 0)
        self.line.addWidget(self.eta, 0)
        self.line.addWidget(self.speed, 0)
        self.line.addWidget(self.filesize, 0)
        self.line.addWidget(self.playlist, 0)

        self.it_in_layout = False
        self.info_text = QLabel('', parent=self)
        self.info_text.setWordWrap(True)
        self.info_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.info_text.hide()

        self.vline = QVBoxLayout()
        self.vline.addLayout(self.line, 0)
        self.vline.addWidget(self.info_text, 1)

        self.setLayout(self.vline)

        self.progress.setStyleSheet(f'background: {"#484848" if self.process.progress else "#303030"}')
        self.eta.setStyleSheet(f'background: {"#484848" if self.process.eta else "#303030"}')
        self.speed.setStyleSheet(f'background: {"#484848" if self.process.speed else "#303030"}')
        self.filesize.setStyleSheet(f'background: {"#484848" if self.process.filesize else "#303030"}')
        self.playlist.setStyleSheet(f'background: {"#484848" if self.process.playlist else "#303030"}')

    def adjust(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setFixedHeight(self.sizeHint().height())
        self.slot.setSizeHint(self.sizeHint())

    def stat_update(self):
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
            if not self.it_in_layout:
                self.info_text.show()
                self.it_in_layout = True

            self.status_box.setText(color_text(self.process.status))
            self.info_text.setText(f'{self.process.name if self.process.name else "Process"}'
                                   f' failed with message:\n{self.process.error_log.replace("ERROR:", "")}')
        elif self.process.status == 'Aborted':
            self.status_box.setText(color_text(self.process.status))
            if not self.it_in_layout:
                self.info_text.show()
                self.it_in_layout = True
                self.info_text.setText(self.process.error_log)
            else:
                self.info_text.setText(self.process.error_log +
                                       ' | ' + self.process.name)

        elif self.process.error_log:
            if not self.it_in_layout:
                self.info_text.show()
                self.it_in_layout = True
            self.info_text.setText(f'{self.process.error_log.replace("[download] ", "")}')

        else:
            if self.process.name and not self.it_in_layout:
                self.info_text.show()
                self.it_in_layout = True

            if self.process.name:
                self.info_text.setText(self.process.name)

        self.adjust()
