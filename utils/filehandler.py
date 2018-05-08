import json
import os
import sys
from functools import wraps, partial

from PyQt5.QtCore import QThreadPool, QTimer, Qt

from .task import Task
from .utilities import get_base_settings


def threaded(func):
    """ A decorator that makes it so the decorate function will run
     in a thread, but prevents the same function from being rerun for a given time.
     After give time, the last call not performed will be executed.

     Purpose of this is to ensure writing to disc does not happen all too often,
     avoid IO operations reducing GUI smoothness.

     A drawback is that if a user "queues" a save, but reloads the file before the last save,
     they will load a version that is not up to date. This is not a problem for Grabber, as the
     settings are only read on startup. However, it's a drawback that prevents a more general use.

     This decorator requires being used in an instance which has a threadpool instance.
     """
    cooldown_time = {}
    timer = QTimer()
    timer.setInterval(5000)
    timer.setSingleShot(True)
    timer.setTimerType(Qt.VeryCoarseTimer)

    if func.__name__ not in cooldown_time:
        cooldown_time[func.__name__] = timer

    @wraps(func)
    def wrapper(self, *args, **kwargs):

        timer = cooldown_time[func.__name__]

        worker = Task(func, self, *args, **kwargs)
        if timer.receivers(timer.timeout):
            timer.disconnect()

        if self.force_save:
            timer.stop()
            self.threadpool.start(worker)
            self.threadpool.waitForDone()

        if timer.isActive():
            # TODO: Find a way to make sure saving happens when the user closes the program.

            timer.timeout.connect(partial(self.threadpool.start, worker))
            timer.start()
            return

        timer.start()
        self.threadpool.start(worker)
        return

    return wrapper


class FileHandler:
    """
    A class to handle finding/loading/saving to files. So, IO operations.
    """

    def __init__(self, settings='settings.json'):
        self.settings_path = settings
        self.work_dir = os.getcwd()

        # TODO: Perform saving in a threadpool with runnable
        # TODO: implement a timed save, to avoid multiple saves a second.
        self.force_save = False

        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)

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

    @threaded
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
        local_path = os.path.join(self.work_dir, program)
        if self.is_file(local_path):
            # print(f'Returning existing isfile exe: {os.path.join(self.work_dir, program)}')
            return local_path
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if self.is_file(exe_file):
                # print(f'Returning existing exe: {os.path.abspath(exe_file)}')
                return os.path.abspath(exe_file)
        # TODO: Check if not covered by path above!

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
