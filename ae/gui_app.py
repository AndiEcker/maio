"""
base class for python applications with a graphical user interface
==================================================================

The abstract base class :class:`MainAppBase` provided by this ae namespace
portion can be used for to integrate any of the available Python GUI
frameworks into the ae namespace.

The plan is to integrate the following GUI frameworks until the end of 2020:

* :mod:`Kivy <ae.kivy_app>`
* :mod:`Enaml <ae.enaml_app>`
* :mod:`Beeware <ae.beeware_app>`
* :mod:`Dabo <ae.dabo_app>`
* :mod:`QPython <ae.qpython_app>`
* :mod:`AppJar <ae.appjar_app>`

Currently available is the :mod:`Kivy <ae.kivy_app>` integration of
the :ref:`Kivy Framework <kivy.org>`.

.. note:
    In implementing the outstanding framework integrations this module will be
    extended and changed frequently.


extended console application environment
----------------------------------------

:class:`MainAppBase` inherits directly from the ae namespace class
:class:`ae console application environment class <ae.console.ConsoleApp>`.
The so inherited helper methods are useful for to configure and
control the run-time of your GUI app via command line arguments,
:ref:`config-options` and :ref:`config-files`.

.. hint:
    Please see the documentation of the :mod:`ae.console` namespace
    portion/module for more detailed information.

:class:`MainAppBase` adds on top of the :class:`~ae.console.ConsoleApp`
the concepts of :ref:`application status` and :ref:`application context`,
explained further down.


integrate new gui framework
---------------------------

For to integrate a new Python GUI framework you have to declare a
new class that inherits from :class:`MainAppBase` and implements at
least the two abstract methods :meth:`~MainAppBase.on_app_init`
and :meth:`~MainAppBase.run_app`.

Most GUI frameworks are providing an application class that need to
be initialized. For to keep a reference to the framework app class
instance within your main app class you can use the
:attr:`~MainAppBase.framework_app` attribute of :class:`MainAppBase`.

.. hint:
    The initialization of :attr:`~MainAppBase.framework_app` is optional.
    Alternatively you could also add the framework application as mixin
    to the main app class.

A typical implementation of a framework-specific main app class could
look like::

    from new_gui_framework import NewFrameworkApp

    class NewFrameworkMainApp(MainAppBase):
        def on_app_init(self):
            self.framework_app = NewFrameworkApp()

        def run_app(self):
            self.framework_app.run()

Both implementations of these abstract methods will be executed only once
at app startup. In the first executed method
:meth:`~MainAppBase.on_app_init` you could initialize
the GUI framework and prepare it for the app startup. The :meth:`~MainAppClass.run_app`
method will be called from the main module of your app project for to
start the framework app instance.


application status
------------------

Any application- and user-specific configurations like e.g. the last
window position/size, the app theme/font or the last selected context
within your app, could be included in the application status.

This namespace portion introduces the section `aeAppState` in the app
:ref:`config-files`, where any status values can be stored persistently
for to be recovered on the next startup of your application.

.. hint:
    The section name is declared by the :data:`APP_STATE_SECTION_NAME`
    constant. If you need to access this config section directly then
    please use this constant instead of the hardcoded section name.

.. _app-state-variables:

Which app state variables are finally used by your app project is (fully data-driven)
depending on the app state :ref:`config-variables` detected in all the
:ref:`config-files` that are found/available at run-time of your app.
The names of the available application state variables can be
determined with the helper function :func:`app_state_keys`.

:class:`MainBaseApp` provides optionally a user-defined font size to your application
if it detect the app state variable :attr:`~MainAppBase.font_size`. The method
:meth:`set_font_size` has to be called when the user has changed the font size
of your app.

Another two built-in app state variables are :attr:`~MainAppBase.context_id` and
:attr:`~MainAppBase.context_path` which will be explained in the next section.

The :meth:`~MainBaseApp.load_app_states` method is called on instantiation from
the implemented main app class for to load the values of all
app state variables from the :ref:`config-files`, and is then calling
:meth:~MainAppBase.setup_app_states` for pass them into their corresponding
instance attributes.

Use the main app instance attribute for to read/get the actual value of
a single app state variable. The actual values of
all app state variables as a dict is determining the method
:meth:`~MainBaseApp.retrieve_app_states` for you.

Changed app state value that need to be propagated also to the framework
app instance should be set not via the instance attribute, instead call
the method :meth:`~MainBaseApp.change_app_state` (which ensures the
propagation to any duplicated value in a (bound) framework property).

For to to save the app state to the :ref:`config-files` the implementing main app
instance has to call the method :meth:`~MainBaseApp.save_app_states` - this could be
done e.g. after the app state has changed or at least on quiting the application.


application context
-------------------

:class:`MainBaseApp` provides your application a integrated context manager,
which persists application contexts in the :ref:`config-files`.

A application context is represented by a string that defines e.g.
the action for to enter into the context, the data that gets currently displayed
and an index within the data.

The format of this context string/id can be freely defined by your application.
The app state variable :attr:`~MainAppBase.context_id` stores the current
context when the app quits for to restore it on the next app start.

The context id is initially an empty string. As soon as the user is
initiating an action your application has to call the
:meth:`~MainBaseApp.set_context` method for to change the app context.

For more complex applications you can specify a path of nested contexts.
This context path gets represented by the app state variable
:attr:`~MainAppBase.context_path`, which is a list of context strings/ids.
For to enter into a deeper/nested context you have to call the
:meth:`~MainBaseApp.context_enter` method instead of the
:meth:`~MainBaseApp.set_context` method.


application events
------------------

The helper method :meth:`~MainAppBase.call_event` can be used to support
optionally implemented event callback routines.

Internally is this method used for to fire the event `on_context_draw()`
automatically after a change of the :ref:`application context` or if
the user changed the font size.

"""
from abc import ABC, abstractmethod
from configparser import ConfigParser, NoSectionError
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
    try:    # quicker than asking before with: if cfg_parser.has_section(APP_STATE_SECTION_NAME):
        return tuple(cfg_parser.options(APP_STATE_SECTION_NAME))
    except NoSectionError:
        return tuple()


