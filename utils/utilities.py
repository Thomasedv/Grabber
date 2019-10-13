"""
Utilities for Grabber.
"""
import copy
import re
import sys
from traceback import format_exception
from winreg import ConnectRegistry, OpenKey, QueryValueEx, HKEY_CURRENT_USER

from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QApplication, QMessageBox

FONT_CONSOLAS = QFont()
FONT_CONSOLAS.setFamily('Consolas')
FONT_CONSOLAS.setPixelSize(13)


def except_hook(cls, exception, traceback):
    if getattr(sys, 'frozen', False):
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        QMessageBox.warning(None,
                            'ERROR!',
                            'An critical error happened running the program. Please forward this error to developer:\n\n'
                            f'{"".join(format_exception(cls, exception, traceback))}', QMessageBox.Ok)
        QApplication.exit(1)
    else:
        sys.__excepthook__(cls, exception, traceback)


# If not frozen as .exe, crashes show here
sys.excepthook = except_hook


def path_shortener(full_path: str):
    """ Formats a path to a shorter version, for cleaner UI."""

    # Convert to standard style, use / not \\
    full_path = full_path.replace('\\', '/')

    if full_path[-1] != '/':
        full_path = full_path + '/'

    if len(full_path) > 20:
        times = 0
        for integer, letter in enumerate(reversed(full_path)):
            if letter == '/':
                split = -integer - 1
                times += 1
                if times == 3 and full_path.count('/') >= 4:
                    short_path = ''.join([full_path[:full_path.find('/')+1], '...', full_path[split:]])
                    # print(short_path)
                    break
                elif times == 3:
                    split = full_path.find('/', split)
                    short_path = ''.join([full_path[:full_path.find('/')+1], '...', full_path[split:]])
                    break
        else:
            short_path = full_path
    else:
        short_path = full_path

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
    com = re.compile(r'{.+\}')
    split_command = command.split()
    for index, item in enumerate(split_command):
        if '{}' in item and com.search(item) is None:
            split_command[index] = item.format(option)
            return split_command
    return split_command


def get_win_accent_color():
    """
    Return the Windows 10 accent color used by the user in a HEX format
    """
    # Open the registry
    registry = ConnectRegistry(None, HKEY_CURRENT_USER)
    key = OpenKey(registry, r'Software\Microsoft\Windows\DWM')
    key_value = QueryValueEx(key, 'AccentColor')
    accent_int = key_value[0]
    accent_hex = hex(accent_int)  # Remove FF offset and convert to HEX again
    accent_hex = str(accent_hex)[4:]  # Remove prefix and suffix

    accent = accent_hex[4:6] + accent_hex[2:4] + accent_hex[0:2]

    return '#' + accent


class SettingsError(Exception):
    pass


class ProfileLoadError(Exception):
    pass


