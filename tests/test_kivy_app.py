""" test ae.kivy_app portion """
import os
import pytest
from ae.gui_app import APP_STATE_SECTION_NAME
from ae.kivy_app import KivyMainApp

TST_VAR = 'win_rectangle'
TST_VAL = (90, 60, 900, 600)

TST_DICT = {TST_VAR: TST_VAL}
def_app_state = TST_DICT.copy()


@pytest.fixture
def ini_file(restore_app_env):
    """ provide test config file """
    fn = 'tests/tst.ini'
    with open(fn, 'w') as file_handle:
        file_handle.write(f"[{APP_STATE_SECTION_NAME}]\n{def_app_state!r}")
    yield fn
    if os.path.exists(fn):      # some exception/error-check tests need to delete the INI
        os.remove(fn)


class KeyboardStub:
    """ stub to simulate keyboard instance for key events. """
    def __init__(self, **kwargs):
        self.command_keys = kwargs


class KivyAppTest(KivyMainApp):
    """ kivy main app test implementation """
    app_state_list: list
    app_state_bool: bool

    on_init_called = False
    on_start_called = False
    on_run_called = False
    on_context_called = False
    on_stop_called = False

    on_key_press_called = False
    on_key_release_called = False
    last_keys = ()

    def on_framework_app_init(self):
        """ called from KivyMainApp """
        self.on_init_called = True
        super().on_framework_app_init()

    def on_framework_app_start(self):
        """ called from KivyMainApp """
        self.on_start_called = True

    def run_app(self):
        """ called by test routine """
        self.on_run_called = True
        return super().run_app()

    def on_context_draw(self):
        """ called from KivyMainApp """
        self.on_context_called = True

    def on_framework_app_stop(self):
        """ called from KivyMainApp """
        self.on_stop_called = True

    def on_key_press(self, key, modifier):
        """ key press callback """
        self.on_key_press_called = True
        self.last_keys = key, modifier
        return True

    def on_key_release(self, key):
        """ key release callback """
        self.on_key_release_called = True
        self.last_keys = key,
        return True


class TestCallbacks:
    def test_setup_app_states(self, ini_file, restore_app_env):
        app = KivyMainApp(additional_cfg_files=(ini_file,))
        assert getattr(app, TST_VAR) == def_app_state[TST_VAR]

    def test_retrieve_app_states(self, restore_app_env):
        app = KivyMainApp()
        assert app.retrieve_app_states() == dict()

    def test_init(self, restore_app_env):
        app = KivyAppTest()
        assert app.on_init_called

    def test_run(self, restore_app_env):
        app = KivyAppTest()
        assert not app.on_run_called
        app.run_app()
        assert app.on_run_called
        assert app.framework_app
        assert app.framework_app.app_state == def_app_state

    def test_start(self, restore_app_env):
        app = KivyAppTest()
        assert not app.on_start_called
        app.run_app()
        assert app.on_start_called

    def test_context_draw(self, restore_app_env):
        app = KivyAppTest()
        assert not app.on_context_called
        app.set_context('tstCtx')
        assert app.on_context_called


class TestAppState:
    def test_retrieve_app_states(self, ini_file, restore_app_env):
        app = KivyMainApp(additional_cfg_files=(ini_file,))
        assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == TST_VAL
        assert app.retrieve_app_states() == TST_DICT

    def test_load_app_states(self, ini_file, restore_app_env):
        app = KivyMainApp(additional_cfg_files=(ini_file,))
        assert app.get_var(TST_VAR, section=APP_STATE_SECTION_NAME) == TST_VAL

        app.load_app_states()
        assert getattr(app, TST_VAR) == TST_VAL
        assert app.framework_app.app_state == TST_DICT
        assert app.retrieve_app_states() == TST_DICT

    def test_setup_app_states(self, ini_file, restore_app_env):
        assert KivyMainApp.win_rectangle == def_app_state['win_rectangle']
        app = KivyMainApp(additional_cfg_files=(ini_file,))
        assert getattr(app, TST_VAR) == TST_VAL
        app.setup_app_states(TST_DICT)
        assert getattr(app, TST_VAR) == TST_VAL

    def test_change_app_state(self, ini_file, restore_app_env):
        app = KivyMainApp(additional_cfg_files=(ini_file,))
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
        app = KivyMainApp(additional_cfg_files=(ini_file,))
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
        app = KivyMainApp(additional_cfg_files=(ini_file,))
        os.remove(ini_file)
        assert app.save_app_states() != ""

    def test_set_font_size(self, ini_file, restore_app_env):
        app = KivyAppTest(additional_cfg_files=(ini_file,))
        assert app.font_size == 0.0
        assert not app.on_context_called

        font_size = 99.9
        app.set_font_size(font_size)
        assert app.font_size == font_size
        assert app.on_context_called


