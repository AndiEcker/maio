""" Base class for applications with a graphical user interface. """
from abc import ABC, abstractmethod
from configparser import ConfigParser
from typing import Any, Dict, Tuple, List

from ae.core import DEBUG_LEVEL_VERBOSE         # type: ignore
from ae.literal import Literal                  # type: ignore
from ae.console import ConsoleApp               # type: ignore


AppStateType = Dict[str, Any]           #: app state config variable type

APP_STATE_SECTION_NAME = 'aeAppState'   #: config section name for to store app state


def app_state_keys(cfg_parser: ConfigParser) -> Tuple:
    """

    :param cfg_parser:      instance of the :class:`~configparser.ConfigParser` provided by
                            :class:`~ae.console.ConsoleApp`.
    :return:                tuple of all app state item keys.
    """
    if cfg_parser.has_section(APP_STATE_SECTION_NAME):
        return tuple(cfg_parser.options(APP_STATE_SECTION_NAME))
    return tuple()


class MainAppBase(ConsoleApp, ABC):
    """ abstract base class for to implement a GUIApp-conform app class """

    context_path: List[str]                                 #: list of context ids, reflecting recent user actions
    context_id: str = ""                                    #: id of the current app context (entered by the app user)
    font_size: float = 30.                                  #: font size used for toolbar and context screens
    framework_app: Any = None                               #: app class instance of the used GUI framework
    selected_item_ink: Tuple = (0.69, 1.0, 0.39, 0.18)      #: rgba color tuple for list items (selected)
    unselected_item_ink: Tuple = (0.39, 0.39, 0.39, 0.18)   #: rgba color tuple for list items (unselected)
    context_path_ink: Tuple = (0.99, 0.99, 0.39, 0.48)      #: rgba color tuple for drag&drop item placeholder
    context_id_ink: Tuple = (0.99, 0.99, 0.69, 0.69)        #: rgba color tuple for drag&drop sub_list placeholder

    win_rectangle: Tuple = (0, 0, 800, 600)                 #: app window coordinates

    debug_bubble: bool = False                              #: visibility of a popup/bubble showing debugging info
    info_bubble: Any = None                                 #: optional DebugBubble widget

    root_win: Any = None                                    #: app window
    root_layout: Any = None                                 #: app root layout

    def __init__(self, debug_bubble: bool = False, **console_app_kwargs):
        """ create instance of app class.

        :param debug_bubble:
        :param console_app_kwargs:
        """
        self.context_path = list()
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

    def setup_app_state(self, app_state: AppStateType) -> str:
        """ put app state variables into main app instance for to prepare framework app.run_app """
        for key in app_state_keys(self._cfg_parser):
            if key in app_state and (hasattr(self, key) or hasattr(self.__class__, key)):
                # set main app instance attribute and update also self.framework_app.app_state (if exists/initialized)
                self.change_app_state(key, app_state[key])
        return ""

    def call_event(self, method: str, *args, **kwargs) -> Any:
        """ dispatch event to inheriting instances. """
        event_callback = getattr(self, method, None)
        if event_callback:
            return event_callback(*args, **kwargs)
        return None

    def change_app_state(self, state_name: str, new_value: Any):
        """ change single app state item to value in self.attribute and app_state dict item. """
        setattr(self, state_name, new_value)
        if self.framework_app and self.framework_app.app_state:     # if framework needs duplicate DictProperty
            self.framework_app.app_state[state_name] = new_value

    def context_enter(self, context_id: str, next_context_id: str = ''):
        """ user extending/entering/adding new context_id (e.g. navigates down in the app context path/tree) """
        self.context_path.append(context_id)
        self.set_context(next_context_id)

    def context_leave(self, next_context_id: str = ''):
        """ user navigates up in the data tree """
        list_name = self.context_path.pop()
        self.set_context(next_context_id or list_name)

    def load_app_state(self) -> str:
        """ load application state for to prepare app.run_app """
        self.debug_bubble = self.get_opt('debugLevel') >= DEBUG_LEVEL_VERBOSE

        app_state = dict()
        if self._cfg_parser.has_section(APP_STATE_SECTION_NAME):
            items = self._cfg_parser.items(APP_STATE_SECTION_NAME)
            for key, state in items:
                lit = Literal(state, value_type=type(getattr(self, key, "")))
                app_state[key] = lit.value

        return self.setup_app_state(app_state)

    @staticmethod
    def play_beep():
        """ make a short beep sound """
        print(chr(7), "BEEP")

    def retrieve_app_state(self) -> AppStateType:
        """ determine the state of a running app and return it as dict """
        app_state = dict()
        for key in app_state_keys(self._cfg_parser):
            app_state[key] = getattr(self, key)

        return app_state

    def save_app_state(self) -> str:
        """ save app state in config file """
        err_msg = ""

        app_state = self.retrieve_app_state()
        for key, state in app_state.items():
            err_msg = self.set_var(key, state, section=APP_STATE_SECTION_NAME)
            if err_msg:
                break
        self.load_cfg_files()
        return err_msg

    def set_context(self, context_id: str, redraw: bool = True):
        """ propagate change of context path and context/current id/item and display changed context.

        :param context_id:  name of new current item.
        :param redraw:      pass False to prevent to redraw the context screens.
        """
        self.change_app_state('context_path', self.context_path)
        self.change_app_state('context_id', context_id)
        if redraw:
            self.call_event('on_context_draw')

    def set_font_size(self, font_size: float):
        """ change font size. """
        self.change_app_state('font_size', font_size)
        self.call_event('on_context_draw')
