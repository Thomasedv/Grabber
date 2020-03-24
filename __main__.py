import json
import os
import sys

# If Grabber is run from start menu, working directory is set to system32, this changes to file location.
if os.getcwd().lower() == r'c:\windows\system32'.lower():  # Bit of a hack, but if you have this, your fault
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

    while True:
        EXIT_CODE = 1
        try:
            app = QApplication(sys.argv)
            program = GUI()

            EXIT_CODE = app.exec_()
            app = None  # Required! Crashes on restart without.

            if EXIT_CODE == GUI.EXIT_CODE_REBOOT:
                continue

        # For when startup fails
        except (SettingsError, ProfileLoadError, json.decoder.JSONDecodeError) as e:
            if isinstance(e, ProfileLoadError):
                file = 'profiles file'
            else:
                file = 'settings file'

            warning = QMessageBox.warning(None,
                                          f'Corruption of {file}!',
                                          ''.join([str(e), '\nRestore to defaults?']),
                                          buttons=QMessageBox.Yes | QMessageBox.No)

            # If yes, do settings or profile reset.
            if warning == QMessageBox.Yes:
                filehandler = FileHandler()
                if isinstance(e, ProfileLoadError):
                    filehandler.save_profiles({})
                else:
                    setting = filehandler.load_settings(reset=True)
                    filehandler.save_settings(setting.settings_data)

                app = None  # Ensures the app instance is properly removed!
                continue

        sys.exit(EXIT_CODE)


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    main()
