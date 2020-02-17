""" application environment updater

This module is providing helper functions for easy deployment of
updates for your Python application.

updater helper functions
========================

Update any files on the destination machine with the help of the functions
:func:`check_local_moves` and :func:`check_local_overwrites`.

For more complex updates the function :func:`check_local_updates` checks
if your deployment package contains a python update script
that will be executed (and only one time) on the next startup
of your application.

For a temporary work-around or bug-fix you can deploy your application
update with a bootstrap python script which will be executed on every
startup of your application. The detection and execution of such
bootstrap script is done by the function :func:`check_local_bootstrap`-

The function :func:`check_all` does all the above checks and is recommended
for to be used for standard applications, like so::

    import python_and_3rd_party_libs
    import ae.updater
    import any_project_local_libs

    ae.updater.check_all()

    app = WhatEverApp(app_name=...)
    app.add_option(...)
    ...

Make sure that :func:`check_all` get called before you initialize any
app instances if you want to update ony :ref:`config-variables`, like
:ref:`application status` or user preferences.

..hint: More info you find in the doc-strings of the check functions.
"""
import os
import glob
import shutil
from typing import List

from ae.core import module_callable         # type: ignore
from ae.console import get_user_data_path   # type: ignore


MOVES_SRC_FOLDER_NAME = 'ae_updater_moves'
OVERWRITES_SRC_FOLDER_NAME = 'ae_updater_overwrites'

UPDATER_MODULE_NAME = 'ae_updater'
BOOTSTRAP_MODULE_NAME = 'ae_bootstrap'


def _move_files(src_folder: str, dst_folder: str, overwrite: bool = False) -> List[str]:
    """ move files from src_folder into dst_folder, optionally overwriting the destination file.

    :param src_folder:      path to source folder/directory where the files get moved from.
    :param dst_folder:      path to destination folder/directory where the files get moved to. If
                            you pass an empty string then the user data/preferences path will be used.
    :param overwrite:       pass True to overwrite existing files in the destination folder/directory.
    :return:                list of moved files, with their destination path.
    """
    if not dst_folder:
        dst_folder = get_user_data_path()

    updated = list()

    if os.path.exists(src_folder):
        for src_file in glob.glob(os.path.join(src_folder, '**'), recursive=True):
            if os.path.isfile(src_file):
                dst_file = os.path.abspath(os.path.join(dst_folder, os.path.relpath(src_file, src_folder)))
                if overwrite or not os.path.exists(dst_file):
                    dst_sub_dir = os.path.dirname(dst_file)
                    if not os.path.exists(dst_sub_dir):
                        os.makedirs(dst_sub_dir)
                    updated.append(shutil.move(src_file, dst_file))

    return updated


def check_local_moves(src_folder: str = MOVES_SRC_FOLDER_NAME, dst_folder: str = "") -> List[str]:
    """ check on missing files to be moved from src_folder to the dst_folder.

    :param src_folder:      path to source folder/directory where the files get moved from. If not specified
                            then :data:`MOVES_SRC_FOLDER_NAME` will be used
                            for to check and do local file moves.
    :param dst_folder:      path to destination folder/directory where the files get moved to. If not specified
                            or if you pass an empty string then the user data/preferences path will be used.
    :return:                list of moved files, with their destination path.
    """
    return _move_files(src_folder, dst_folder)


def check_local_overwrites(src_folder: str = OVERWRITES_SRC_FOLDER_NAME, dst_folder: str = "") -> List[str]:
    """ check on files to be moved from the source directory and overwritten within the destination directory.

    :param src_folder:      path to source folder/directory where the files get moved from. If not specified
                            then :data:`OVERWRITES_SRC_FOLDER_NAME` will be used
                            for to check and move local file overwrites.
    :param dst_folder:      path to destination folder/directory where the files get moved to. If not specified
                            or if you pass an empty string then the user data/preferences path will be used.
    :return:                list of moved files, with their destination path.
    """
    return _move_files(src_folder, dst_folder, overwrite=True)


def check_local_updates() -> bool:
    """ check if ae_updater script exists in the current working directory for to be executed and deleted.

    .. note:
        If the module :data:`UPDATER_MODULE_NAME` exists, is declaring a :func:`run_updater` function and that
        function is returning a non-empty return value (evaluating as boolean True) then the module will be
        automatically deleted after the execution of the function.

    :return:                return value (True) of executed run_updater method (if module&function exists), else False.
    """
    _, func = module_callable(UPDATER_MODULE_NAME + ':run_updater')
    ret = func() if func else False
    if ret:
        os.remove(UPDATER_MODULE_NAME + ".py")
    return ret


def check_local_bootstraps() -> bool:
    """ check if ae_bootstrap script exists in the current working directory for to be executed on app startup.

    :return:                return value (True) of executed run_updater function (if module&function exists) else False.
    """
    _, func = module_callable(BOOTSTRAP_MODULE_NAME + ':run_updater')
    return func() if func else False


def check_all(src_folder: str = "", dst_folder: str = "") -> List[str]:
    """ check all outstanding scripts to be executed and files to be moved/overwritten.

    :param src_folder:      path to source folder/directory where the files get moved from. If not specified
                            or if you pass an empty string then :data:`MOVES_SRC_FOLDER_NAME` will be used
                            for to check local file updates and :data:`OVERWRITES_SRC_FOLDER_NAME` will be used
                            for to check and move local file overwrites.
    :param dst_folder:      path to destination folder/directory where the files get moved to. If not specified
                            or if you pass an empty string then the user data/preferences path will be used.
    :return:                list of moved and overwritten files, with their destination path.
    """
    check_local_updates()
    check_local_bootstraps()

    return (check_local_moves(src_folder=src_folder or MOVES_SRC_FOLDER_NAME, dst_folder=dst_folder) +
            check_local_overwrites(src_folder=src_folder or OVERWRITES_SRC_FOLDER_NAME, dst_folder=dst_folder))
