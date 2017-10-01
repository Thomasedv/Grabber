import sys
import json
from core import GUI, SettingsError, QMessageBox
from PyQt5.QtWidgets import QApplication


def main():
    EXIT_CODE = GUI.EXIT_CODE_REBOOT

    while True:
        try:
            app = QApplication(sys.argv)
            qProcess = GUI()

            EXIT_CODE = app.exec_()
            app = None


            if EXIT_CODE == -123456789:
                continue
            else:
                break

        except (SettingsError,json.decoder.JSONDecodeError) as e :
            warning = QMessageBox.warning(None,
                                          'Corrupt settings',
                                          ''.join([str(e),'\nRestore default settings?']),
                                          buttons=QMessageBox.Yes | QMessageBox.No)
            if warning == QMessageBox.Yes:
                GUI.write_default_settings(True)
                app = None
                continue
            else:
                break

if __name__ == '__main__':
    main()