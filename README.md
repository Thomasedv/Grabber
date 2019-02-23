# Grabber
A wrapper for Youtube-dl for Windows. 

![Main](https://i.imgur.com/fKopNX6.png)

**Requires you to have youtube-dl.exe in the same folder as this program(Grabber), or in PATH. 
If you want to convert the videos, or otherwise use features of youtube-dl that require ffmpeg,
that also has to be in the same folder (or path) as Grabber.** 

You can get those programs here:
* Youtube-dl: https://rg3.github.io/youtube-dl/ 
* ffmpeg: https://ffmpeg.zeranoe.com/builds/  

**USE THE 4.0.2 static ffmpeg version!** Extract the 3 executables from the bin folder to the Grabber folder or PATH

______

Requirements to use source code:

* Python 3.6+ 
* PyQt5 5.9 (Earlier version might work too, worked fine with 5.8 before i upgraded.) 

Made with PyQt5 https://www.riverbankcomputing.com/software/pyqt/intro


![param](https://i.imgur.com/4jFwhFe.png) ![About](https://i.imgur.com/52Fy75J.png) 
![Option](https://i.imgur.com/ceYwgyS.png) ![List](https://i.imgur.com/L0PL5OH.png)


Images from version 0.3.1.

Current to do list: 

* Possibly in desired: Add hide from taskbar. (So only a icon in bottom right corner, potentially pop-up when done downloading.) 
* ~~Add general error handling when stuff goes wrong, especially read/write errors if there are some.~~
* ~~Upload first release executable. (Built with PyInstaller)~~ Done!
* ~~Add custom profiles. ~~
