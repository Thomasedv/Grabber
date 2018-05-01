import json
import os
import sys

from .utilities import get_base_settings


class FileHandler:
    """
    A class to handle finding/loading/saving to files. So, IO operations.
    """

    def __init__(self, settings='settings.json'):
        self.settings_path = settings
        self.work_dir = os.getcwd()

        # TODO: Perform saving in a thread
        # TODO: implement a timed save, to avoid multiple saves a second.
        # For example at intervals 5, 10 or 20 seconds.

    def find_file(self, relative_path, exist=True):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        path = os.path.join(base_path, relative_path).replace('\\', '/')

        if exist:
            if self.is_file(path):
                # print(f'Returning existing path: {path}')
                return path
            else:
                # print(f'No found: {relative_path}')
                return None

        else:
            # print(f'Returning path: {path}')
            return path

    def save_settings(self, settings):
        try:
            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=4, sort_keys=True)
                return True
        except (OSError, IOError) as e:
            # TODO: Logging!
            # print('Failed to save settings!')
            # print(f'Error given:\n{e}')
            # traceback.print_exc()
            return False

    def load_settings(self, reset=False):
        """ Reads settings, or writes them if absent, or if instructed to using reset. """
        if reset:
            settings = get_base_settings()
            self.save_settings(settings)
            return settings
        else:
            if self.is_file(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    return json.load(f)
            else:
                return self.load_settings(reset=True)

    @staticmethod
    def is_file(path):
        return os.path.isfile(path) and os.access(path, os.X_OK)

    def find_exe(self, program):
        """Used to find executables."""
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if self.is_file(exe_file):
                # print(f'Returning existing exe: {os.path.abspath(exe_file)}')
                return os.path.abspath(exe_file)
        # TODO: Check if not covered by path above!
        if os.path.isfile(program):
            # print(f'Returning existing isfile exe: {os.path.join(self.work_dir, program)}')
            return os.path.join(self.work_dir, program)
        # print(f'No found: {program}')
        return None

    def read_textfile(self, path):
        if self.is_file(path):
            try:
                with open(path, 'r') as f:
                    content = f.read()
                return content
            except (OSError, IOError) as e:
                return None
        else:
            return None

    def write_textfile(self, path, content):
        if self.is_file(path):
            try:
                with open(path, 'w') as f:
                    f.write(content)
                return True
            except (OSError, IOError) as e:
                return False
        else:
            return False
