""" unit tests for ae.updater portion. """
import os
import shutil
import tempfile

import pytest

from ae.console import get_user_data_path
from ae.updater import (
    MOVES_SRC_FOLDER_NAME, OVERWRITES_SRC_FOLDER_NAME, UPDATER_MODULE_NAME, BOOTSTRAP_MODULE_NAME,
    check_local_moves, check_local_overwrites, check_local_updates, check_local_bootstraps, check_all)

FILE0 = 'app.ini'
CONTENT0 = "TEST FILE0 CONTENT"
OLD_CONTENT0 = "OLD/LOCKED FILE0 CONTENT"

DIR1 = 'app_dir'
FILE1 = 'app.png'
CONTENT1 = "TEST FILE1 CONTENT"


@pytest.fixture(params=[MOVES_SRC_FOLDER_NAME, OVERWRITES_SRC_FOLDER_NAME])
def files_to_move(request, tmpdir):
    """ create test files in source directory for to be moved and/or overwritten. """
    src_dir = tmpdir.mkdir(request.param)

    src_file1 = src_dir.join(FILE0)
    src_file1.write(CONTENT0)
    src_sub_dir = src_dir.mkdir(DIR1)
    src_file2 = src_sub_dir.join(FILE1)
    src_file2.write(CONTENT1)

    yield str(src_file1), str(src_file2)

    # tmpdir/dst_dir1 will be removed automatically by pytest - leaving the last three temporary directories
    # .. see https://docs.pytest.org/en/latest/tmpdir.html#the-default-base-temporary-directory
    # shutil.rmtree(tmpdir)


def _create_file_at_destination(dst_folder):
    """ create file0 at destination folder for to block move. """
    dst_file = os.path.join(dst_folder, FILE0)
    with open(dst_file, 'w') as fp:
        fp.write(OLD_CONTENT0)
    return dst_file


def _file_content(fn):
    with open(fn) as fp:
        fc = fp.read()
    return fc


class TestFileUpdates:
    def test_moves_to_parent_dir(self, files_to_move):
        src_dir = os.path.dirname(files_to_move[0])
        dst_dir = os.path.join(src_dir, '..')
        for src_file_path in files_to_move:
            assert os.path.exists(src_file_path)
            assert not os.path.exists(os.path.join(dst_dir, os.path.relpath(src_file_path, src_dir)))

        check_local_moves(src_folder=src_dir, dst_folder=dst_dir)

        if MOVES_SRC_FOLDER_NAME in src_dir:
            for src_file_path in files_to_move:
                assert not os.path.exists(src_file_path)
                assert os.path.exists(os.path.join(dst_dir, os.path.relpath(src_file_path, src_dir)))

    def test_blocked_moves_to_parent_dir(self, files_to_move):
        src_dir = os.path.dirname(files_to_move[0])
        dst_dir = os.path.join(src_dir, '..')
        dst_block_file = _create_file_at_destination(dst_dir)
        assert os.path.exists(dst_block_file)
        for src_file_path in files_to_move:
            assert os.path.exists(src_file_path)
            dst_file = os.path.join(dst_dir, os.path.relpath(src_file_path, src_dir))
            assert dst_file == dst_block_file or not os.path.exists(dst_file)

        check_local_moves(src_folder=src_dir, dst_folder=dst_dir)

        if MOVES_SRC_FOLDER_NAME in src_dir:
            assert os.path.exists(files_to_move[0])
            assert _file_content(files_to_move[0]) == CONTENT0
            dst_file = os.path.join(dst_dir, os.path.relpath(files_to_move[0], src_dir))
            assert os.path.exists(dst_file)
            assert _file_content(dst_file) == OLD_CONTENT0

            assert not os.path.exists(files_to_move[1])
            dst_file = os.path.join(dst_dir, os.path.relpath(files_to_move[1], src_dir))
            assert os.path.exists(dst_file)
            assert _file_content(dst_file) == CONTENT1

    def test_overwrites_to_parent_dir(self, files_to_move):
        src_dir = os.path.dirname(files_to_move[0])
        dst_dir = os.path.join(src_dir, '..')
        for src_file_path in files_to_move:
            assert os.path.exists(src_file_path)
            assert not os.path.exists(os.path.join(dst_dir, os.path.relpath(src_file_path, src_dir)))

        check_local_overwrites(src_folder=src_dir, dst_folder=dst_dir)

        if OVERWRITES_SRC_FOLDER_NAME in src_dir:
            for src_file_path in files_to_move:
                assert not os.path.exists(src_file_path)
                assert os.path.exists(os.path.join(dst_dir, os.path.relpath(src_file_path, src_dir)))

    def test_unblocked_overwrites_to_parent_dir(self, files_to_move):
        src_dir = os.path.dirname(files_to_move[0])
        dst_dir = os.path.join(src_dir, '..')
        dst_block_file = _create_file_at_destination(dst_dir)
        assert os.path.exists(dst_block_file)
        for src_file_path in files_to_move:
            assert os.path.exists(src_file_path)
            dst_file = os.path.join(dst_dir, os.path.relpath(src_file_path, src_dir))
            assert dst_file == dst_block_file or not os.path.exists(dst_file)

        check_local_overwrites(src_folder=src_dir, dst_folder=dst_dir)

        if OVERWRITES_SRC_FOLDER_NAME in src_dir:
            assert not os.path.exists(files_to_move[0])
            dst_file = os.path.join(dst_dir, os.path.relpath(files_to_move[0], src_dir))
            assert os.path.exists(dst_file)
            assert _file_content(dst_file) == CONTENT0

            assert not os.path.exists(files_to_move[1])
            dst_file = os.path.join(dst_dir, os.path.relpath(files_to_move[1], src_dir))
            assert os.path.exists(dst_file)
            assert _file_content(dst_file) == CONTENT1


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

    def test_file_moves_to_user_dir_via_check_all(self, files_to_move):
        src_dir = os.path.dirname(files_to_move[0])
        dst_dir = get_user_data_path()

        moved = list()
        try:
            moved += check_all(src_folder=src_dir)

            for src_file_path in files_to_move:
                assert not os.path.exists(src_file_path)
                assert os.path.exists(os.path.join(dst_dir, os.path.relpath(src_file_path, src_dir)))
        finally:
            for dst_file_path in moved:
                dst_path = os.path.relpath(dst_file_path, dst_dir)
                if os.path.exists(dst_file_path):
                    os.remove(dst_file_path)
                    if dst_path != os.path.basename(dst_file_path):
                        shutil.rmtree(os.path.dirname(dst_file_path))

    def test_updater_via_check_all(self, created_run_updater):
        assert os.path.exists(created_run_updater)
        check_all()
        assert not os.path.exists(created_run_updater)

    def test_bootstrap_via_check_all(self, created_bootstrap):
        assert os.path.exists(created_bootstrap)
        check_all()
        assert os.path.exists(created_bootstrap)
