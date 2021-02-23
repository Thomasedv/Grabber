import json
import os
import sys

# If Grabber is run from start menu, working directory is set to system32, this changes to correct working directory.
if os.getcwd().lower() == r'c:\windows\system32'.lower():

    # Check if running as script, or executable.
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(__file__)
    os.chdir(os.path.realpath(application_path))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from core import GUI
from utils.filehandler import FileHandler
from utils.utilities import SettingsError, ProfileLoadError


def main():
    # Main loop
    EXIT_CODE = 1

    while True:
        try:
            app = QApplication(sys.argv)
            program = GUI()

            EXIT_CODE = app.exec_()
            app = None  # Required! Clears memory. Crashes on restart without it.

            if EXIT_CODE == GUI.EXIT_CODE_REBOOT:
                continue

        # If corrupt or wrong settings or profile files
        except (SettingsError, ProfileLoadError, json.decoder.JSONDecodeError) as e:
            if isinstance(e, ProfileLoadError):
                file = 'profiles file'
            else:
                file = 'settings file'

            warning = QMessageBox.warning(None,
                                          f'Corruption of {file}!',
                                          ''.join([str(e), '\nRestore to defaults?']),
                                          buttons=QMessageBox.Yes | QMessageBox.No)

            # If yes (to reset), do settings or profile reset.
            if warning == QMessageBox.Yes:
                filehandler = FileHandler()
                if isinstance(e, ProfileLoadError):
                    filehandler.save_profiles({})
                else:
                    setting = filehandler.load_settings(reset=True)
                    filehandler.save_settings(setting.settings_data)

                app = None  # Ensures the app instance is properly cleared!
                continue

        sys.exit(EXIT_CODE)


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    main()
