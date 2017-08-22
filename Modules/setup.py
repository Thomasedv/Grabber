import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ['sys'], 'include_files':['Modules/','GUI/']}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"


setup(name="Youtube-dl GUI",
      version="1.5",
      description="Youtube-dl wrapper",
      options={"build_exe": build_exe_options},
      executables=[Executable("Main.py", base=base, icon='GUI/YTDLGUI.ico')])
