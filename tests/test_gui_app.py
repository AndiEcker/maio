""" test ae.GUIApp """
import os
import pytest
from typing import Dict, Any

from ae.gui_app import MainAppBase, APP_STATE_SECTION_NAME


TST_VAR = 'tstVar'
TST_VAL = 'tstVal'
TST_DICT = {TST_VAR: TST_VAL}


class ImplementationOfABC(MainAppBase):
    """ test abc implementation stub class """
    retrieve_state_called = False
    init_called = False
    run_called = False
    start_called = False
    setup_state_called = False
    context_draw_called = False

    def setup_app_state(self, app_state: Dict[str, Any]) -> str:
        """ setup app state """
        self.setup_state_called = True
        return ""

    def on_framework_app_init(self):
        """ init app """
        self.init_called = True

    def retrieve_app_state(self) -> Dict[str, Any]:
        """ get app state """
        global TST_DICT
        self.retrieve_state_called = True
        return TST_DICT

    def run_app(self) -> str:
        """ run app """
        self.run_called = True
        return ""

    def on_framework_app_start(self):
        """ init app """
        self.start_called = True

    def on_context_draw(self):
        """ draw screen. """
        self.context_draw_called = True


class TestCallbacks:
    def test_setup_app_state(self, restore_app_env):
        app = ImplementationOfABC()
        assert app.setup_state_called

    def test_retrieve_app_state(self, restore_app_env):
        app = ImplementationOfABC()
        assert not app.retrieve_state_called
        app.retrieve_app_state()
        assert app.retrieve_state_called

    def test_init(self, restore_app_env):
        app = ImplementationOfABC()
        assert app.init_called

    def test_run(self, restore_app_env):
        app = ImplementationOfABC()
        assert not app.run_called
        app.run_app()
        assert app.run_called

    def test_start(self, restore_app_env):
        app = ImplementationOfABC()
        assert not app.start_called
        app.on_framework_app_start()
        assert app.start_called

    def test_context_draw(self, restore_app_env):
        app = ImplementationOfABC()
        assert not app.context_draw_called
        app.on_context_draw()
        assert app.context_draw_called


@pytest.fixture
def ini_file(restore_app_env):
    """ provide test config file """
    fn = 'tests/tst.ini'
    with open(fn, 'w') as file_handle:
        file_handle.write("[" + APP_STATE_SECTION_NAME + "]\n" + TST_VAR + " = " + TST_VAL)
    yield fn
    os.remove(fn)


class TestLoadSaveAppState:
    def test_load(self, ini_file, restore_app_env):
        app = ImplementationOfABC(additional_cfg_files=(ini_file, ))
        assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == TST_VAL

        assert app.load_app_state() == ""
        assert app.retrieve_app_state() == TST_DICT

    def test_save(self, ini_file, restore_app_env):
        global TST_DICT
        app = ImplementationOfABC(additional_cfg_files=(ini_file, ))
        old_dict = TST_DICT.copy()
        try:
            chg_val = 'ChangedVal'
            TST_DICT = {TST_VAR: chg_val}
            assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == TST_VAL
            assert app.retrieve_app_state() == TST_DICT

            assert app.save_app_state() == ""
            assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == chg_val
            assert app.retrieve_app_state() == TST_DICT
        finally:
            TST_DICT = old_dict
