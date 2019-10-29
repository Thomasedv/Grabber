from collections import deque

from PyQt5.QtCore import pyqtSignal, QProcess, QObject

from Modules.download_element import Download
from utils.utilities import color_text


class Downloader(QObject):
    stateChanged = pyqtSignal()

    output = pyqtSignal(str)
    clearOutput = pyqtSignal()

    def __init__(self, file_handler, mode=0):
        super(Downloader, self).__init__()
        self.active_download: Download = None
        self._queue = deque()
        self.mode = mode
        self.RUNNING = False
        self.error_count = 0
        self.file_handler = file_handler
        # Make this point to parallel queue for multi dl.
        if mode:
            self.queue_handler = self._parallel_queue_handler
            self.active_download = []
        else:
            self.queue_handler = self._single_queue_handler
            self.active_download = None

        # For parallel downloads
        self.active = 0

    def set_mode(self, parallel=False):
        if parallel:
            self.queue_handler = self._parallel_queue_handler
            self.active_download = []
            self.active = 0
        else:
            self.queue_handler = self._single_queue_handler
            self.active_download = None

    def restart_current_download(self):
        # TODO: Trigger this make trigger for restarting download!
        # Only works in single mode
        if self.active_download is not None:
            if isinstance(self.active_download, Download) and self.active_download.state() == QProcess.Running:
                self.active_download.kill()
                # self.output.emit(color_text('Restarting download!', weight='normal'))
                self.active_download.start()
            elif isinstance(self.active_download, list):
                for i in self.active_download:
                    i.kill()
                    i.start()
        # else:
        #     self.output.emit('No active download to restart!')

    def _parallel_queue_handler(self, process_finished=False):
        if not self.RUNNING:
            self.clearOutput.emit()

        if not self.RUNNING or process_finished or self.active < 4:
            if self._queue:
                download = self._queue.popleft()
                self.active_download.append(download)
                try:
                    download.start_dl()
                    self.RUNNING = True
                    self.stateChanged.emit()
                except TypeError as e:
                    self.error_count += 1
                    # self.output.emit(color_text(f'FAILED with error {e}'))
                    return self.queue_handler(process_finished=True)
                self.active += 1

            else:

                if not self.active:
                    self.RUNNING = False
                    self.stateChanged.emit()

                    error_report = 0 if not self.error_count else color_text(str(self.error_count), "darkorange",
                                                                             "bold")
                    # self.output.emit(f'Error count: {error_report}.')
                    self.error_count = 0

    def _single_queue_handler(self, process_finished=False):
        # if not self.RUNNING:
        #     self.clearOutput.emit()

        if not self.RUNNING or process_finished:
            # TODO: Detect crash when redistributable C++ is not present, if possible

            if self._queue:
                download = self._queue.popleft()
                self.active_download = download
                try:
                    download.start_dl()
                    self.RUNNING = True
                    self.stateChanged.emit()
                except TypeError as e:
                    self.error_count += 1
                    # self.output.emit(color_text(f'FAILED with error {e}'))
                    return self.queue_handler(process_finished=True)

            else:
                self.active_download = None
                self.RUNNING = False
                self.stateChanged.emit()

                error_report = 0 if not self.error_count else color_text(str(self.error_count), "darkorange", "bold")
                # self.output.emit(f'Error count: {error_report}.')
                self.error_count = 0

    # When the current download is started/stopped then this runs.
    def program_state_changed(self, program: Download):
        new_state = program.state()
        if new_state == QProcess.NotRunning:
            program.disconnect()
            # self.output.emit('\nDone\n')
            if self.mode:
                self.active -= 1
            self.queue_handler(process_finished=True)

        return

    def has_pending(self):
        return bool(self._queue)

    def many_active(self):
        return self.active > 1 or self.has_pending()

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
            if isinstance(self.active_download, Download):
                if self.active_download.state() == QProcess.Running:
                    self.active_download.kill()
                    self.active_download.set_status_killed()
            elif isinstance(self.active_download, list):
                for i in self.active_download:
                    i.kill()
                    i.set_status_killed()
            else:
                self.output.emit('No active downloads...')

    def queue_dl(self, download: Download):
        download.stateChanged.connect(lambda x, dl=download: self.program_state_changed(dl))
        self._queue.append(download)
        self.queue_handler()

