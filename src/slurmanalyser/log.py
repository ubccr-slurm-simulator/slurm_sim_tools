import sys
import logging
from logging import INFO, DEBUG
from logging import basicConfig, critical, error, warning, info, debug, getLogger, exception

print("Logger initialization")

class Colors:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

    colors = [PURPLE, BLUE, GREEN, YELLOW, RED]

    @staticmethod
    def is_color(value):
        if value is not None and value in Colors.colors:
            return True
        return False


def colorize(text, color):
    """
    Turns the provided text the provided color. It does this by wrapping it with the provided color code before
    and an end color code after the text.

    :param text: the textual input to be colored.
    :param color: the color to be used during the colorizing process.
    :return: color + text + end color.
    """
    if text and color and Colors.is_color(color):
        return color + text + Colors.ENDC
    elif text and color is not Colors.is_color(color):
        raise AssertionError('Color must be valid')
    else:
        return text


def purple(text):
    """
    Turns the provided text 'Purple'. It does this by wrapping it with a color code before
    and an end color code after the text.

    :param text the textual input that will be colored purple.
    :return: the text but wrapped in a color code that when output to stdout will be interpreted as purple.
    """
    return colorize(text, Colors.PURPLE)


def blue(text):
    """
    Turns the provided text 'Blue'. It does this by wrapping it with a color code before
    and an end color code after the text.

    :param text the textual input that will be colored blue.
    :return: the text but wrapped in a color code that when output to stdout will be interpreted as blue.
    """
    return colorize(text, Colors.BLUE)


def green(text):
    """
    Turns the provided text 'Green'. It does this by wrapping it with a color code before
    and an end color code after the text.

    :param text the textual input that will be colored green.
    :return: the text but wrapped in a color code that when output to stdout will be interpreted as green.
    """
    return colorize(text, Colors.GREEN)


def yellow(text):
    """
    Turns the provided text 'Yellow'. It does this by wrapping it with a color code before
    and an end color code after the text.

    :param text the textual input that will be colored yellow.
    :return: the text but wrapped in a color code that when output to stdout will be interpreted as yellow.
    """
    return colorize(text, Colors.YELLOW)


def red(text):
    """
    Turns the provided text 'Red'. It does this by wrapping it with a color code before
    and an end color code after the text.

    :param text the textual input that will be colored red.
    :return: the text but wrapped in a color code that when output to stdout will be interpreted as red.
    """
    return colorize(text, Colors.RED)



verbose = False
very_verbose = False
error_count = 0
warning_count = 0

# Set colors around logging level names
logging.addLevelName(logging.DEBUG, "\033[1;37m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
logging.addLevelName(logging.INFO, "\033[1;92m%s\033[1;0m" % logging.getLevelName(logging.INFO))
logging.addLevelName(logging.WARNING, "\033[1;93m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;91m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.addLevelName(logging.CRITICAL, "\033[1;91m%s\033[1;0m" % logging.getLevelName(logging.CRITICAL))


def debug2(msg, *args, **kwargs):
    """
    more verbose logging
    """
    if getLogger().level < 10:
        debug(msg, *args, **kwargs)


def dry_run(msg, *_, **__):
    print("[DryRun] "+msg)


def empty_line():
    print()


def log_input(message: str, *args):
    if message:
        if len(args) > 0:
            formatted_message = message % args
        else:
            formatted_message = message
    else:
        formatted_message = ''

    print('[' + colorize.purple('INPUT') + '] ' + formatted_message)


def input_choice(message: str, choice=None, default=None):
    """
    Ask user for a choice/
    If arguments choice and default is not set then use yes/no with yes as default
    """
    if choice is None:
        choice = ('yes', 'no')
        if default is None:
            default = 'yes'

    if default is not None and default not in choice:
        raise ValueError("Default is not among choices")

    choice_message = "/".join(choice)
    if default is not None:
        choice_message += " or hit enter for " + default

    print('[' + colorize.purple('INPUT') + '] ' + message + " [" + choice_message + "]:")

    while True:
        user_input = input()
        user_input = user_input.strip()
        if user_input == '' and default is not None:
            return default
        if user_input in choice:
            return user_input
        else:
            warning("Unknown choice, select from following " + choice_message)


def log_traceback(m_str=None):
    import traceback
    msg = "###### Exception ######\n"
    if m_str is not None:
        msg = msg + m_str+"\n"

    msg = msg + traceback.format_exc()
    exception(msg)


def test_log():
    basicConfig(
        level=INFO,
        format="[%(asctime)s - %(levelname)s] %(message)s"
    )
    getLogger().setLevel(DEBUG)
    critical("test critical")
    error("test error")
    exception("test exception")
    warning("test warning")
    info("test info")


def set_verbose():
    global verbose
    verbose = True
    basicConfig(level=DEBUG)
    getLogger().setLevel(DEBUG)


def flush():
    import sys
    sys.stdout.flush()
    sys.stderr.flush()


basicConfig(
    level=INFO,
    stream = sys.stdout,
    format="[%(levelname)s] %(message)s"
)
#set_verbose()