class SettingsClass:
    def __init__(self, settings, profiles, filehandler=None):
        if not settings:
            raise SettingsError('Empty settings file!')

        if any((i in settings for i in ('Profiles', 'Other stuff', 'Settings'))):
            settings, old_profiles = self._upgrade_settings(settings)
            # Check for older settings files.
            if not profiles:
                profiles = old_profiles
            else:
                old_profiles.update(profiles)
                profiles = copy.deepcopy(old_profiles)
        try:
            self._userdefined = settings['default']
            self._parameters = settings['parameters']
        except KeyError as e:
            raise SettingsError(f'Missing section {e}')

        self._profiles = profiles
        self._filehandler = filehandler

        self.need_parameters = []

        self._validate_settings()

        # print(self._profiles)
        # print(self.get_settings_data)

    def __enter__(self):
        return self._parameters

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._filehandler is not None:
            self._filehandler.save_settings(self.get_settings_data)

    def __getitem__(self, item):
        return self._parameters[item]

    @property
    def user_options(self):
        return self._userdefined

    def get_favorites(self):
        return self._userdefined['favorites']

    def is_activate(self, parameter):
        return self._parameters[parameter]['state']

    def get_active_setting(self, parameter):
        param = self._parameters[parameter]
        if '{}' in param['command']:
            active = param['active option']
            return param['options'][active]

    @property
    def parameters(self) -> dict:
        return self._parameters

    @property
    def get_settings_data(self):
        return {'default': self._userdefined, 'parameters': self._parameters}

    @property
    def current_profile(self):
        return self._userdefined['current_profile']

    @property
    def profiles(self):
        return list(self._profiles.keys())

    @property
    def get_profiles_data(self):
        return self._profiles

    def create_profile(self, profile):
        self._profiles[profile] = copy.deepcopy(self._parameters)
        self._userdefined['current_profile'] = profile

    def delete_profile(self, profile):
        del self._profiles[profile]
        self._userdefined['current_profile'] = ''

    def remove_parameter_option(self, parameter, index):
        del self._parameters[parameter]['options'][index]
        option = self._parameters[parameter]['active option']
        option -= 1 if option > 0 else 0
        self._parameters[parameter]['active option'] = option
        if not option:
            self.need_parameters.append(parameter)
        # TODO: Remove options from profiles too. At least download options. Except when it's the selected option!!!

    def add_parameter_option(self, parameter, option):
        self._parameters[parameter]['options'].insert(0, option)

    def change_profile(self, profile):
        if self.current_profile == profile:
            return True

        if profile not in self._profiles:
            return False

        for param, data in self._profiles[profile].items():
            if param not in self._parameters:
                self._parameters[param] = data
                continue

            if '{}' in data['command'] and self._parameters[param]['options'] != data['options']:
                self._parameters[param]['options'] = data['options'] + \
                                                     [i for i in self._parameters[param]['options'] if
                                                      i not in data['options']]
                new_data = {k: v for k, v in data.items() if k != 'options'}
                self._parameters[param].update(new_data)
            else:
                self._parameters[param].update(data)

        self._userdefined['current_profile'] = profile
        return True

    @staticmethod
    def _upgrade_settings(old_settings):
        # print('Upgrading settings!!')
        settings = {}
        try:
            settings['default'] = copy.deepcopy(old_settings['Other stuff'])
            if old_settings['Favorites']:
                settings['default']['favorites'] = copy.deepcopy(old_settings['Favorites'])
            settings['parameters'] = copy.deepcopy(old_settings['Settings'])
        except KeyError:
            pass

        try:
            profiles = copy.deepcopy(old_settings['Profiles'])
        except KeyError:
            profiles = {}

        return settings, profiles

    def _validate_settings(self):
        # User defined part
        global base_settings
        missing_settings = {}

        # TODO: Validated that each settings is a dict before checking for keys.

        keys = base_settings['default'].keys()
        for key in keys:
            if key not in self._userdefined:
                self._userdefined[key] = get_base_setting('default', key)

        keys = base_settings['parameters']
        for profile in self.profiles:
            for key in keys:
                if key not in self._profiles[profile]:
                    self._profiles[profile][key] = get_base_setting('parameters', key)

        # Parameters

        keys = ['command',
                'dependency',
                'options',
                'state',
                'tooltip']

        for setting in {i for i in base_settings['parameters'] if i not in self._parameters}:
            self._parameters[setting] = copy.deepcopy(base_settings['parameters'][setting])

        for setting, option in self._parameters.items():
            # setting: The name of the setting, like "Ignore errors"
            # option: The dict which contains the base keys.
            # key (Define below): is a key in the base settings

            for key in keys:
                # Check if all base keys are in the options.

                if key not in option.keys():
                    # Check if the current setting has already logged a missing key
                    # If it hasn't, create an entry in the missing_settings dict, as a list.
                    # If it's there, then add the key to the missing list.

                    if setting not in missing_settings.keys():
                        missing_settings[setting] = [key]
                    else:
                        missing_settings[setting].append(key)

                # Check if the current setting is missing options for the command, when needed.
                # Disable the setting by default. Possibly alert the user.
                elif key == 'command':
                    if '{}' in option[key]:
                        if not option['options']:
                            # print(f'{setting} currently lacks any valid options!')
                            if 'state' in option.keys() and setting != 'Download location':
                                self._parameters[setting]['state'] = False
                                # Add to a list over options to add setting to.
                                self.need_parameters.append(setting)

        if missing_settings:
            raise SettingsError('\n'.join(['Settings file is corrupt/missing:',
                                           '-' * 20,
                                           *[f'{key}:\n - {", ".join(value)}' if value
                                             else f"{key}" for key, value in missing_settings.items()],
                                           '-' * 20]))

        if not self._parameters['Download location']['options']:
            # Checks for a download setting, set the current path to that.
            path = self._filehandler.work_dir + '/DL/'
            self._parameters['Download location']['options'] = [path]

        try:
            # Checks if the active option is valid, if not reset to the first item.
            for setting in self._parameters:
                options = self._parameters[setting]['options']
                if options is not None:
                    # Check if active option is a valid number.
                    if not (0 <= self._parameters[setting]['active option'] < len(options)):
                        self._parameters[setting]['active option'] = 0
        # Catch if the setting is missing for needed options.
        except KeyError as error:
            raise SettingsError(f'{setting} is missing a needed option {error}.')
        # Catches multiple type errors.
        except TypeError as error:
            raise SettingsError(f'An unexpected type was encountered for setting:\n - {setting}\n -- {error}')

        self._filehandler.save_profiles(self.get_profiles_data)
        self._filehandler.save_settings(self.get_settings_data)


