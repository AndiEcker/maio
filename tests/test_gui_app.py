""" test ae.gui_app portion """
import os
import pytest
from typing import Dict, Any

from ae.console import get_user_data_path

from ae.gui_app import MainAppBase, APP_STATE_SECTION_NAME, app_state_keys


TST_VAR = 'tst_var'
TST_VAL = 'tstVal'
TST_DICT = {TST_VAR: TST_VAL}


def _create_ini_file(fn):
    with open(fn, 'w') as file_handle:
        file_handle.write("[" + APP_STATE_SECTION_NAME + "]\n" + TST_VAR + " = " + TST_VAL)


@pytest.fixture
def ini_file(restore_app_env):
    """ provide test config file """
    fn = 'tests/tst.ini'
    _create_ini_file(fn)
    yield fn
    if os.path.exists(fn):      # some exception/error-check tests need to delete the INI
        os.remove(fn)


class FrameworkApp:
    """ gui framework app stub """
    app_state = dict()


class ImplementationOfMainApp(MainAppBase):
    """ test abc implementation stub class """
    retrieve_state_called = False
    init_called = False
    run_called = False
    start_called = False
    setup_state_called = False
    context_draw_called = False

    tst_var: str = ""
    font_size: float = 0.0

    def setup_app_states(self, app_state: Dict[str, Any]):
        """ setup app state """
        self.setup_state_called = True
        super().setup_app_states(app_state)

    def on_app_init(self):
        """ init app """
        self.framework_app = FrameworkApp()
        self.framework_app.app_state.update(self.retrieve_app_states())
        self.init_called = True

    def retrieve_app_states(self) -> Dict[str, Any]:
        """ get app state """
        self.retrieve_state_called = True
        return super().retrieve_app_states()

    def run_app(self) -> str:
        """ run app """
        self.run_called = True
        return ""

    def on_app_start(self):
        """ init app """
        self.start_called = True

    def on_context_draw(self):
        """ draw screen. """
        self.context_draw_called = True


class TestHelpers:
    def test_app_state_keys(self, ini_file):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        keys = app_state_keys(app._cfg_parser)
        assert isinstance(keys, tuple)
        assert len(keys) == 1
        assert keys[0] == TST_VAR


