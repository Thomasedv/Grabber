import os
import sys

from PyQt5.QtCore import QProcess, pyqtSignal, Qt
from PyQt5.QtWidgets import QListWidgetItem, QTableWidgetItem, QWidget, QHBoxLayout, QLabel, QVBoxLayout, QListWidget, \
    QApplication, QSizePolicy, QLayout

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

        self.state = 'In queue'
        self.progress = ''
        self.eta = ''
        self.filesize = ''
        self.speed = ''

        self.name = ''
        self.playlist = ''
        self.error_log = ''

    def get_state(self):
        return self.state, self.progress, self.eta, self.filesize, self.speed

    def program_state_changed(self, new_state):
        if new_state == QProcess.NotRunning:
            self.state = 'Finished'
            self.progress = '100%'
            self.eta = ''
            self.filesize = ''
            self.speed = ''
            self.getOutput.emit()

    def start_dl(self):
        if self.program_path is None:
            raise TypeError('Can\'t find youtube-dl executable')

        self.start(self.program_path, self.commands)

    def process_output(self):
        """
        Reference used:
        https://github.com/MrS0m30n3/youtube-dl-gui/blob/master/youtube_dl_gui/downloaders.py
        """

        stdout = self.readAllStandardOutput().data().decode('utf-8', 'replace')

        if not stdout:
            return

        print(stdout)
        stdout_with_spaces = stdout.split(' ')
        stdout = stdout.split()

        stdout[0] = stdout[0].lstrip('\r')
        # print(stdout)
        if stdout[1] == 'Destination:':
            path, fullname = os.path.split(' '.join(stdout_with_spaces[2:]).strip("\""))
            self.name = fullname

        if stdout[0] == '[download]':
            self.state = 'Downloading'
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
                self.state = 'Already Downloaded'
                self.error_log = ' '.join(stdout)

            if stdout[-3:] == ['recorded', 'in', 'archive']:
                self.state = 'Already Downloaded'
                self.error_log = ' '.join(stdout)

            # Get filesize abort status
            if stdout[-1] == 'Aborting.':
                self.state = 'Filesize Error'

        elif stdout[0] == '[hlsnative]':
            # native hls extractor
            # see: https://github.com/rg3/youtube-dl/blob/master/youtube_dl/downloader/hls.py#L54
            self.state = 'Downloading'

            if len(stdout) == 7:
                segment_no = float(stdout[6])
                current_segment = float(stdout[4])

                # Get the percentage
                percent = '{0:.1f}%'.format(current_segment / segment_no * 100)
                self.state = percent

        elif stdout[0] == '[ffmpeg]':
            self.state = 'Post Processing'

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
            self.state = 'ERROR'
            self.error_log = ' '.join(stdout)

        self.getOutput.emit()


class ProcessListItem(QWidget):
    def __init__(self, process: Download, parent=None):
        super(ProcessListItem, self).__init__(parent=parent)
        self.process = process
        self.process.getOutput.connect(self.stat_update)
        self.line = QHBoxLayout()
        self.setFocusPolicy(Qt.NoFocus)
        self.setStyleSheet('QLabel {border-width: 1px;'
                           'border-radius: 5px;'
                           'background: #;'
                           'padding: 2px;}')

        self.status_box = QLabel(color_text('In queue', color='lawngreen'))
        self.status_box.setStyleSheet('text: red;')
        self.progress = QLabel(parent=self)
        self.eta = QLabel('', parent=self)
        self.speed = QLabel(parent=self)
        self.filesize = QLabel(parent=self)
        self.playlist = QLabel(parent=self)
        font_size_pixels = FONT_CONSOLAS.pixelSize()

        self.progress.setFixedWidth(4 * font_size_pixels)
        self.eta.setFixedWidth(4 * font_size_pixels)
        self.speed.setFixedWidth(4 * font_size_pixels)
        self.filesize.setFixedWidth(4 * font_size_pixels)
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
        self.vline.addLayout(self.line)
        self.vline.addWidget(self.info_text)

        self.setLayout(self.vline)
        self.setFixedHeight(self.sizeHint().height())

    def set_slot(self, widget):
        # Used to update list widget size
        self.slot = widget
        self.slot.setSizeHint(self.sizeHint())

    def stat_update(self):
        self.status_box.setText(color_text(self.process.state, color='lawngreen'))
        self.progress.setText(color_text(self.process.progress, color='lawngreen'))
        self.eta.setText(self.process.eta)
        self.speed.setText(self.process.speed)
        self.filesize.setText(self.process.filesize)
        self.playlist.setText(self.process.playlist)

        if self.process.state == 'ERROR':
            if not self.it_in_layout:
                self.info_text.show()
                self.it_in_layout = True

            self.status_box.setText(color_text(self.process.state))
            self.info_text.setText(f'{self.process.name if self.process.name else "Process"}'
                                   f' failed with message:\n{self.process.error_log[7:]}')

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

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(self.sizeHint().height())
        self.slot.setSizeHint(self.sizeHint())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    program = QListWidget()
    a = QListWidgetItem('test')
    program.addItem(a)
    b = ProcessListItem(Download('', '', []))
    b.set_slot(a)
    program.setItemWidget(a, b)

    program.show()
    EXIT_CODE = app.exec_()
    app = None
