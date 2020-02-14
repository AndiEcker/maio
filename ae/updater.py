""" application environment updater """
import os
import glob
import shutil
from typing import List

from ae.core import module_callable     # type: ignore


MOVES_FOLDER_NAME = 'ae_updater_moves'
OVERWRITES_FOLDER_NAME = 'ae_updater_overwrites'

UPDATER_MODULE_NAME = 'ae_updater'
BOOTSTRAP_MODULE_NAME = 'ae_bootstrap'


def _update_files(src_folder: str, dst_folder: str, overwrite: bool = False) -> List[str]:
    """ update and remove files from src_folder into dst_folder. """
    updated = list()

    if os.path.exists(src_folder):
        for src_file in glob.glob(os.path.join(src_folder, '**'), recursive=True):
            if os.path.isfile(src_file):
                dst_file = os.path.join(dst_folder, src_file[len(src_folder) + len(os.sep):])
                if overwrite or not os.path.exists(dst_file):
                    updated.append(shutil.move(src_file, dst_file))

    return updated


def check_local_moves(src_folder: str = MOVES_FOLDER_NAME, dst_folder: str = ".") -> List[str]:
    """ check on files to be moved to app directory. """
    return _update_files(src_folder, dst_folder)


def check_local_overwrites(src_folder: str = OVERWRITES_FOLDER_NAME, dst_folder: str = ".") -> List[str]:
    """ check on files to be overwritten within app directory. """
    return _update_files(src_folder, dst_folder, overwrite=True)


def check_local_updates() -> bool:
    """ check if ae_updater script exists for to be executed and deleted. """
    _, func = module_callable(UPDATER_MODULE_NAME + ':run_updater')
    ret = func() if func else False
    if ret:
        os.remove(UPDATER_MODULE_NAME + ".py")
    return ret


def check_local_bootstraps() -> bool:
    """ check if ae_bootstrap script exists for to be executed on app startup. """
    _, func = module_callable(BOOTSTRAP_MODULE_NAME + ':run_updater')
    return func() if func else False


def check_all():
    """ check all update features. """
    check_local_updates()
    check_local_bootstraps()

    check_local_overwrites()
    check_local_moves()
