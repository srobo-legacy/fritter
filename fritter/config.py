
try:
    # python 2
    import ConfigParser as configparser
except ImportError:
    # python 3
    import configparser

from os.path import join

def load_config(base_dir):
    """Loads a config set from the given folder. Will load a 'config.ini'
    first, and then look for an optional 'local.ini' to override any values
    from the defaults.

    Parameters
    ----------
    base_dir : str
        The directory to look for the config files in.
    """

    config = configparser.SafeConfigParser()
    config.readfp(open(join(base_dir, 'config.ini')))
    config.read([join(base_dir, 'local.ini')])

    return config
