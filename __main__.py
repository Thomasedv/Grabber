import json
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from core import GUI
from utils.filehandler import FileHandler
from utils.utilities import SettingsError, ProfileLoadError


def main():
    while True:
        try:
            app = QApplication(sys.argv)
            program = GUI()

            EXIT_CODE = app.exec_()
            app = None

            if EXIT_CODE == GUI.EXIT_CODE_REBOOT:
                continue

        except (SettingsError, ProfileLoadError, json.decoder.JSONDecodeError) as e:
            if isinstance(e, ProfileLoadError):
                file = 'profiles file'
            else:
                file = 'settings file'

            warning = QMessageBox.warning(None,
                                          f'Corruption of {file}!',
                                          ''.join([str(e), '\nRestore to defaults?']),
                                          buttons=QMessageBox.Yes | QMessageBox.No)

            if warning == QMessageBox.Yes:
                filehandler = FileHandler()
                if isinstance(e, ProfileLoadError):
                    filehandler.save_profiles({})
                else:
                    setting = filehandler.load_settings(reset=True)
                    filehandler.save_settings(setting.get_settings_data)

                app = None  # Ensures the app instance is properly removed!
                continue

        break


if __name__ == '__main__':
    # TODO: Test on high DPI screen.
    # TODO: Get a high DPI screen...
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    main()
