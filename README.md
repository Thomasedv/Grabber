# Grabber
A wrapper for Youtube-dl for Windows. 

![Main](https://i.imgur.com/45yhvmH.png)

**Requires you to have youtube-dl.exe in the same folder as this program(Grabber), or in PATH. 
If you want to convert the videos, or otherwise use features of youtube-dl that require ffmpeg,
that also has to be in the same folder as Grabber.** 

You can get those programs here:
* Youtube-dl: https://rg3.github.io/youtube-dl/
* ffmpeg: https://www.ffmpeg.org/

Requirements to use source:

* Python 3.6+ 
* PyQt5 5.9 (Earlier version might work too, worked fine with 5.8 before i upgraded.) 

Made with PyQt5 https://www.riverbankcomputing.com/software/pyqt/intro


![param](https://i.imgur.com/4jFwhFe.png) ![About](https://i.imgur.com/52Fy75J.png) 
![Option](https://i.imgur.com/ceYwgyS.png) ![List](https://i.imgur.com/L0PL5OH.png)
Images from version 0.3.1.

Current to do list: 

* Make code consistent in style. (Mostly completed...)
* Add lots of comments, strings an other stuff to ensure code readability and actually make it possible form someone else to understand the code.
* Rename really badly made functions. (Mostly done)
* Docstrings to modules.
* Replace code that has been given simplifications. 
* Remove or specify try/except statements where they are too broad.
* Add general error handling when stuff goes wrong, especially read/write errors if there are some. 
* ~~Upload first release executable. (Built with PyInstaller)~~ Done!
* Learn to do testing...
* Add hide fram taskbar. (So only a icon in bottom right corner, potentially pop-up when done downloading.) 
* Add custom profiles. 
