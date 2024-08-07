# Grabber
A wrapper for Youtube-dl for Windows. 

![Main](https://i.imgur.com/Tdd2oHt.png)

**Requires you to have youtube-dl.exe in the same folder as this program(Grabber), or in PATH. 
If you want to convert the videos, or otherwise use features of youtube-dl that require ffmpeg,
that also has to be in the same folder (or path) as Grabber.** 

#### Installation guide

1. Download Grabber.exe and place in a folder.
2. Download youtube-dl.exe and *either* place it in the same folder as above, or in PATH, if you know how. 
3. If you want to convert to audio, you need to also put ffmpeg.exe and the other included executables that follow into the same folder as Grabber.exe or in PATH.
4. If nothing happens when you try to start a download, youtube-dl likely fails because you **need** this installed:
 https://www.microsoft.com/en-US/download/details.aspx?id=5555

Youtube-dl download: 
https://ytdl-org.github.io/youtube-dl/download.html


If you don't put anything in path, this is what your folder should have:
- Grabber.exe
- ffmpeg.exe
- ffprobe.exe
- ffplay.exe (is included in ffmpeg bin folder, but not actually needed)
- youtube-dl.exe (if you use youtube-dlp, just renamed it to youtube-dl and it will work)

**Remember, if nothing happens when you try a download, to install "Microsoft Visual C++ 2010 Redistributable Package (x86)" from the microsoft link above!** This is required by youtube-dl to run.

______

### Features

The core of Grabber is to let you use Youtube-dl more easily on a regular basis. It has easy checkboxes for adding the parameters you'd normally use. 

Some core highlights:
* Serial downloads, or parallel downloads (up to 4, currently hard coded to that, make an issue if u want it changed to more!)
* You can queue up as many downlaods as you need, regardless of serial download or parallel mode. The first ones in are the first ones to be started. 
* Automatically highlight the URL text when the window get's focus or when you click the url box. 
 
  This means you copy any URL, alt-tab(go to Grabber), Paste the ULR (Ctrl+V), and press Enter. No clicking with the mouse needed!
* Built in super simple textfile editor, and the option to let youtube-dl use the textfile for downloading url.
* Profiles, so when you want to change something around, it's not too many clicks away! 
* Favorite parameters, so they are up and front, to easier tweak often used parameters. 
* Right-click to add or remove options to a parameter, or a favorite the parameter.
* Right click the folder path at the top of the param tab to go to the folder.
* Pro-tip: Many sites change often, and causes youtube-dl to break, so update often using the Update button in the About tab. 
 
______

Requirements to use source code:

* Python 3.6+ 
* PyQt5 5.9 (Earlier version might work too, worked fine with 5.8 before i upgraded.) 

Made with PyQt5 https://www.riverbankcomputing.com/software/pyqt/intro


![param](https://i.imgur.com/4jFwhFe.png) ![About](https://i.imgur.com/52Fy75J.png) 
![Option](https://i.imgur.com/ceYwgyS.png) ![List](https://i.imgur.com/L0PL5OH.png)


Current updates, if desired, that I could implement:
* Custom UI colors