class TestCallbacks:
    def test_setup_app_states(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert app.setup_state_called

    def test_retrieve_app_states(self, restore_app_env):
        app = ImplementationOfMainApp()
        assert app.retrieve_state_called

    def test_init(self, restore_app_env):
        app = ImplementationOfMainApp()
        assert app.init_called

    def test_run(self, restore_app_env):
        app = ImplementationOfMainApp()
        assert not app.run_called
        app.run_app()
        assert app.run_called

    def test_start(self, restore_app_env):
        app = ImplementationOfMainApp()
        assert not app.start_called
        app.on_app_start()
        assert app.start_called

    def test_context_draw(self, restore_app_env):
        app = ImplementationOfMainApp()
        assert not app.context_draw_called
        app.on_context_draw()
        assert app.context_draw_called


class TestAppState:
    def test_retrieve_app_states(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == TST_VAL
        assert app.retrieve_app_states() == TST_DICT

    def test_load_app_states(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == TST_VAL

        app.load_app_states()
        assert getattr(app, TST_VAR) == TST_VAL
        assert app.framework_app.app_state == TST_DICT
        assert app.retrieve_app_states() == TST_DICT

    def test_setup_app_states(self, ini_file, restore_app_env):
        assert ImplementationOfMainApp.tst_var == ""
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert getattr(app, TST_VAR) == TST_VAL
        app.setup_app_states(TST_DICT)
        assert getattr(app, TST_VAR) == TST_VAL

    def test_change_app_state(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert app.save_app_states() == ""
        assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == TST_VAL
        assert app.retrieve_app_states() == TST_DICT

        chg_val = 'ChangedVal'
        chg_dict = {TST_VAR: chg_val}
        app.change_app_state(TST_VAR, chg_val)

        assert getattr(app, TST_VAR) == chg_val
        assert app.framework_app.app_state == chg_dict
        assert app.retrieve_app_states() == chg_dict

        assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == TST_VAL
        assert app.save_app_states() == ""
        assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == chg_val

    def test_save_app_states(self, ini_file, restore_app_env):
        global TST_DICT
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        old_dict = TST_DICT.copy()
        try:
            assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == TST_VAL
            assert app.retrieve_app_states() == TST_DICT

            chg_val = 'ChangedVal'
            TST_DICT = {TST_VAR: chg_val}
            setattr(app, TST_VAR, chg_val)
            assert app.save_app_states() == ""
            assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == chg_val
            assert app.retrieve_app_states() == TST_DICT
        finally:
            TST_DICT = old_dict

    def test_save_app_states_exception(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        os.remove(ini_file)
        assert app.save_app_states() != ""

    def test_set_font_size(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert app.font_size == 0.0
        assert not app.context_draw_called

        font_size = 99.9
        app.set_font_size(font_size)
        assert app.font_size == font_size
        assert app.context_draw_called


class TestOtherMainAppMethods:
    def test_call_event_valid_method(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert not app.context_draw_called
        assert app.call_event('on_context_draw') is None
        assert app.context_draw_called

    def test_call_event_return(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert not app.run_called
        assert app.call_event('run_app') == ""
        assert app.run_called

    def test_call_event_invalid_method(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert app.call_event('invalid_method_name') is None

    def test_ini_file_cwd_default(self, restore_app_env, tst_app_key):
        app = ImplementationOfMainApp()
        ini_file_path = os.path.abspath(tst_app_key + ".ini")
        assert app._main_cfg_fnam == ini_file_path

    def test_ini_file_added_in_tests_subdir(self, restore_app_env, tst_app_key, ini_file):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        ini_file_path = os.path.abspath(ini_file)
        assert app._main_cfg_fnam == ini_file_path

    def test_ini_file_user_data_path(self, restore_app_env, tst_app_key):
        ini_file_path = os.path.abspath(os.path.join(get_user_data_path(), tst_app_key + ".ini"))
        try:
            _create_ini_file(ini_file_path)
            app = ImplementationOfMainApp()
            assert app._main_cfg_fnam == ini_file_path
        finally:
            if os.path.exists(ini_file_path):
                os.remove(ini_file_path)

    def test_play_beep(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert app.play_beep() is None


class TestContext:
    def test_set_context_with_redraw(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert len(app.context_path) == 0
        assert app.context_id == ""
        assert not app.context_draw_called

        ctx1 = 'first_context'
        app.set_context(ctx1)
        assert len(app.context_path) == 0
        assert app.context_id == ctx1
        assert app.context_draw_called

    def test_set_context_without_redraw(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert len(app.context_path) == 0
        assert app.context_id == ""
        assert not app.context_draw_called

        ctx1 = 'first_context'
        app.set_context(ctx1, redraw=False)
        assert len(app.context_path) == 0
        assert app.context_id == ctx1
        assert not app.context_draw_called

    def test_context_enter(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert len(app.context_path) == 0
        ctx1 = 'first_context'
        app.context_enter(ctx1)
        assert len(app.context_path) == 1
        assert app.context_path[0] == ctx1

    def test_context_enter_next_id(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        assert len(app.context_path) == 0
        assert app.context_id == ""
        ctx1 = 'first_context'
        ctx2 = '2nd_context'
        app.context_enter(ctx1, ctx2)
        assert len(app.context_path) == 1
        assert app.context_path[0] == ctx1
        assert app.context_id == ctx2

    def test_context_leave(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        ctx1 = 'first_context'
        app.context_enter(ctx1)

        app.context_leave()

        assert len(app.context_path) == 0
        assert app.context_id == ctx1

    def test_context_leave_next_id(self, ini_file, restore_app_env):
        app = ImplementationOfMainApp(additional_cfg_files=(ini_file,))
        ctx1 = 'first_context'
        ctx2 = '2nd_context'
        ctx3 = '3rd_context'
        app.context_enter(ctx1, ctx2)

        app.context_leave(next_context_id=ctx3)

        assert len(app.context_path) == 0
        assert app.context_id == ctx3