stylesheet = """
                                QWidget {{
                                    background-color: {background_light};
                                    color: {text_normal};
                                }}
                                QMainWindow {{
                                    background-color: {background_dark};
                                    color: red;
                                }}
                                
                                QMenu::separator {{
                                    height: 2px;
                                }}
                                QFrame#line {{
                                    color: {background_dark};
                                }}
                                QLabel {{
                                    background: #484848;
                                    padding: 2px;
                                    border-radius: 2px;
                                    outline: 0;    
                                }}

                                QTabWidget::pane {{
                                    border: none;
                                }}

                                QMenu::item {{
                                    border: none;
                                    padding: 3px 20px 3px 5px
                                }}

                                QMenu {{
                                    border: 1px solid {background_dark};
                                }}

                                QMenu::item:selected {{
                                    background-color: {background_dark};
                                }}

                                QMenu::item:disabled {{
                                    color: #808080;
                                }}

                                QTabWidget {{
                                    background-color: {background_dark};
                                }}

                                QTabBar {{
                                    color: {background_dark};
                                    background: {background_dark};
                                }}

                                QTabBar::tab {{
                                    color: {text_shaded};
                                    background-color: {background_lightest};
                                    border-bottom: none;
                                    border-left: 1px solid #00000000;
                                    min-width: 15ex;
                                    min-height: 7ex;
                                }}

                                QTabBar::tab:selected {{
                                    color: white;
                                    background-color: {background_light};
                                }}
                                QTabBar::tab:!selected {{
                                    margin-top: 6px;
                                    background-color: {background_lightest}
                                }}

                                QTabWidget::tab-bar {{
                                    border-top: 1px solid {background_dark};
                                }}

                                QLineEdit {{
                                    background-color: {background_dark};
                                    color: {text_shaded};
                                    border-radius: 0px;
                                    padding: 0 3px;
                                }}
                                
                                QLineEdit:disabled {{
                                    background-color: {background_dark};
                                    color: #505050;
                                    border-radius: none;
                                }}
                                
                                QTextEdit {{
                                    background-color: {background_light};
                                    color: {text_shaded};
                                    border: red solid 1px;
                                }}

                                QTextEdit#TextFileEdit {{
                                    background-color: {background_dark};
                                    color: {text_shaded};
                                    border: red solid 1px;
                                    border-radius: 2px;
                                }}
                                    
                                QListWidget {{
                                    outline: none;
                                    outline-width: 0px;
                                    background: {background_dark};
                                    border-radius: 2px;
                                }}
                                
                                QScrollBar::vertical {{
                                    border: none;
                                    background-color: rgba(255,255,255,0);
                                    width: 10px;
                                    margin: 0px 0px 1px 0px;
                                }}

                                QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
                                    border: none;
                                    background: none;
                                }}

                                QScrollBar::handle:vertical {{
                                    background: {background_dark};
                                    color: red;
                                    min-height: 20px;
                                    border-radius: 5px;
                                }}

                                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical  {{
                                    background: none;
                                }}

                                QPushButton {{
                                    background-color: {background_dark};
                                    color: white;
                                    border: 1px solid transparent;
                                    border-radius: none;
                                    width: 60px;
                                    height: 20px;
                                }}

                                QPushButton:disabled {{
                                    border: 1px solid {background_dark};
                                    background-color: transparent;
                                    color: #757575;
                                }}
                                
                                QPushButton:pressed {{
                                    background-color: #101010;
                                    color: white;
                                }}
                                
                                QTreeWidget {{
                                    selection-color: red;
                                    border: none;
                                    outline: none;
                                    outline-width: 0px;
                                    selection-background-color: blue;
                                }}      
                                
                                QTreeWidget::item {{
                                    height: 16px;
                                }}

                                QTreeWidget::item:disabled {{
                                    color: grey;
                                }}

                                QTreeWidget::item:hover, QTreeWidget::item:selected {{
                                    background-color: transparent;
                                    color: white;
                                }}

                                QComboBox {{
                                    border: 1px solid {background_dark};
                                    border-radius: 0px;
                                    background-color: {background_dark};
                                    color: {text_shaded};
                                    padding-right: 5px;
                                    padding-left: 5px;
                                }}
                                

                                QComboBox::drop-down {{
                                    border: 0px;
                                    background: none;
                                }}                        
                                
                                QComboBox::disabled {{
                                    color: {background_light};
                                }}
                                
                                """

