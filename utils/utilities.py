"""
Utilities for Grabber.
"""
import copy

def path_shortener(full_path: str):
    """ Formats a path to a shorter version, for cleaner UI."""

    # Convert to standard style, use / not \\
    full_path = full_path.replace('\\', '/')

    if full_path[-1] != '/':
        full_path = ''.join([full_path, '/'])

    if len(full_path) > 15:
        times = 0
        for integer, letter in enumerate(reversed(full_path)):
            if letter == '/':
                split = -integer - 1
                times += 1
                if times == 3:
                    break
        else:
            raise Exception(''.join(['Something went wrong with path shortening! Path:', full_path]))

        short_path = ''.join([full_path[0:3], '...', full_path[split:]])
    else:
        short_path = full_path

    if not short_path[-1] == '/':
        short_path += '/'

    return short_path


def color_text(text: str, color: str = 'darkorange', weight: str = 'bold', sections: tuple = None) -> str:
    """
    Formats a piece of string to be colored/bolded.
    Also supports having a section of the string colored.
    """
    text = text.replace('\n', '<br>')

    if not sections:
        string = ''.join(['<span style=\"color:', color,
                          '; font-weight:', weight,
                          """;\" >""", text,
                          "</span>"]
                         )
    else:
        work_text = text[sections[0]:sections[1]]
        string = ''.join([text[:sections[0]],
                          '<span style=\"color:', color,
                          '; font-weight:', weight,
                          """;\" >""", work_text,
                          "</span>",
                          text[sections[1]:]]
                         )
    return string


def format_in_list(command, option):
    split_command = command.split()
    for index, item in enumerate(split_command):
        if '{}' in item:
            split_command[index] = item.format(option)
            return split_command
    return split_command


class SettingsError(Exception):
    pass


class ArgumentError(Exception):
    pass


