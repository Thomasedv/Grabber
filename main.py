import sys
import json
from core import GUI, SettingsError, QMessageBox
from PyQt5.QtWidgets import QApplication


def main():
    while True:
        try:
            app = QApplication(sys.argv)
            program = GUI()

            EXIT_CODE = app.exec_()
            app = None

            if not (EXIT_CODE == GUI.EXIT_CODE_REBOOT):
                break

        except (SettingsError, json.decoder.JSONDecodeError) as e:
            warning = QMessageBox.warning(None,
                                          'Corrupt settings',
                                          ''.join([str(e),'\nRestore default settings?']),
                                          buttons=QMessageBox.Yes | QMessageBox.No)
            if warning == QMessageBox.Yes:
                GUI.write_default_settings(True)
                app = None
                continue
            break

if __name__ == '__main__':
    main()