base_settings = dict()
base_settings['profiles'] = {}
base_settings['parameters'] = {}
base_settings['default'] = {
    'multidl_txt': '',
    "parallel": False,
    'current_profile': '',
    'select_on_focus': True,
    'favorites': [],
    'show_collapse_arrows': False,
    'use_win_accent': False,
    'custom': {
        "command": "Custom",
        "state": False,
        "tooltip": "Custom option, double click to edit."
    }
}
base_settings['parameters']['Convert to audio'] = {
    "active option": 0,
    "command": "-x --audio-format {}",
    "dependency": None,
    "options": ['mp3'],
    "state": False,
    "tooltip": "Convert video files to audio-only files\n"
               "Requires ffmpeg, avconv and ffprobe or avprobe."
}
base_settings['parameters']["Add thumbnail"] = {
    "active option": 0,
    "command": "--embed-thumbnail",
    "dependency": 'Convert to audio',
    "options": None,
    "state": False,
    "tooltip": "Include thumbnail on audio files."
}
base_settings['parameters']['Audio quality'] = {
    "active option": 0,
    "command": "--audio-quality {}",
    "dependency": 'Convert to audio',
    "options": ['0', '5', '9'],
    "state": True,
    "tooltip": "Specify ffmpeg/avconv audio quality.\ninsert"
               "a value between\n0 (better) and 9 (worse)"
               "for VBR\nor a specific bitrate like 128K"
}
base_settings['parameters']['Ignore errors'] = {
    "active option": 0,
    "command": "-i",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Ignores errors, and jumps to next element instead of stopping."
}
base_settings['parameters']['Download location'] = {
    "active option": 0,
    "command": "-o {}",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Select download location."
}
base_settings['parameters']['Strict file names'] = {
    "active option": 0,
    "command": "--restrict-filenames",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Sets strict naming, to prevent unsupported characters in names."
}
base_settings['parameters']['Keep archive'] = {
    "active option": 0,
    "command": "--download-archive {}",
    "dependency": None,
    "options": ['Archive.txt'],
    "state": False,
    "tooltip": "Saves links to a textfile to avoid duplicate downloads later."
}
base_settings['parameters']['Force generic extractor'] = {
    "active option": 0,
    "command": "--force-generic-extractor",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Force extraction to use the generic extractor"
}
base_settings['parameters']['Use proxy'] = {
    "active option": 0,
    "command": "--proxy {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Use the specified HTTP/HTTPS/SOCKS proxy."
}
base_settings['parameters']['Socket timeout'] = {
    "active option": 0,
    "command": "--socket-timeout {}",
    "dependency": None,
    "options": [10, 60, 300],
    "state": False,
    "tooltip": "Time to wait before giving up, in seconds."
}
base_settings['parameters']['Source IP'] = {
    "active option": 0,
    "command": "--source-address {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Client-side IP address to bind to."
}
base_settings['parameters']['Force ipv4/6'] = {
    "active option": 0,
    "command": "--{}",
    "dependency": None,
    "options": ['force-ipv4', 'force-ipv6'],
    "state": False,
    "tooltip": "Make all connections via ipv4/6."
}
base_settings['parameters']['Geo bypass URL'] = {
    "active option": 0,
    "command": "--geo-verification-proxy {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Use this proxy to verify the IP address for some geo-restricted sites.\n"
               "The default proxy specified by"
               " --proxy (or none, if the options is not present)\nis used for the actual downloading."
}
base_settings['parameters']['Geo bypass country CODE'] = {
    "active option": 0,
    "command": "--geo-bypass-country {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Force bypass geographic restriction with explicitly provided\n"
               "two-letter ISO 3166-2 country code (experimental)."
}
base_settings['parameters']['Playlist start'] = {
    "active option": 0,
    "command": "--playlist-start {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Playlist video to start at (default is 1)."
}
base_settings['parameters']['Playlist end'] = {
    "active option": 0,
    "command": "--playlist-end {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Playlist video to end at (default is last)."
}
base_settings['parameters']['Playlist items'] = {
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
base_settings['parameters']['Match titles'] = {
    "active option": 0,
    "command": "--match-title {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Download only matching titles (regex or caseless sub-string)."
}
base_settings['parameters']['Reject titles'] = {
    "active option": 0,
    "command": "--reject-title {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Skip download for matching titles (regex or caseless sub-string)."
}
base_settings['parameters']['Max downloads'] = {
    "active option": 0,
    "command": "--max-downloads {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Abort after downloading a certain number of files."
}
base_settings['parameters']['Minimum size'] = {
    "active option": 0,
    "command": "--min-filesize {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Do not download any videos smaller than SIZE (e.g. 50k or 44.6m)."
}
base_settings['parameters']['Maximum size'] = {
    "active option": 0,
    "command": "--max-filesize {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Do not download any videos bigger than SIZE (e.g. 50k or 44.6m)."
}
base_settings['parameters']['No playlist'] = {
    "active option": 0,
    "command": "--no-playlist ",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Download only the video, if the URL refers to a video and a playlist."
}
base_settings['parameters']['Download speed limit'] = {
    "active option": 0,
    "command": "--limit-rate {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Maximum download rate in bytes per second (e.g. 50K or 4.2M)."
}
base_settings['parameters']['Retry rate'] = {
    "active option": 0,
    "command": "--retries {}",
    "dependency": None,
    "options": [10, 15],
    "state": False,
    "tooltip": "Number of retries (default is 10), or \"infinite\"."
}
base_settings['parameters']['Download order'] = {
    "active option": 0,
    "command": "--playlist-{}",
    "dependency": None,
    "options": ['reverse', 'random'],
    "state": False,
    "tooltip": "Download playlist videos in reverse/random order."
}
base_settings['parameters']['Prefer native/ffmpeg'] = {
    "active option": 0,
    "command": "--hls-prefer-{}",
    "dependency": None,
    "options": ['ffmpeg', 'native'],
    "state": False,
    "tooltip": "Use the native HLS downloader instead of ffmpeg, or vice versa."
}
base_settings['parameters']['Don\'t overwrite files'] = {
    "active option": 0,
    "command": "--no-overwrites",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Do not overwrite files"
}
base_settings['parameters']['Don\'t continue files'] = {
    "active option": 0,
    "command": "--no-continue",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Do not resume partially downloaded files."
}
base_settings['parameters']['Don\'t use .part files'] = {
    "active option": 0,
    "command": "--no-part",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Do not use .part files - write directly into output file."
}
base_settings['parameters']['Verbose'] = {
    "active option": 0,
    "command": "--verbose",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Print various debugging information."
}
base_settings['parameters']['Custom user agent'] = {
    "active option": 0,
    "command": "--user-agent {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Specify a custom user agent."
}
base_settings['parameters']['Custom referer'] = {
    "active option": 0,
    "command": "--referer {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Specify a custom referer, use if the video access is restricted to one domain."
}
base_settings['parameters']['Min sleep interval'] = {
    "active option": 0,
    "command": "--sleep-interval {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Number of seconds to sleep before each download;\nwhen used "
               "alone or a lower bound of a range for randomized sleep before each\n"
               "download when used along with max sleep interval."
}
base_settings['parameters']['Max sleep interval'] = {
    "active option": 0,
    "command": "--max-sleep-interval {}",
    "dependency": "Min sleep interval",
    "options": [],
    "state": False,
    "tooltip": "Upper bound of a range for randomized sleep before each download\n"
               "(maximum possible number of seconds to sleep).\n"
               "Must only be used along with --min-sleep-interval."
}
base_settings['parameters']['Video format'] = {
    "active option": 0,
    "command": "--format {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Video format code."
}
base_settings['parameters']['Write subtitle file'] = {
    "active option": 0,
    "command": "--write-sub",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Write subtitle file."
}
base_settings['parameters']['Recode video'] = {
    "active option": 0,
    "command": "--recode-video {}",
    "dependency": None,
    "options": ['mp4', 'flv', 'ogg', 'webm', 'mkv', 'avi'],
    "state": False,
    "tooltip": "Encode the video to another format if necessary.\n"
               "Currently supported: mp4|flv|ogg|webm|mkv|avi."
}
base_settings['parameters']['No post overwrite'] = {
    "active option": 0,
    "command": "--no-post-overwrites",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Do not overwrite post-processed files;\n"
               "the post-processed files are overwritten by default."
}
base_settings['parameters']['Embed subs'] = {
    "active option": 0,
    "command": "--embed-subs",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Embed subtitles in the video (only for mp4, webm and mkv videos)"
}
base_settings['parameters']['Add metadata'] = {
    "active option": 0,
    "command": "--add-metadata",
    "dependency": None,
    "options": None,
    "state": False,
    "tooltip": "Write metadata to the video file."
}
base_settings['parameters']['Metadata from title'] = {
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
base_settings['parameters']['Merge output format'] = {
    "active option": 0,
    "command": "--merge-output-format {}",
    "dependency": None,
    "options": ["mp4", "mkv", "ogg", "webm", "flv"],
    "state": False,
    "tooltip": "If a merge is required (e.g. bestvideo+bestaudio),"
               "\noutput to given container format."
               "\nOne of mkv, mp4, ogg, webm, flv."
               "\nIgnored if no merge is required"
}
base_settings['parameters']['Username'] = {
    "active option": 0,
    "command": "--username {}",
    "dependency": None,
    "options": [],
    "state": False,
    "tooltip": "Username of your account. Password will be asked for on run."
}


def get_base_settings() -> dict:
    settings = copy.deepcopy(base_settings)
    return settings


def get_base_setting(section, setting):
    return copy.deepcopy(base_settings[section][setting])


def darken(color: QColor):
    return color.darker(150)


def lighten(color: QColor):
    return color.lighter(150)


surface = QColor('#484848')
text = QColor('white')

default_style = {'background_light': surface,
                 'background_dark': darken(surface),
                 'background_lightest': lighten(surface),
                 'text_shaded': darken(text),
                 'text_normal': text}


def qcolorToStr(color_map: dict):
    return {k: v.name(QColor.HexRgb) for k, v in color_map.items()}


def get_stylesheet(**kwargs):
    global default_style
    styles = default_style.copy()
    styles.update(kwargs)
    return stylesheet.format(**qcolorToStr(styles))


if __name__ == '__main__':
    pass

# print(color_text('rests valued', sections=(2, 5)))
# Testing of settings class:
# import json
# with open('..\\settings.json') as f:
#     profile = json.load(f)
# s = SettingsClass(base_settings, profile['Profiles'])
# s.change_profile('Music')
# s.change_profile('Music')
# s.change_profile('Video')
