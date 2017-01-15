import logging
import logging.config
import os


def configure_logging(config):
    options = config.get('logging', {})

    # Create the default log dir, just in case
    if not os.path.exists('var/log'):
        os.makedirs('var/log', exist_ok=True)

    logging.config.dictConfig(options)