class TestHelperMethods:
    def test_call_event_valid_method(self, ini_file, restore_app_env):
        app = KivyAppTest(additional_cfg_files=(ini_file,))
        assert not app.on_context_called
        assert app.call_event('on_context_draw') is None
        assert app.on_context_called

    def test_call_event_return(self, ini_file, restore_app_env):
        app = KivyAppTest(additional_cfg_files=(ini_file,))
        assert not app.on_run_called
        assert app.call_event('run_app') == ""
        assert app.on_run_called

    def test_call_event_invalid_method(self, ini_file, restore_app_env):
        app = KivyMainApp(additional_cfg_files=(ini_file,))
        assert app.call_event('invalid_method_name') is None

    def test_play_beep(self, ini_file, restore_app_env):
        app = KivyMainApp(additional_cfg_files=(ini_file,))
        assert app.play_beep() is None


class TestContext:
    def test_set_context_with_redraw(self, ini_file, restore_app_env):
        app = KivyAppTest(additional_cfg_files=(ini_file,))
        assert len(app.context_path) == 0
        assert app.context_id == ""
        assert not app.on_context_called

        ctx1 = 'first_context'
        app.set_context(ctx1)
        assert len(app.context_path) == 0
        assert app.context_id == ctx1
        assert app.on_context_called

    def test_set_context_without_redraw(self, ini_file, restore_app_env):
        app = KivyAppTest(additional_cfg_files=(ini_file,))
        assert len(app.context_path) == 0
        assert app.context_id == ""
        assert not app.on_context_called

        ctx1 = 'first_context'
        app.set_context(ctx1, redraw=False)
        assert len(app.context_path) == 0
        assert app.context_id == ctx1
        assert not app.on_context_called

    def test_context_enter(self, ini_file, restore_app_env):
        app = KivyMainApp(additional_cfg_files=(ini_file,))
        assert len(app.context_path) == 0
        ctx1 = 'first_context'
        app.context_enter(ctx1)
        assert len(app.context_path) == 1
        assert app.context_path[0] == ctx1

    def test_context_enter_next_id(self, ini_file, restore_app_env):
        app = KivyMainApp(additional_cfg_files=(ini_file,))
        assert len(app.context_path) == 0
        assert app.context_id == ""
        ctx1 = 'first_context'
        ctx2 = '2nd_context'
        app.context_enter(ctx1, ctx2)
        assert len(app.context_path) == 1
        assert app.context_path[0] == ctx1
        assert app.context_id == ctx2

    def test_context_leave(self, ini_file, restore_app_env):
        app = KivyMainApp(additional_cfg_files=(ini_file,))
        ctx1 = 'first_context'
        app.context_enter(ctx1)

        app.context_leave()

        assert len(app.context_path) == 0
        assert app.context_id == ctx1

    def test_context_leave_next_id(self, ini_file, restore_app_env):
        app = KivyMainApp(additional_cfg_files=(ini_file,))
        ctx1 = 'first_context'
        ctx2 = '2nd_context'
        ctx3 = '3rd_context'
        app.context_enter(ctx1, ctx2)

        app.context_leave(next_context_id=ctx3)

        assert len(app.context_path) == 0
        assert app.context_id == ctx3


class TestKeyEvents:
    def test_key_press_text(self, restore_app_env):
        app = KivyAppTest()
        kbd = KeyboardStub()
        key_code = 32
        key_text = ' '
        modifiers = 0
        assert app.framework_app.on_key_down(kbd, key_code, None, key_text, modifiers)
        assert app.last_keys == (key_text, modifiers)

    def test_key_press_code(self, restore_app_env):
        app = KivyAppTest()
        kbd = KeyboardStub()
        key_code = 32
        key_text = ''
        modifiers = 0
        assert app.framework_app.on_key_down(kbd, key_code, None, key_text, modifiers)
        assert app.last_keys == (key_code, modifiers)

    def test_key_release(self, restore_app_env):
        app = KivyAppTest()
        kbd = KeyboardStub()
        key_code = 32
        assert app.framework_app.on_key_up(kbd, key_code, None)
        assert app.last_keys == (key_code, )