class MainAppBase(ConsoleApp, ABC):
    """ abstract base class for to implement a GUIApp-conform app class """
    # app states
    context_id: str = ""                                    #: id of the current app context (entered by the app user)
    context_path: List[str]                                 #: list of context ids, reflecting recent user actions
    font_size: float = 30.                                  #: font size used for toolbar and context screens

    # generic run-time shortcut references provided by the main app
    framework_app: Any = None                               #: app class instance of the used GUI framework
    debug_bubble: bool = False                              #: visibility of a popup/bubble showing debugging info
    info_bubble: Any = None                                 #: optional DebugBubble widget

    root_win: Any = None                                    #: app window
    root_layout: Any = None                                 #: app root layout

    def __init__(self, debug_bubble: bool = False, **console_app_kwargs):
        """ create instance of app class.

        :param debug_bubble:
        :param console_app_kwargs:
        """
        self.context_path = list()  # init for Literal type recognition - will be overwritten by setup_app_states()
        self.debug_bubble = debug_bubble
        super().__init__(**console_app_kwargs)
        self.load_app_states()
        self.on_app_init()

    # abstract methods

    @abstractmethod
    def on_app_init(self):
        """ callback to framework api for to initialize an app instance. """

    @abstractmethod
    def run_app(self) -> str:
        """ startup main and framework applications. """

    # base implementation helper methods (can be overwritten by framework portion or by user main app)

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

    def load_app_states(self):
        """ load application state for to prepare app.run_app """
        self.debug_bubble = self.get_opt('debugLevel') >= DEBUG_LEVEL_VERBOSE

        app_state = dict()
        try:            # if self._cfg_parser.has_section(APP_STATE_SECTION_NAME):
            items = self._cfg_parser.items(APP_STATE_SECTION_NAME)
            for key, state in items:
                lit = Literal(state)        # not working for str literals: , value_type=type(getattr(self, key, "")))
                app_state[key] = lit.value
        except NoSectionError:
            self.dpo(f"MainAppBase.load_app_states: ignoring missing config file section {APP_STATE_SECTION_NAME}")

        self.setup_app_states(app_state)

    @staticmethod
    def play_beep():
        """ make a short beep sound, should be overwritten by GUI framework. """
        print(chr(7), "BEEP")

    def retrieve_app_states(self) -> AppStateType:
        """ determine the state of a running app and return it as dict """
        app_state = dict()
        for key in app_state_keys(self._cfg_parser):
            app_state[key] = getattr(self, key)

        return app_state

    def save_app_states(self) -> str:
        """ save app state in config file """
        err_msg = ""

        app_state = self.retrieve_app_states()
        for key, state in app_state.items():
            err_msg = self.set_var(key, state, section=APP_STATE_SECTION_NAME)
            self.dpo(f"save_app_state {key}={state} {err_msg or 'OK'}")
            if err_msg:
                break
        self.load_cfg_files()
        return err_msg

    def set_context(self, context_id: str, redraw: bool = True):
        """ propagate change of context path and context/current id/item and display changed context.

        :param context_id:  name of new current item.
        :param redraw:      pass False to prevent to redraw the context screens.
        """
        self.dpo(f"set_context({context_id})")
        self.change_app_state('context_path', self.context_path)
        self.change_app_state('context_id', context_id)
        if redraw:
            self.call_event('on_context_draw')

    def set_font_size(self, font_size: float):
        """ change font size. """
        self.change_app_state('font_size', font_size)
        self.call_event('on_context_draw')

    def setup_app_states(self, app_state: AppStateType):
        """ put app state variables into main app instance for to prepare framework app.run_app """
        for key in app_state_keys(self._cfg_parser):
            self.change_app_state(key, app_state[key])
