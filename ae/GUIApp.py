""" Base class for applications with a graphical user interface. """
from abc import ABC, abstractmethod
from configparser import ConfigParser
from typing import Any, Dict, Tuple, List

from ae.core import DEBUG_LEVEL_VERBOSE
from ae.literal import Literal
from ae.console import ConsoleApp


AppStateType = Dict[str, Any]           #: app state config variable type

APP_STATE_SECTION_NAME = 'aeAppState'   #: config section name for to store app state


def app_state_keys(cfg_parser: ConfigParser) -> Tuple:
    """

    :param cfg_parser:      instance of the :class:`~configparser.ConfigParser` provided by
                            :class:`~ae.console.ConsoleApp`.
    :return:                tuple of all app state item keys.
    """
    return tuple(cfg_parser.options(APP_STATE_SECTION_NAME))


class MainAppBase(ConsoleApp, ABC):
    """ abstract base class for to implement a GUIApp-conform app class """

    context_path: List[str] = list()        #: list of context ids, reflecting recent user actions
    context_id: str = ""                    #: id of the current app context (entered by the app user)
    font_size: float = 30.                  #: font size used for toolbar and context screens
    framework_app: Any = None               #: app class instance of the used GUI framework
    selected_item_ink: Tuple = (0.69, 1.0, 0.39, 0.18)      #: rgba color tuple
    unselected_item_ink: Tuple = (0.39, 0.39, 0.39, 0.18)
    win_rectangle: Tuple = (0, 0, 800, 600)

    debug_bubble: bool = False              #: visibility of a popup/bubble showing debugging info
    info_bubble: Any = None                 #: optional DebugBubble widget

    def __init__(self, debug_bubble: bool = False, **console_app_kwargs):
        """ create instance of app class.

        :param debug_bubble:
        :param console_app_kwargs:
        """
        self.debug_bubble = debug_bubble
        super().__init__(**console_app_kwargs)
        self.load_app_state()
        self.on_framework_app_init()

    # abstract methods

    @abstractmethod
    def on_framework_app_init(self):
        """ callback to framework api for to initialize an app instance. """

    @abstractmethod
    def run_app(self) -> str:
        """ startup main and framework applications. """

    # base implementation helper methods (can be overwritten by framework portion or by user main app)

    def change_app_state(self, state_name, new_value):
        """ change single app state item to value in self.attribute and app_state dict item """
        setattr(self, state_name, new_value)
        self.framework_app.app_state[state_name] = new_value

    def context_enter(self, context_id: str, next_context_id: str = ''):
        """ user extending/entering/adding new context_id (e.g. navigates down in the app context path/tree) """
        self.context_path.append(context_id)
        self._set_context_path_and_id(next_context_id)

    def context_leave(self):
        """ user navigates up in the data tree """
        list_name = self.context_path.pop()
        self._set_context_path_and_id(list_name)

    def get_app_state(self) -> AppStateType:
        """ determine the state of a running app and return it as dict """
        app_state = dict()
        for key in app_state_keys(self._cfg_parser):
            app_state[key] = getattr(self, key)

        return app_state

    def load_app_state(self) -> str:
        """ load application state for to prepare app.run_app """
        self.debug_bubble = self.get_opt('debugLevel') >= DEBUG_LEVEL_VERBOSE

        items = self._cfg_parser.items(APP_STATE_SECTION_NAME)
        app_state = dict()
        for key, state in items:
            lit = Literal(state, value_type=type(getattr(self, key, "")))
            app_state[key] = lit.value

        return self.set_app_state(app_state)

    @staticmethod
    def play_beep():
        """ make a short beep sound """
        print(chr(7), "BEEP")

    def save_app_state(self) -> str:
        """ save app state in config file """
        err_msg = ""

        app_state = self.get_app_state()
        for key, state in app_state.items():
            err_msg = self.set_var(key, state, section=APP_STATE_SECTION_NAME)
            if err_msg:
                break
        self.load_cfg_files()
        return err_msg

    def set_app_state(self, app_state: AppStateType) -> str:
        """ set/change the state of a running app """
        for key in app_state_keys(self._cfg_parser):
            if key in app_state and (hasattr(self, key) or hasattr(self.__class__, key)):
                setattr(self, key, app_state[key])
        return ""

    def _set_context_path_and_id(self, context_id):
        """ propagate change of context path and context/current id/item and display changed context.

        :param context_id:   name of new current item.
        """
        self.change_app_state('context_path', self.context_path)
        self.change_app_state('context_id', context_id)

        event_callback = getattr(self, 'on_context_draw', None)
        if event_callback:
            event_callback()
