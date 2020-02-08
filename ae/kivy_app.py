""" GUIApp-conform Kivy app """
import os
from typing import Optional, TextIO

import kivy                                                             # type: ignore
from kivy.app import App                                                # type: ignore
from kivy.core.window import Window                                     # type: ignore
from kivy.factory import Factory                                        # type: ignore
from kivy.properties import BooleanProperty, DictProperty               # type: ignore
from kivy.clock import Clock                                            # type: ignore
from kivy.metrics import sp                                             # type: ignore
from kivy.lang import Builder                                           # type: ignore

from ae.gui_app import MainAppBase

kivy.require('1.9.1')  # currently using 1.11.1 but at least 1.9.1 is needed for Window.softinput_mode 'below_target'
# Window.softinput_mode = 'below_target'  # ensure android keyboard is not covering Popup/text input


MIN_FONT_SIZE = sp(21)
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

    landscape = BooleanProperty()           #: True if app window width is bigger than the app window height, else False
    app_state = DictProperty()              #: duplicate of MainAppBase app state attributes for events/binds

    # kivy App class methods and callbacks

    def __init__(self, main_app: 'KivyMainApp', **kwargs):
        """ init kivy app """
        self.main_app = main_app
        self.title = main_app.app_title                     #: set kivy.app.App.title
        self.icon = os.path.join("img", "app_icon.png")     #: set kivy.app.App.icon

        super().__init__(**kwargs)

    def build(self):
        """ build app """
        self.main_app.po('App.build(), user_data_dir', self.user_data_dir,
                         "config files", getattr(self.main_app, '_cfg_files'))
        Window.bind(on_resize=self.win_pos_size_changed,
                    left=self.win_pos_size_changed,
                    top=self.win_pos_size_changed,
                    on_key_down=self.on_key_down,
                    on_key_up=self.on_key_up)

        return Factory.MaioRoot()

    def on_key_down(self, keyboard, key_code, _scan_code, key_text, modifiers):
        """ key press event. """
        return self.main_app.call_event('on_key_press',
                                        key_text or keyboard.command_keys.get(key_code, key_code),
                                        modifiers)

    def on_key_up(self, keyboard, key_code, _scan_code):
        """ key release event. """
        return self.main_app.call_event('on_key_release', keyboard.command_keys.get(key_code, key_code))

    def on_start(self):
        """ app start event """
        self.win_pos_size_changed()  # init. app./self.landscape (on app startup and after build)
        self.main_app.root_layout = self.root
        self.main_app.root_win = self.root.parent
        self.main_app.call_event('on_app_start')

    def on_pause(self):
        """ app pause event """
        self.main_app.save_app_states()
        self.main_app.call_event('on_app_pause')
        return True

    def on_stop(self):
        """ quit app event """
        self.main_app.save_app_states()
        self.main_app.call_event('on_app_stop')

    def win_pos_size_changed(self, *_):
        """ screen resize handler """
        win_pos_size = (Window.left, Window.top, Window.width, Window.height)
        self.landscape = self.root.width >= self.root.height
        self.main_app.po('win_pos_size_changed', self.landscape, *win_pos_size)
        self.main_app.change_app_state('win_rectangle', win_pos_size)
        self.main_app.call_event('on_win_pos_size')


class KivyMainApp(MainAppBase):
    """ Kivy application """
    win_rectangle: tuple = (0, 0, 800, 600)                 #: window coordinates app state variable

    def on_app_init(self):
        """ initialize framework app instance """
        win_rect = self.win_rectangle
        if win_rect:
            Window.left, Window.top = win_rect[:2]
            Window.size = win_rect[2:]

        self.framework_app = FrameworkApp(self)
        self.framework_app.kv_file = 'main.kv'

        self.framework_app.app_state.update(self.retrieve_app_states())  # copy app states to duplicate DictProperty

    def run_app(self):
        """ startup/display the application """
        if self.debug_bubble:
            Builder.load_string(DEBUG_BUBBLE_DEF)

        self.framework_app.app_state = self.retrieve_app_states()

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
