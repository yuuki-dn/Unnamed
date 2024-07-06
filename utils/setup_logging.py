import logging
from os import makedirs
from sys import stdout, stderr

from colorama import Fore, Style, init

def setup_logging() -> None:
    # Create file .logs/bot.log if not exist
    try:
        open(".logs/bot.log", "a").close()
    except FileNotFoundError:
        makedirs(".logs", exist_ok=True)
        open(".logs/bot.log", "w").close()

    # Setup logging
    init(autoreset=True)

    class SpectificLevelFilter(logging.Filter):
        ## Logging filter that allow only the spectified level to be processed
        def __init__(self, level: int):
                super().__init__()
                self.level = level

        def filter(self, record) -> bool:
                return record.levelno == self.level

    ## Format (console only)
    INFO_FORMAT = f"{Style.DIM}[%(asctime)s]{Style.RESET_ALL} [%(name)s:%(lineno)d] [✅] {Fore.GREEN}[%(levelname)s] - %(message)s{Style.RESET_ALL}"
    WARNING_FORMAT = f"{Style.DIM}[%(asctime)s]{Style.RESET_ALL} [%(name)s:%(lineno)d] [⚠️]  {Fore.YELLOW}[%(levelname)s] - %(message)s{Style.RESET_ALL}"
    ERROR_FORMAT = f"{Style.DIM}[%(asctime)s]{Style.RESET_ALL} [%(name)s:%(lineno)d] [❌] {Fore.RED}[%(levelname)s] - %(message)s{Style.RESET_ALL}"

    DATEFMT="%d-%m-%Y %H:%M:%S"

    ## Create handlers
    infoHandler = logging.StreamHandler(stream=stdout)
    infoHandler.setLevel(logging.INFO)
    infoHandler.addFilter(SpectificLevelFilter(logging.INFO))
    infoHandler.setFormatter(logging.Formatter(INFO_FORMAT, datefmt=DATEFMT))

    warningHandler = logging.StreamHandler(stream=stdout)
    warningHandler.setLevel(logging.WARNING)
    warningHandler.addFilter(SpectificLevelFilter(logging.WARNING))
    warningHandler.setFormatter(logging.Formatter(WARNING_FORMAT, datefmt=DATEFMT))

    errorHandler = logging.StreamHandler(stream=stderr)
    errorHandler.setLevel(logging.ERROR)
    errorHandler.addFilter(SpectificLevelFilter(logging.ERROR))
    errorHandler.setFormatter(logging.Formatter(ERROR_FORMAT, datefmt=DATEFMT))

    fileHandler = logging.FileHandler(".logs/bot.log", mode="a", encoding="utf-8")
    fileHandler.setLevel(logging.INFO)
    fileHandler.setFormatter(logging.Formatter("%(asctime)s %(name)s:%(lineno)d [%(levelname)s] - %(message)s", datefmt=DATEFMT))

    ## Configure
    logging.basicConfig(
        level=logging.INFO,
        handlers=[infoHandler, warningHandler, errorHandler, fileHandler]
    )