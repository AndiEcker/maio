""" Base class for applications with a graphical user interface """
from abc import ABC, abstractmethod
from typing import Any, Dict, Sequence
from ae.core import DEBUG_LEVEL_VERBOSE
from ae.console import ConsoleApp


APP_STATE_SECTION_NAME = 'aeAppState'


class GUIAppBase(ConsoleApp, ABC):
    """ abstract base class for to implement a GUIApp-conform app class """

    app_state_keys: Sequence = ('appVersion', )     #: app state config-variable-names/item-keys
    framework_app: Any = None                       #: app class instance of the used GUI framework
    debug_bubble: bool = False                      #: visibility of a popup/bubble showing debugging info
    info_bubble: Any = None                         #: optional DebugBubble widget

    @abstractmethod
    def get_app_state(self) -> Dict[str, Any]:
        """ determine the state of a running app and return it as dict """

    def load_app_state(self) -> str:
        """ load application state for to prepare app.run_app """
        self.debug_bubble = self.get_opt('debugLevel') >= DEBUG_LEVEL_VERBOSE

        app_state = dict()
        for key in self.app_state_keys:
            app_state[key] = self.get_var(key, section=APP_STATE_SECTION_NAME)

        return self.set_app_state(app_state)

    @abstractmethod
    def run_app(self) -> str:
        """ run application """

    def save_app_state(self) -> str:
        """ save app state in config file """
        err_msg = ""

        app_state = self.get_app_state()
        for key, state in app_state.items():
            err_msg = self.set_var(key, state, section=APP_STATE_SECTION_NAME)
            if err_msg:
                break

        return err_msg

    @abstractmethod
    def set_app_state(self, app_state: Dict[str, Any]) -> str:
        """ set/change the state of a running app """
