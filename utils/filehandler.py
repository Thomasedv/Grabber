import json
import os
import sys
from functools import wraps, partial

from PyQt5.QtCore import QThreadPool, QTimer, Qt

from .task import Task
from .utilities import get_base_settings, SettingsClass, ProfileLoadError


def threaded_cooldown(func):
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

    timer = QTimer()
    timer.setInterval(5000)
    timer.setSingleShot(True)
    timer.setTimerType(Qt.VeryCoarseTimer)

    def wrapper(self, *args, **kwargs):

        if not hasattr(self, 'threadpool'):
            raise AttributeError(f'{self.__class__.__name__} instance does not have a threadpool attribute.')

        if not hasattr(self, 'force_save'):
            raise AttributeError(f'{self.__class__.__name__} instance does not have a force_save attribute.')

        worker = Task(func, self, *args, **kwargs)

        if timer.receivers(timer.timeout):
            timer.disconnect()

        if self.force_save:
            timer.stop()
            self.threadpool.start(worker)
            self.threadpool.waitForDone()
            return

        if timer.isActive():
            timer.timeout.connect(partial(self.threadpool.start, worker))
            timer.start()
            return

        timer.start()
        self.threadpool.start(worker)
        return

    return wrapper


def threaded(func):
    """
    Gives a function to a Task object, and then gives it to a thraed for execuution,
    to avoid using the main loop.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'threadpool'):
            raise AttributeError(f'{self.__class__.__name__} instance does not have a threadpool attribute.')

        worker = Task(func, self, *args, **kwargs)

        self.threadpool.start(worker)
        return

    return wrapper


class FileHandler:
    """
    A class to handle finding/loading/saving to files. So, IO operations.
    """

    # TODO: Implement logging, since returned values from threaded functions are discarded.
    # Need to know if errors hanppen!

    def __init__(self, settings='settings.json', profiles='profiles.json'):

        self.profile_path = profiles
        self.settings_path = settings
        self.work_dir = os.getcwd().replace('\\', '/')

        self.force_save = False

        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)

    @staticmethod
    def find_file(relative_path, exist=True):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        path = os.path.join(base_path, relative_path).replace('\\', '/')

        if exist:
            if FileHandler.is_file(path):
                # print(f'Returning existing path: {path}')
                return path
            else:
                # print(f'No found: {relative_path}')
                return None

        else:
            # print(f'Returning path: {path}')
            return path

    @threaded_cooldown
    def save_settings(self, settings):
        try:
            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=4, sort_keys=True)
                return True
        except (OSError, IOError) as e:
            # TODO: Logging!
            return False

    @threaded_cooldown
    def save_profiles(self, profiles):
        try:
            with open(self.profile_path, 'w') as f:
                json.dump(profiles, f, indent=4, sort_keys=True)
                return True
        except (OSError, IOError) as e:
            # TODO: Logging!
            return False

    def load_settings(self, reset=False) -> SettingsClass:
        """ Reads settings, or writes them if absent, or if instructed to using reset. """

        def get_file(path):
            """  """
            if FileHandler.is_file(path):
                with open(path, 'r') as f:
                    return json.load(f)
            else:
                return {}

        try:
            profiles = get_file(self.profile_path)
        except json.decoder.JSONDecodeError as e:
            raise ProfileLoadError(str(e))

        if reset:
            return SettingsClass(get_base_settings(), profiles, self)
        else:
            settings = get_file(self.settings_path)
            if settings:
                return SettingsClass(settings, profiles, self)
            else:
                return self.load_settings(reset=True)

    @staticmethod
    def is_file(path):
        return os.path.isfile(path) and os.access(path, os.X_OK)

    def find_exe(self, program):
        """Used to find executables."""
        # Possible Windows specific implementation
        local_path = os.path.join(self.work_dir, program)
        if FileHandler.is_file(local_path):
            # print(f'Returning existing isfile exe: {os.path.join(self.work_dir, program)}')
            return local_path
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if FileHandler.is_file(exe_file):
                # print(f'Returning existing exe: {os.path.abspath(exe_file)}')
                return os.path.abspath(exe_file)
        return None

    @staticmethod
    def read_textfile(path):
        if FileHandler.is_file(path):
            try:
                with open(path, 'r') as f:
                    content = f.read()
                return content
            except (OSError, IOError) as e:
                return None
        else:
            return None

    @threaded
    def write_textfile(self, path, content):
        # TODO: Warn user on error. Need smart simple method to send message from threadpool.
        if FileHandler.is_file(path):
            try:
                with open(path, 'w') as f:
                    f.write(content)
                return True
            except (OSError, IOError) as e:
                print('Error! ', e)
                return False
        else:
            print('Error!')
            return False
