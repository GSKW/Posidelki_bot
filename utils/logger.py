from colorlog import ColoredFormatter
import logging


class CustomLogger(logging.Logger):
    def banner(self, msg):
        purple = '\033[95m'
        reset = '\033[0m'
        handler = self.handlers[0]
        handler.setFormatter(logging.Formatter(f"{purple}%(message)s{reset}"))
        self.info(msg)
        # Возвращаем стандартный формат
        handler.setFormatter(
            ColoredFormatter(
                "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
            )
        )


def setup_logger(name='Pos1delk1B0t'):
    logger = CustomLogger(name)

    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger