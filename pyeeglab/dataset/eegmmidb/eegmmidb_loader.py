import logging

from os import sched_getaffinity
from os.path import isfile, join, sep
from typing import List
from multiprocessing import Pool
from ...database import File, Event
from ...io import DataLoader, RawEDF, RawFIF
from .eegmmidb_index import EEGMMIDBIndex


class EEGMMIDBLoader(DataLoader):
    def __init__(self, path: str) -> None:
        super().__init__()
        logging.debug('Create EEG Motor Movement/Imagery Loader')
        if path[-1] != sep:
            path = path + sep
        self.path = path
        self.index = EEGMMIDBIndex(path)

    def __getstate__(self):
        # Workaround for unpickable sqlalchemy.orm.session
        # during multiprocess dataset loading
        state = self.__dict__.copy()
        del state['index']
        return state

    def _get_dataset_by_event(self, f: File, e: Event) -> RawEDF:
        path_edf = join(self.path, f.path)
        path_fif = path_edf + '-' + e.id + '.fif.gz'
        if not isfile(path_fif):
            edf = RawEDF(f.id, path_edf, e.label)
            edf.crop(e.begin, e.end-e.begin)
            edf.open().save(path_fif)
        fif = RawFIF(f.id, path_fif, e.label)
        return fif

    def get_dataset(self) -> List[RawEDF]:
        files = self.index.db.query(File, Event)
        files = files.filter(File.id == Event.file_id)
        files = files.filter(File.format == 'edf').all()
        pool = Pool(len(sched_getaffinity(0)))
        fifs = pool.starmap(self._get_dataset_by_event, files)
        pool.close()
        pool.join()
        return fifs