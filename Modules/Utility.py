import time
import functools


def timeit(func):
    """
    Decorate funstion or run with function to test time. Low accuracy. For detail, use timeit module.
    """
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        startTime = time.time()
        A = func(*args, **kwargs)
        elapsedTime = time.time() - startTime
        print('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsedTime * 1000)))
        return A

    return newfunc

def iterate(A, step=-1):
    """
    A function to nicely (well, more nice than a long line...) present data in various object types.
    """

    if step==-1:
        print('-'*20)
        print(type(A))
    else:
        print('\t'*step,type(A))
    step+=1
    #print('-'*50)
    print('-' * 20)
    if type(A) is dict:
        for key, value in A.items():
            # print(type(value))
            if type(value) is dict:
                print('\t'*step,key, '(dict):')
                iterate(value,step)
            elif type(value) is tuple:
                print('\t'*step,key, '(tuple):')
                iterate(value,step)
            elif type(value) is list:
                print('\t' * step, key, '(list):')
                iterate(value,step)
            else:
                print('\t'*(step), value)
    elif type(A) is list or tuple:
        for item in A:
            iterate(item,step)
    else:
        print('\t'*(step+1),A, type(A))
    print('-' * 20)



if __name__=='__main__':
    SampleDict = {
        "Other stuff": {
            "multidl_txt": "C:/Users/THOMAS/PycharmProjects/YTDLGUI/test.txt"
        },
        "Settings": {
            "Add thumbnail": {
                "Active option": 0,
                "Command": "--embed-thumbnail",
                "dependency": "Convert to audio",
                "options": None,
                "state": True,
                "tooltip": "Include thumbnail on audio files."
            },
            "Convert to audio": {
                "Active option": 0,
                "Command": "-x --audio-format {} --audio-quality 0",
                "dependency": None,
                "options": [
                    "mp3",
                    "mp4"
                ],
                "state": True,
                "tooltip": "Convert to selected audio format."
            },
            "Download location": {
                "Active option": 2,
                "Command": "-o {}",
                "dependency": None,
                "options": [
                    "D:/Musikk/DLs/%(title)s.%(ext)s",
                    "C:/Users/THOMAS/Downloads/Convertering/%(title)s.%(ext)s",
                    "D:/Musikk/Needs review and selection/%(title)s.%(ext)s"
                ],
                "state": True,
                "tooltip": "Select download location."
            },
            "Ignore errors": {
                "Active option": 0,
                "Command": "-i",
                "dependency": None,
                "options": None,
                "state": True,
                "tooltip": "Ignores errors, and jumps to next element instead of stopping."
            },
            "Keep archive": {
                "Active option": 0,
                "Command": "--download-archive {}",
                "dependency": None,
                "options": [
                    "Archive.txt"
                ],
                "state": False,
                "tooltip": "Saves links to a textfile to avoid duplicates later."
            },
            "Strict file names": {
                "Active option": 0,
                "Command": "--restrict-filenames",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Sets strict naming, to prevent unsupported characters in names."
            }
        }
    }

    #iterate(SampleDict)