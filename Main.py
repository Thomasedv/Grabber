import sys
import json
from Core import GUI, SettingsError, QMessageBox
from PyQt5.QtWidgets import QApplication


def main():
    EXIT_CODE = GUI.EXIT_CODE_REBOOT

    while EXIT_CODE == -123456789:
        try:
            app = QApplication(sys.argv)
            qProcess = GUI()

            EXIT_CODE = app.exec_()
            app= None
        except (SettingsError,json.decoder.JSONDecodeError) as e :
            A = QMessageBox.warning(None, 'Corrupt settings', ''.join([str(e),'\nRestore default settings?']), buttons=QMessageBox.Yes | QMessageBox.No)
            if A == QMessageBox.Yes:
                GUI.write_default_settings(True)
                EXIT_CODE = -123456789
            app = None

if __name__ == '__main__':
    main()