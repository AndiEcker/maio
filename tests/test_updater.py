""" unit tests for ae.updater portion. """
import os
import shutil
import tempfile

import pytest

from ae.updater import (
    MOVES_FOLDER_NAME, OVERWRITES_FOLDER_NAME, UPDATER_MODULE_NAME, BOOTSTRAP_MODULE_NAME,
    check_local_moves, check_local_overwrites, check_local_updates, check_local_bootstraps, check_all)

FILE1 = 'app.ini'
CONTENT1 = "TEST FILE CONTENT"
OLD_CONTENT1 = "OLD/LOCKED FILE CONTENT"

DIR2 = 'img'
FILE2 = os.path.join(DIR2, 'app.png')
CONTENT2 = "TEST FILE2 CONTENT"


@pytest.fixture
def files_to_move():
    """ create test files to be moved. """
    cwd = os.getcwd()
    tmp_dir = tempfile.mkdtemp()
    os.chdir(tmp_dir)

    os.mkdir(MOVES_FOLDER_NAME)
    os.mkdir(os.path.join(MOVES_FOLDER_NAME, DIR2))
    fn = os.path.join(MOVES_FOLDER_NAME, FILE1)
    with open(fn, 'w') as fp:
        fp.write(CONTENT1)
    fn = os.path.join(MOVES_FOLDER_NAME, FILE2)
    with open(fn, 'w') as fp:
        fp.write(CONTENT2)

    os.mkdir(DIR2)

    yield [FILE1, FILE2]

    shutil.rmtree(tmp_dir)
    os.chdir(cwd)


@pytest.fixture
def file_existing_at_destination():
    """ files to block move, to be added after files_to_move. """
    with open(FILE1, 'w') as fp:
        fp.write(OLD_CONTENT1)
    yield FILE1


@pytest.fixture
def files_to_overwrite():
    """ create test files to be overwritten. """
    cwd = os.getcwd()
    tmp_dir = tempfile.mkdtemp()
    os.chdir(tmp_dir)

    os.mkdir(OVERWRITES_FOLDER_NAME)
    os.mkdir(os.path.join(OVERWRITES_FOLDER_NAME, DIR2))
    fn = os.path.join(OVERWRITES_FOLDER_NAME, FILE1)
    with open(fn, 'w') as fp:
        fp.write(CONTENT1)
    fn = os.path.join(OVERWRITES_FOLDER_NAME, FILE2)
    with open(fn, 'w') as fp:
        fp.write(CONTENT2)

    os.mkdir(DIR2)

    yield [FILE1, FILE2]

    shutil.rmtree(tmp_dir)
    os.chdir(cwd)


def _file_content(fn):
    with open(fn) as fp:
        fc = fp.read()
    return fc


class TestFileUpdates:
    def test_moves(self, files_to_move):
        for fn in files_to_move:
            assert os.path.exists(os.path.join(MOVES_FOLDER_NAME, fn))
            assert not os.path.exists(fn)

        check_local_moves()

        for fn in files_to_move:
            assert not os.path.exists(os.path.join(MOVES_FOLDER_NAME, fn))
            assert os.path.exists(fn)

    def test_blocked_moves(self, files_to_move, file_existing_at_destination):
        for fn in files_to_move:
            assert os.path.exists(os.path.join(MOVES_FOLDER_NAME, fn))
        assert os.path.exists(FILE1)
        assert not os.path.exists(FILE2)

        check_local_moves()

        assert os.path.exists(os.path.join(MOVES_FOLDER_NAME, FILE1))
        assert _file_content(os.path.join(MOVES_FOLDER_NAME, FILE1)) == CONTENT1
        assert os.path.exists(FILE1)
        assert _file_content(FILE1) == OLD_CONTENT1
        assert not os.path.exists(os.path.join(MOVES_FOLDER_NAME, FILE2))
        assert os.path.exists(FILE2)
        assert _file_content(FILE2) == CONTENT2

    def test_overwrites(self, files_to_overwrite):
        for fn in files_to_overwrite:
            assert os.path.exists(os.path.join(OVERWRITES_FOLDER_NAME, fn))
            assert not os.path.exists(fn)

        check_local_overwrites()

        for fn in files_to_overwrite:
            assert not os.path.exists(os.path.join(OVERWRITES_FOLDER_NAME, fn))
            assert os.path.exists(fn)

    def test_unblocked_overwrites(self, files_to_overwrite, file_existing_at_destination):
        for fn in files_to_overwrite:
            assert os.path.exists(os.path.join(OVERWRITES_FOLDER_NAME, fn))
        assert os.path.exists(FILE1)
        assert _file_content(FILE1) == OLD_CONTENT1
        assert not os.path.exists(FILE2)

        check_local_overwrites()

        assert not os.path.exists(os.path.join(OVERWRITES_FOLDER_NAME, FILE1))
        assert os.path.exists(FILE1)
        assert _file_content(FILE1) == CONTENT1
        assert not os.path.exists(os.path.join(OVERWRITES_FOLDER_NAME, FILE2))
        assert os.path.exists(FILE2)
        assert _file_content(FILE2) == CONTENT2


def _create_module(tmp_dir, module_name):
    fn = os.path.join(tmp_dir, module_name + '.py')
    with open(fn, 'w') as fp:
        fp.write("""def run_updater():\n    return True""")

    return fn


@pytest.fixture
def created_run_updater():
    """ create test module to be executed. """
    cwd = os.getcwd()
    tmp_dir = tempfile.mkdtemp()
    os.chdir(tmp_dir)

    yield _create_module(tmp_dir, UPDATER_MODULE_NAME)

    shutil.rmtree(tmp_dir)
    os.chdir(cwd)


@pytest.fixture
def created_bootstrap():
    """ create test module to be executed. """
    cwd = os.getcwd()
    tmp_dir = tempfile.mkdtemp()
    os.chdir(tmp_dir)

    yield _create_module(tmp_dir, BOOTSTRAP_MODULE_NAME)

    shutil.rmtree(tmp_dir)
    os.chdir(cwd)


class TestRunUpdater:
    def test_updater(self, created_run_updater):
        assert os.path.exists(created_run_updater)
        check_local_updates()
        assert not os.path.exists(created_run_updater)

    def test_bootstrap(self, created_bootstrap):
        assert os.path.exists(created_bootstrap)
        check_local_bootstraps()
        assert os.path.exists(created_bootstrap)


class TestCheckAll:
    def test_nothing_to_do(self):
        cwd = os.getcwd()
        tmp_dir = tempfile.mkdtemp()
        os.chdir(tmp_dir)

        check_all()

        shutil.rmtree(tmp_dir)
        os.chdir(cwd)

    def test_only_moves(self, files_to_move):
        for fn in files_to_move:
            assert os.path.exists(os.path.join(MOVES_FOLDER_NAME, fn))
            assert not os.path.exists(fn)

        check_all()

        for fn in files_to_move:
            assert not os.path.exists(os.path.join(MOVES_FOLDER_NAME, fn))
            assert os.path.exists(fn)

    def test_only_updater(self, created_run_updater):
        assert os.path.exists(created_run_updater)
        check_all()
        assert not os.path.exists(created_run_updater)
