# Grabber
A wrapper for Youtube-dl for Windows. 

![Main](https://i.imgur.com/ArcscSv.png) ![param](https://i.imgur.com/FHcXryA.png) ![List](https://i.imgur.com/hTRe9f7.png) ![About](https://i.imgur.com/bTuJHDr.png)

Requires you to have youtube-dl.exe in the same folder as this program(Grabber), or in PATH. 
If you want to convert the videos, or otherwise use features of youtube-dl that require ffmpeg,
that also has to be in the same folder as Grabber. 

You can get those programs here:
* Youtube-dl here: https://rg3.github.io/youtube-dl/
* ffmpeg here: https://www.ffmpeg.org/

Requirements to use source:

* Python 3.6+ 
* PyQt5 5.9 (Earlier version might work too, worked fine with 5.8 before i upgraded.) 

Made with PyQt5 https://www.riverbankcomputing.com/software/pyqt/intro


Current to do list: 

* Make code consistent in style.
* Add lots of comments, strings an other stuff to ensure code readability and actually make it possible form someone else to understand the code.
* Rename really badly made functions. 
* Add a bit of explanation to naming conventions and other guidelines that should be followed.
* Docstrings to modules.
* Replace code that has been given simplifications. 
* Remove or specify try/except statements where they are too broad.
* Add general error handling when stuff goes wrong, especially read/write errors if there are some. 
* ~~Upload first release executable. (Built with PyInstaller)~~
* Learn to do testing...

