# Grabber
A wrapper for Youtube-dl for Windows. 

![Main](https://i.imgur.com/fKopNX6.png)

**Requires you to have youtube-dl.exe in the same folder as this program(Grabber), or in PATH. 
If you want to convert the videos, or otherwise use features of youtube-dl that require ffmpeg,
that also has to be in the same folder (or path) as Grabber.** 

Short installation guide:

* Download Grabber.exe and place in a folder.
* Download youtube-dl.exe and *either* place it in the same folder as above, or in PATH, if you know how. 
* If you want to convert to audio, you need to also put ffmpeg.exe and the other included executables that follow into the same folder as Grabber.exe or in PATH.
* If nothing happens when you try to start a download, youtube-dl likely fails because you **need** this installed:
 https://www.microsoft.com/en-US/download/details.aspx?id=5555

Youtube-dl download: 
https://ytdl-org.github.io/youtube-dl/download.html

FFmpeg download (**STATIC build verioin**, for example 4..4 Windows 64/32, static) : 
https://ffmpeg.zeranoe.com/builds/

Open the ffmpeg zip, copy 3 executables in the **bin** folder to the locations mentioned above.

**USE THE 4.X.X static ffmpeg version!** Extract the 3 executables from the bin folder to the Grabber folder or PATH

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
