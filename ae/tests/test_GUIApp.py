""" test ae.GUIApp """
import os
import pytest
from typing import Dict, Any

from ae.GUIApp import MainAppBase, APP_STATE_SECTION_NAME


TST_VAR = 'tstVar'
TST_VAL = 'tstVal'
TST_DICT = {TST_VAR: TST_VAL}


class ImplementationOfABC(MainAppBase):
    """ test abc implementation stub class """
    get_state_called = False
    init_called = False
    run_called = False
    set_state_called = False

    def get_app_state(self) -> Dict[str, Any]:
        """ get app state """
        global TST_DICT
        self.get_state_called = True
        return TST_DICT

    def on_framework_app_init(self):
        """ init app """
        self.init_called = True

    def run_app(self) -> str:
        """ run app """
        self.run_called = True
        return ""

    def set_app_state(self, app_state: Dict[str, Any]) -> str:
        """ set app state """
        self.set_state_called = True
        return ""


class TestCallbacks:
    def test_get_state(self):
        app = ImplementationOfABC()
        assert not app.get_state_called
        app.get_app_state()
        assert app.get_state_called

    def test_init(self):
        app = ImplementationOfABC()
        assert app.init_called

    def test_run(self):
        app = ImplementationOfABC()
        assert not app.get_state_called
        app.get_app_state()
        assert app.get_state_called

    def test_set_state(self):
        app = ImplementationOfABC()
        assert not app.set_state_called
        app.set_app_state(TST_DICT)
        assert app.set_state_called


@pytest.fixture
def ini_file(restore_app_env):
    """ provide test config file """
    fn = 'tests/tst.ini'
    with open(fn, 'w') as file_handle:
        file_handle.write("[" + APP_STATE_SECTION_NAME + "]\n" + TST_VAR + " = " + TST_VAL)
    yield fn
    os.remove(fn)


class TestLoadSaveAppState:
    def test_load(self, ini_file):
        app = ImplementationOfABC(additional_cfg_files=(ini_file, ))
        assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == TST_VAL

        assert app.load_app_state() == ""
        assert app.get_app_state() == TST_DICT

    def test_save(self, ini_file):
        global TST_DICT
        app = ImplementationOfABC(additional_cfg_files=(ini_file, ))
        old_dict = TST_DICT.copy()
        try:
            chg_val = 'ChangedVal'
            TST_DICT = {TST_VAR: chg_val}
            assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == TST_VAL
            assert app.get_app_state() == TST_DICT

            assert app.save_app_state() == ""
            assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == chg_val
            assert app.get_app_state() == TST_DICT
        finally:
            TST_DICT = old_dict
