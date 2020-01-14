""" Base class for applications with a graphical user interface """
import os
from typing import Any
from ae.core import DEBUG_LEVEL_VERBOSE
from ae.console import ConsoleApp


APP_STATE_FILE_PATH = "AppState.txt"


class GUIAppBase(ConsoleApp):
    """ base class for to implement a GUIApp-conform app class """

    user_data_dir: str = "."        #: folder path for to store user app data/state
    app_state_file_path: str        #: app state data file path
    framework_app: Any = None       #: app class instance of the kivy framework
    debug_bubble: bool = False      #: visibility of a popup/bubble showing debugging info
    info_bubble: Any = None         #: optional DebugBubble widget

    def load_app_state(self) -> bool:
        """ load application state for to prepare app.run_app """
        self.debug_bubble = self.get_opt('debugLevel') >= DEBUG_LEVEL_VERBOSE

        self.app_state_file_path = os.path.join(self.user_data_dir, APP_STATE_FILE_PATH)

        return True

    def run_app(self):
        """ run application """
        assert self.framework_app, "Missing framework app instance - has to be set before calling run_app()"

        raise NotImplementedError("run_app() method has to be implemented by the class inheriting from GUIAppBase"
                                  ", which is encapsulating the used GUI framework")

    def save_app_state(self):
        """ save app state in user data dir """
