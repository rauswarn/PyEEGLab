import logging
from abc import ABC, abstractmethod

from os.path import isfile, join
from hashlib import md5
from pickle import load, dump

from ..io import DataLoader
from ..preprocessing import Pipeline

class Cache(ABC):

    def __init__(self) -> None:
        logging.debug('Create cache manager')

    def _get_cache_key(self, dataset: str, loader: DataLoader, pipeline: Pipeline) -> str:
        key = [loader, pipeline]
        key = [hash(k) for k in key]
        key = [str(k).encode() for k in key]
        key = [md5(k).hexdigest() for k in key]
        key = list(zip(['loader', 'pipeline'], key))
        key = ['_'.join(k) for k in key]
        key = dataset + '_' + '_'.join(key)
        return key

    @abstractmethod
    def load(self, dataset: str, loader: DataLoader, pipeline: Pipeline):
        pass


class SinglePickleCache(Cache):

    def __init__(self, path: str):
        super().__init__()
        logging.debug('Create single picle cache manager')
        self.path = path

    def load(self, dataset: str, loader: DataLoader, pipeline: Pipeline):
        logging.debug('Computing cache key')
        key = self._get_cache_key(dataset, loader, pipeline)
        logging.debug('Computed cache key: %s', key)
        key = key + '.pkl'
        key = join(self.path, key)
        if isfile(key):
            logging.debug('Cache file found')
            with open(key, 'rb') as file:
                try:
                    logging.debug('Loading cache file')
                    data = load(file)
                    return data
                except:
                    logging.debug('Loading cache file failed')
                    pass
        logging.debug('Cache file not found, genereting new one')
        data = loader.get_dataset()
        data = pipeline.run(data)
        with open(key, 'wb') as file:
            logging.debug('Dumping cache file')
            dump(data, file)
        return data
