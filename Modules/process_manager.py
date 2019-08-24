import re
from collections import deque

from PyQt5.QtCore import pyqtSignal, QProcess, QObject

from Modules import Download
from utils.utilities import color_text


class Downloader(QObject):
    stateChanged = pyqtSignal()

    output = pyqtSignal(str)
    clearOutput = pyqtSignal()
    updateQueue = pyqtSignal(str)

    def __init__(self, file_handler):
        super(Downloader, self).__init__()
        self.active_download = None
        self._queue = deque()

        self.RUNNING = False
        self.error_count = 0
        self.file_handler = file_handler

    def read_process(self, download: Download):
        data = download.readAllStandardOutput().data()
        text = data.decode('utf-8', 'replace').strip()
        text = self.cmdoutput(text)
        self.output.emit(text)

    def restart_current_download(self):
        # TODO: Trigger this make trigger for restarting download!
        if self.active_download is not None and self.active_download.state() == QProcess.Running:
            self.active_download.kill()
            self.output(color_text('Restarting download!', weight='normal'))
            self.active_download.start()

    def update_youtube_dl(self, update: Download):
        self.output.emit('Update queued!')
        self.queue_dl(update)

    def queue_handler(self, process_finished=False):
        # TODO: Add parallel downloads!
        if not self.RUNNING:
            self.clearOutput.emit()

        if not self.RUNNING or process_finished:
            if self._queue:
                download = self._queue.popleft()
                self.updateQueue.emit(f'Items in queue: {len(self._queue):3}')
                self.active_download = download
                try:
                    download.start_dl()
                    self.RUNNING = True
                    self.stateChanged.emit()
                except TypeError:
                    self.error_count += 1
                    self.output.emit(color_text('DOWNLOAD FAILED!\nYuotube-dl is missing!\n'))
                    return self.queue_handler(process_finished=True)

            else:

                self.active_download = None
                self.RUNNING = False
                self.stateChanged.emit()
                self.output.emit(f'Error count: '
                                 f'{self.error_count if self.error_count == 0 else color_text(str(self.error_count),
                                                                                              "darkorange", "bold")}.')
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
        download.readyReadStandardOutput.connect(lambda: self.read_process(download))
        download.stateChanged.connect(self.program_state_changed)
        self._queue.append(download)
        self.queue_handler()

    def cmdoutput(self, info):
        replace_dict = {
            '[ffmpeg] ': '',
            '[youtube] ': ''
        }
        substrs = sorted(replace_dict, key=len, reverse=True)
        if info.startswith('ERROR'):
            self.error_count += 1
            info = info.replace('ERROR', '<span style=\"color: darkorange; font-weight: bold;\">ERROR</span>')
        info = re.sub(r'\s+$', '', info, 0, re.M)
        info = re.sub(' +', ' ', info)
        regexp = re.compile('|'.join(map(re.escape, substrs)))

        return regexp.sub(lambda match: replace_dict[match.group(0)], info)
