import json
import logging

from util.exception import ALEDException
from util.Configurer import Configurer

logger = logging.getLogger("Config")

class AbcConfig:
    def __init__(self, pattern=None, file=None, strict=False):
        if pattern is None: pattern = self.__class__.PATTERN
        if file is None: file = self.__class__.FILE
        logger.info(f"Chargement de {file}")

        self._pattern = pattern
        self._file = f"_config/{file}.cfg"
        try:
            self._load_file()
        except FileNotFoundError:
            if strict:
                raise FileNotFoundError("The file doesn't exist or is not a valid json")
            else:
                conf = Configurer(pattern)
                self._config = conf.to_json()
                logging.warning("The file doesn't exist or is not a valid json, creating file with default with very default value ...")
                conf.raw_save(file=self._file)

    def _load_file(self):
        with open(self._file) as fd:
            try:
                self._config = json.load(fd)
            except json.JSONDecodeError as e:
                raise ALEDException(f"Le json {self._file} est comrompue: {e}")

    def __getitem__(self, item):
        return self._config[item]

    async def open_editor(self, channel, user, client, timeout=60):
        await Configurer.open_and_listen(self._file, self._pattern, channel, user, client, timeout=timeout)
        self._load_file()


