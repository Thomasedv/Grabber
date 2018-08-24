from PyQt5.QtCore import QProcess


class Download(QProcess):
    def __init__(self, working_dir: str, program_path: str, commands: list, parent=None):
        """
        Download objects take required elements, and will start a process on command.
        """
        super(Download, self).__init__(parent=parent)

        self.program_path = program_path

        self.commands = commands
        self.setWorkingDirectory(working_dir)
        self.setProcessChannelMode(QProcess.MergedChannels)

    def start_dl(self):
        if self.program_path is None:
            raise TypeError('Missing youtube-dl path.')
        # TODO: Handler errors with starting youtube-dl

        self.errorOccurred.connect(lambda: print('error', self.error()))

        self.start(self.program_path, self.commands)


if __name__ == '__main__':
    pass
