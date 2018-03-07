from PyQt5.QtCore import QProcess

from utils.utilities import ArgumentError


class Download(QProcess):
    def __init__(self, working_dir: str, program_path: str, commands: list, parent=None):
        """
        Download objects take required elements, and will start a process on command.
        """
        super(Download, self).__init__(parent=parent)

        if program_path is not None:
            self.program_path = program_path
        else:
            raise ArgumentError('Program path is None.')

        self.commands = commands
        self.setWorkingDirectory(working_dir)
        self.setProcessChannelMode(QProcess.MergedChannels)

    def start_dl(self):
        self.start(self.program_path, self.commands)


if __name__ == '__main__':
    pass
