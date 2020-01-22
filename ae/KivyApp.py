""" GUIApp-conform Kivy app """
import os
from typing import Any, Dict, Optional, TextIO

from ae.GUIApp import GUIAppBase

import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.properties import BooleanProperty, DictProperty
from kivy.clock import Clock
from kivy.metrics import sp
from kivy.lang import Builder

kivy.require('1.11.1')  # currently using 1.11.1 but at least 1.9.1 is needed for Window.softinput_mode 'below_target'
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


class FrameworkAppClass(App):
    """ framework app class """

    landscape = BooleanProperty()
    app_state = DictProperty()

    # kivy App class methods and callbacks

    def __init__(self, gui_app: 'KivyApp', **kwargs):
        """ init kivy app """
        self.gui_app = gui_app
        self.title = gui_app.app_title                      #: set kivy.app.App.title
        self.icon = os.path.join("img", "app_icon.png")     #: set kivy.app.App.icon

        super().__init__(**kwargs)

    def build(self):
        """ build app """
        self.gui_app.po('App.build(), user_data_dir', self.user_data_dir,
                        "config files", getattr(self.gui_app, '_cfg_files'))
        Window.bind(on_resize=self.screen_size_changed)
        return Factory.MaioRoot()

    def screen_size_changed(self, *_):
        """ screen resize handler """
        self.gui_app.po('screen_size_changed', self.root.width, self.root.height)
        self.landscape = self.root.width >= self.root.height

    def on_start(self):
        """ app start event """
        self.screen_size_changed()  # init. app./self.landscape (on app startup and after build)
        display_callback = getattr(self.gui_app, 'on_draw_gui', None)
        if display_callback:
            display_callback()

    def on_pause(self):
        """ app pause event """
        self.gui_app.save_app_state()
        return True

    def on_stop(self):
        """ quit app event """
        self.gui_app.save_app_state()


class KivyApp(GUIAppBase):
    """ Kivy application """
    def change_app_state(self, state_name, new_value):
        """ change single app state item to value in self.attribute and app_state dict item """
        setattr(self, state_name, new_value)
        self.framework_app.app_state[state_name] = new_value

    def set_app_state(self, app_state: Dict[str, Any]) -> str:
        """ set/change the state of a running app, called for to prepare app.run_app """
        err_msg = super().set_app_state(app_state)
        if not err_msg:
            win_rect = app_state['win_rectangle']
            if win_rect:
                Window.left, Window.top = win_rect[:2]
                Window.size = win_rect[2:]

        return err_msg

    def on_init_app(self):
        """ initialize framework app instance """
        self.framework_app = FrameworkAppClass(self)
        self.framework_app.kv_file = 'main.kv'
        self.font_size = MIN_FONT_SIZE                  #: font size used for toolbar and leafs
        self.win_rectangle = (sp(90), sp(90), sp(800), sp(600))   #: (x, y, width, height) of the app window

    def run_app(self):
        """ startup/display the application """
        if self.debug_bubble:
            Builder.load_string(DEBUG_BUBBLE_DEF)
        self.framework_app.app_state = self.get_app_state()
        self.framework_app.run()

    def show_bubble(self, *objects, file: Optional[TextIO] = None, **kwargs):
        """ show popup bubble - compatible to Python print() and AppBase.print_out() """
        if not self.info_bubble:
            self.info_bubble = Factory.DebugBubble()
        self.info_bubble.message = " ".join([repr(message) for message in objects])
        if not self.info_bubble.parent:  # Check if bubble is not already on screen
            Window.add_widget(self.info_bubble)
        Clock.schedule_once(lambda dt: Window.remove_widget(self.info_bubble), 9)  # Remove bubble after some seconds
        self.po(*objects, file=file, **kwargs)
