""" GUIApp-conform Kivy app """
from typing import Any, Dict, Optional, Sequence, TextIO

from ae.GUIApp import GUIAppBase

import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.clock import Clock
from kivy.metrics import sp
from kivy.lang import Builder

kivy.require('1.9.1')  # currently using 1.11.1 but at least 1.9.1 is needed for Window.softinput_mode 'below_target'
Window.softinput_mode = 'below_target'  # ensure android keyboard is not covering Popup/text input


MIN_FONT_SIZE = sp(24)
MAX_FONT_SIZE = sp(33)


# adapted from: https://stackoverflow.com/questions/23055696
#    /see-output-of-print-statements-on-android-using-kivy-kivy-launcher
DEBUG_BUBBLE_DEF = '''
<DebugBubble@Bubble>
    message: 'empty message'
    size_hint: None, None
    show_arrow: False
    pos_hint: {'top': 1, 'right': 1}
    size: sp(600), lbl.texture_size[1] + sp(30)
    Label:
        id: lbl
        text: root.message
        # constraint text to be displayed within the bubble width and have it be unrestricted on the height
        text_size: root.width - sp(30), None
'''


class FrameworkApp(App):
    """ framework app class """
    title = 'My All In One'
    icon = 'img/app_icon.png'
    toggled_item_ink = (0.69, 1.0, 0.39, 0.18)
    normal_item_ink = (0.39, 0.39, 0.39, 0.18)

    landscape = BooleanProperty()

    data = ObjectProperty()

    _edit_list_name = ''  # list name to be initially edited ('' on add new list)
    _copy_items_from = ''  # list name of source list for list copy

    _currentListItem = None  # ListItem widget used for to add a new or edit a list item

    _multi_tap = 0  # used for listTouchDownHandler
    _last_touch_start_callback = dict()

    # kivy App class methods and callbacks

    def __init__(self, gui_app: 'KivyApp', **kwargs):
        """ init kivy app """
        self.gui_app = gui_app
        super().__init__(**kwargs)

    def build(self):
        """ build app """
        self.gui_app.print_out('App.build(), user_data_dir', self.user_data_dir)
        self.data = self.gui_app.app_state
        Window.bind(on_resize=self.screen_size_changed)
        self.root = Factory.MaioRoot()
        return self.root

    def screen_size_changed(self, *_):
        """ screen resize handler """
        self.gui_app.print_out('screen_size_changed', self.root.width, self.root.height)
        self.landscape = self.root.width >= self.root.height

    def on_start(self):
        """ app start event """
        self.screen_size_changed()  # init. app./self.landscape (on app startup and after build)

    def on_pause(self):
        """ app pause event """
        self.gui_app.save_app_state()
        return True

    def on_stop(self):
        """ quit app event """
        self.gui_app.save_app_state()


class KivyApp(GUIAppBase):
    """ Kivy application """

    font_size: float = MIN_FONT_SIZE                    #: font size used for toolbar and list items
    win_rectangle: Sequence = (0, 0, sp(800), sp(600))  #: (x, y, width, height) of the app window

    def get_app_state(self) -> Dict[str, Any]:
        """ determine state of running Kivy app """
        app_state = dict()
        app_state['fontSize'] = self.font_size

        return app_state

    def run_app(self):
        """ startup/display the application """
        if self.debug_bubble:
            Builder.load_string(DEBUG_BUBBLE_DEF)

    def set_app_state(self, app_state: Dict[str, Any]) -> str:
        """ set/change the state of a running app, called for to prepare app.run_app """
        if 'fontSize' not in self.app_state_keys:
            self.app_state_keys += ('fontSize', 'winRectangle', )
        self.framework_app = FrameworkApp(self)

        self.font_size = app_state['fontSize']
        win_rect = app_state['winRectangle']
        if win_rect:
            pos_x, pos_y, width, height = win_rect
            self.framework_app.window

        return ""

    def show_bubble(self, *objects, file: Optional[TextIO] = None, **kwargs):
        """ show popup bubble - compatible to Python print() and AppBase.print_out() """
        if not self.info_bubble:
            self.info_bubble = Factory.DebugBubble()
        self.info_bubble.message = " ".join([repr(message) for message in objects])
        if not self.info_bubble.parent:  # Check if bubble is not already on screen
            Window.add_widget(self.info_bubble)
        Clock.schedule_once(lambda dt: Window.remove_widget(self.info_bubble), 9)  # Remove bubble after some seconds
        self.print_out(*objects, file=file, **kwargs)