base_settings = dict()
base_settings['Profiles'] = {}
base_settings['Favorites'] = []
base_settings['Settings'] = {}
base_settings['Other stuff'] = {
    'multidl_txt': '',
    'current_profile': '',
    'select_on_focus': True,
    'show_collapse_arrows': False,
    'custom': {
        "command": "Custom",
        "state": False,
        "tooltip": "Custom option, double click to edit."
    }
}
base_settings['Settings']['Convert to audio'] = {
    "active option": 0,
    "command": "-x --audio-format {}",
    "dependency": None,
    "options": ['mp3'],
    "state": False,
    "tooltip": "Convert video files to audio-only files\n"
               "Requires ffmpeg, avconv and ffprobe or avprobe."
}
base_settings['Settings']["Add thumbnail"] = {
    "active option": 0,
    "command": "--embed-thumbnail",
    "dependency": 'Convert to audio',
    "options": None,
    "state": False,
    "tooltip": "Include thumbnail on audio files."
}
base_settings['Settings']['Audio quality'] = {
    "active option": 0,
    "command": "--audio-quality {}",
    "dependency": 'Convert to audio',
    "options": ['0', '5', '9'],
    "state": True,
    "tooltip": "Specify ffmpeg/avconv audio quality.\ninsert"
               "a value between\n0 (better) and 9 (worse)"
               "for VBR\nor a specific bitrate like 128K"
}
base_settings['Settings']['Ignore errors'] = {
    "active option": 0,
    "command": "-i",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Ignores errors, and jumps to next element instead of stopping."
}
base_settings['Settings']['Download location'] = {
    "active option": 0,
    "command": "-o {}",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Select download location."
}
base_settings['Settings']['Strict file names'] = {
    "active option": 0,
    "command": "--restrict-filenames",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Sets strict naming, to prevent unsupported characters in names."
}
base_settings['Settings']['Keep archive'] = {
    "active option": 0,
    "command": "--download-archive {}",
    "dependency": None,
    "options": ['Archive.txt'],
    "state": False,
    "tooltip": "Saves links to a textfile to avoid duplicate downloads later."
}
base_settings['Settings']['Force generic extractor'] = {
    "active option": 0,
    "command": "--force-generic-extractor",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Force extraction to use the generic extractor"
}
base_settings['Settings']['Use proxy'] = {
    "active option": 0,
    "command": "--proxy {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Use the specified HTTP/HTTPS/SOCKS proxy."
}
base_settings['Settings']['Socket timeout'] = {
    "active option": 0,
    "command": "--socket-timeout {}",
    "dependency": None,
    "options": [10, 60, 300],
    "state": False,
    "tooltip": "Time to wait before giving up, in seconds."
}
base_settings['Settings']['Source IP'] = {
    "active option": 0,
    "command": "--source-address {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Client-side IP address to bind to."
}
base_settings['Settings']['Force ipv4/6'] = {
    "active option": 0,
    "command": "--{}",
    "dependency": None,
    "options": ['force-ipv4', 'force-ipv6'],
    "state": False,
    "tooltip": "Make all connections via ipv4/6."
}
base_settings['Settings']['Geo bypass URL'] = {
    "active option": 0,
    "command": "--geo-verification-proxy {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Use this proxy to verify the IP address for some geo-restricted sites.\n"
               "The default proxy specified by"
               " --proxy (or none, if the options is not present)\nis used for the actual downloading."
}
base_settings['Settings']['Geo bypass country CODE'] = {
    "active option": 0,
    "command": "--geo-bypass-country {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Force bypass geographic restriction with explicitly provided\n"
               "two-letter ISO 3166-2 country code (experimental)."
}
base_settings['Settings']['Playlist start'] = {
    "active option": 0,
    "command": "--playlist-start {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Playlist video to start at (default is 1)."
}
base_settings['Settings']['Playlist end'] = {
    "active option": 0,
    "command": "--playlist-end {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Playlist video to end at (default is last)."
}
base_settings['Settings']['Playlist items'] = {
    "active option": 0,
    "command": "--playlist-items {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Playlist video items to download.\n"
               "Specify indices of the videos in the playlist "
               "separated by commas like:\n\"1,2,5,8\" if you want to download videos "
               "indexed 1, 2, 5, 8 in the playlist.\nYou can specify range:"
               "\"1-3,7,10-13\"\nwill download the videos at index:\n1, 2, 3, 7, 10, 11, 12 and 13."
}
base_settings['Settings']['Match titles'] = {
    "active option": 0,
    "command": "--match-title {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Download only matching titles (regex or caseless sub-string)."
}
base_settings['Settings']['Reject titles'] = {
    "active option": 0,
    "command": "--reject-title {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Skip download for matching titles (regex or caseless sub-string)."
}
base_settings['Settings']['Max downloads'] = {
    "active option": 0,
    "command": "--max-downloads {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Abort after downloading a certain number of files."
}
base_settings['Settings']['Minimum size'] = {
    "active option": 0,
    "command": "--min-filesize {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Do not download any videos smaller than SIZE (e.g. 50k or 44.6m)."
}
base_settings['Settings']['Maximum size'] = {
    "active option": 0,
    "command": "--max-filesize {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Do not download any videos bigger than SIZE (e.g. 50k or 44.6m)."
}
base_settings['Settings']['No playlist'] = {
    "active option": 0,
    "command": "--no-playlist ",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Download only the video, if the URL refers to a video and a playlist."
}
base_settings['Settings']['Download speed limit'] = {
    "active option": 0,
    "command": "--limit-rate {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Maximum download rate in bytes per second (e.g. 50K or 4.2M)."
}
base_settings['Settings']['Retry rate'] = {
    "active option": 0,
    "command": "--retries {}",
    "dependency": None,
    "options": ['Implement later', 10, 15],
    "state": False,
    "tooltip": "Number of retries (default is 10), or \"infinite\"."
}
base_settings['Settings']['Download order'] = {
    "active option": 0,
    "command": "--playlist-{}",
    "dependency": None,
    "options": ['reverse', 'random'],
    "state": False,
    "tooltip": "Download playlist videos in reverse/random order."
}
base_settings['Settings']['Prefer native/ffmpeg'] = {
    "active option": 0,
    "command": "--hls-prefer-{}",
    "dependency": None,
    "options": ['ffmpeg', 'native'],
    "state": False,
    "tooltip": "Use the native HLS downloader instead of ffmpeg, or vice versa."
}
base_settings['Settings']['Don\'t overwrite files'] = {
    "active option": 0,
    "command": "--no-overwrites",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Do not overwrite files"
}
base_settings['Settings']['Don\'t continue files'] = {
    "active option": 0,
    "command": "--no-continue",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Do not resume partially downloaded files."
}
base_settings['Settings']['Don\'t use .part files'] = {
    "active option": 0,
    "command": "--no-part",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Do not use .part files - write directly into output file."
}
base_settings['Settings']['Verbose'] = {
    "active option": 0,
    "command": "--verbose",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Print various debugging information."
}
base_settings['Settings']['Custom user agent'] = {
    "active option": 0,
    "command": "--user-agent {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Specify a custom user agent."
}
base_settings['Settings']['Custom referer'] = {
    "active option": 0,
    "command": "--referer {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Specify a custom referer, use if the video access is restricted to one domain."
}
base_settings['Settings']['Min sleep interval'] = {
    "active option": 0,
    "command": "--sleep-interval {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Number of seconds to sleep before each download;\nwhen used "
               "alone or a lower bound of a range for randomized sleep before each\n"
               "download when used along with max sleep interval."
}
base_settings['Settings']['Max sleep interval'] = {
    "active option": 0,
    "command": "--max-sleep-interval {}",
    "dependency": "Min sleep interval",
    "options": [],
    "state": False,
    "tooltip": "Upper bound of a range for randomized sleep before each download\n"
               "(maximum possible number of seconds to sleep).\n"
               "Must only be used along with --min-sleep-interval."
}
base_settings['Settings']['Video format'] = {
    "active option": 0,
    "command": "--format {}",
    "dependency": None,
    "options": ["Implement later"],
    "state": False,
    "tooltip": "Video format code."
}
base_settings['Settings']['Write subtitle file'] = {
    "active option": 0,
    "command": "--write-sub",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Write subtitle file."
}
base_settings['Settings']['Recode video'] = {
    "active option": 0,
    "command": "--recode-video {}",
    "dependency": None,
    "options": ['mp4', 'flv', 'ogg', 'webm', 'mkv', 'avi'],
    "state": False,
    "tooltip": "Encode the video to another format if necessary.\n"
               "Currently supported: mp4|flv|ogg|webm|mkv|avi."
}
base_settings['Settings']['No post overwrite'] = {
    "active option": 0,
    "command": "--no-post-overwrites",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Do not overwrite post-processed files;\n"
               "the post-processed files are overwritten by default."
}
base_settings['Settings']['Embed subs'] = {
    "active option": 0,
    "command": "--embed-subs",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Embed subtitles in the video (only for mp4, webm and mkv videos)"
}
base_settings['Settings']['Add metadata'] = {
    "active option": 0,
    "command": "--add-metadata",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Write metadata to the video file."
}
base_settings['Settings']['Metadata from title'] = {
    "active option": 0,
    "command": "--metadata-from-title {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Parse additional metadata like song title /"
               "artist from the video title.\nThe format"
               "syntax is the same as --output.\nRegular "
               "expression with named capture groups may"
               "also be used.\nThe parsed parameters replace "
               "existing values.\n\n"
               "Example:\n\"%(artist)s - %(title)s\" matches a"
               "title like \"Coldplay - Paradise\".\nExample"
               "(regex):\n\"(?P<artist>.+?) - (?P<title>.+)\""
}


def get_base_settings() -> dict:
    settings = copy.deepcopy(base_settings)
    return settings


def get_base_setting(section, setting):
    return copy.deepcopy(base_settings[section][setting])


if __name__ == '__main__':
    print(color_text('rests valued', sections=(2, 5)))
