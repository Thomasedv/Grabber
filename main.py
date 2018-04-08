import json
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from core import GUI
from utils.utilities import SettingsError


def main():
    while True:
        try:
            app = QApplication(sys.argv)
            program = GUI()

            EXIT_CODE = app.exec_()
            app = None

            if EXIT_CODE == GUI.EXIT_CODE_REBOOT:
                continue

        except (SettingsError, json.decoder.JSONDecodeError) as e:
            warning = QMessageBox.warning(None,
                                          'Corrupt settings',
                                          ''.join([str(e), '\nRestore default settings?']),
                                          buttons=QMessageBox.Yes | QMessageBox.No)
            if warning == QMessageBox.Yes:
                GUI.get_settings(True)
                app = None
                continue

        break


if __name__ == '__main__':
    # TODO: Test on high DPI screen.
    # TODO: Get a high DPI screen...
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    main()
