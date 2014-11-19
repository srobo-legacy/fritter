
try:
    # python 2
    import ConfigParser as configparser
except ImportError:
    # python 3
    import configparser

import logging
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

    logger = logging.getLogger('fritter.config')

    config = configparser.SafeConfigParser()

    main_config = join(base_dir, 'config.ini')
    logger.info("Loading base config data from '%s'.", main_config)
    config.readfp(open(main_config))
    logger.info("Successfully loaded base config data from '%s'.", main_config)

    local_config = join(base_dir, 'local.ini')
    logger.info("Loading local config data from '%s'.", local_config)
    success = config.read([local_config])
    logger.info("Successfully read local config data from '%s'.", "', '".join(success))

    return config
