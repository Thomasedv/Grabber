"""
Utilities for Grabber.
"""


def path_shortener(full_path: str):
    """ Formats a path to a shorter version, for cleaner UI."""

    full_path = full_path.replace('%(title)s.%(ext)s', '')
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


if __name__ == '__main__':
    print(color_text('rests valued', sections=(2, 5)))
