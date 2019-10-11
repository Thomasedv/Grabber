import re
from collections import deque
from textwrap import dedent

from PyQt5.QtCore import pyqtSignal, QProcess, QObject

from utils.utilities import color_text
from .download_element import Download


class Downloader(QObject):
    stateChanged = pyqtSignal()

    output = pyqtSignal(str)
    clearOutput = pyqtSignal()
    updateQueue = pyqtSignal(str)

    def __init__(self, file_handler):
        super(Downloader, self).__init__()
        self.active_download: Download = None
        self._queue = deque()

        self.RUNNING = False
        self.error_count = 0
        self.file_handler = file_handler
        # Make this point to parallel queue for multi dl.
        self.queue_handler = self._single_queue_handler

    def read_process(self):
        program = self.active_download
        self.output.emit(' | '.join(program.get_state()))

    def restart_current_download(self):
        # TODO: Trigger this make trigger for restarting download!
        if self.active_download is not None and self.active_download.state() == QProcess.Running:
            self.active_download.kill()
            self.output.emit(color_text('Restarting download!', weight='normal'))
            self.active_download.start()
        else:
            self.output.emit('No active download to restart!')

    def update_youtube_dl(self, update: Download):
        self.output.emit('Update queued!')
        self.queue_dl(update)

    def _single_queue_handler(self, process_finished=False):
        # TODO: Add parallel downloads!
        if not self.RUNNING:
            self.clearOutput.emit()

        if not self.RUNNING or process_finished:
            # TODO: Detect crash when redistributable C++ is not present, if possible

            # if process_finished:
            #     error_code = self.active_download.exitCode()
            #     if error_code:
            #         self.output.emit(color_text(f'Youtube-dl closed with error code {error_code}! '
            #                                     'Is the required C++ distributable installed?'))
            #         self.error_count += 1

            if self._queue:
                download = self._queue.popleft()
                self.updateQueue.emit(f'Items in queue: {len(self._queue):3}')
                self.active_download = download
                try:
                    download.start_dl()
                    self.RUNNING = True
                    self.stateChanged.emit()
                except TypeError as e:
                    self.error_count += 1
                    self.output.emit(color_text(f'FAILED with error {e}'))
                    return self.queue_handler(process_finished=True)

            else:
                self.active_download = None
                self.RUNNING = False
                self.stateChanged.emit()

                error_report = 0 if not self.error_count else color_text(str(self.error_count), "darkorange", "bold")
                self.output.emit(f'Error count: {error_report}.')
                self.error_count = 0
        self.updateQueue.emit(f'Items in queue: {len(self._queue):3}')

    # When the current download is started/stopped then this runs.
    def program_state_changed(self, new_state):
        if new_state == QProcess.NotRunning:
            self.active_download.disconnect()
            self.output.emit('\nDone\n')
            self.queue_handler(process_finished=True)
        elif new_state == QProcess.Running:
            self.output.emit(color_text('Starting...\n', 'lawngreen', 'normal', sections=(0, 8)))

        return

    def has_pending(self):
        return bool(self._queue)

    def stop_download(self, all_dls=False):
        if all_dls:
            for download in self._queue:
                download.disconnect()
                del download
            self._queue.clear()
            self.output.emit('Stopped all downloads...')
        else:
            self.output.emit('Stopped a download...')

        if self.active_download is not None:
            if self.active_download.state() == QProcess.Running:
                self.active_download.kill()
            else:
                self.output.emit('No active downloads...')

    def queue_dl(self, download: Download):
        download.getOutput.connect(self.read_process)
        download.stateChanged.connect(self.program_state_changed)
        self._queue.append(download)
        self.queue_handler()

    def cmdoutput(self):
        # # TODO: Remove here, use in download!
        # replace_dict = {
        #     '[ffmpeg] ': '',
        #     '[youtube] ': ''
        # }
        # substrs = sorted(replace_dict, key=len, reverse=True)
        # if info.startswith('ERROR'):
        #     self.error_count += 1
        #     info = info.replace('ERROR', '<span style=\"color: darkorange; font-weight: bold;\">ERROR</span>')
        # info = re.sub(r'\s+$', '', info, 0, re.M)
        # info = re.sub(' +', ' ', info)
        # regexp = re.compile('|'.join(map(re.escape, substrs)))
        # return info
        # return regexp.sub(lambda match: replace_dict[match.group(0)], info)
        pass
