# -*- coding: UTF-8 -*-
""" My All In One - (c) 2020 Andi Ecker.

  version history:
    0.1     first beta (mini shopping list for Irma with 4 static lists Lidl/Mercadona/Nor/Sur).
    0.2     enhanced icons/texts, fixed problems with ActionBar and Popup for to edit list item, moved data to sdcard.
    0.3     changed to dynamic lists, changed data file extension to txt (for easier device maintenance),
            added app version to data file
    0.4     code clean-ups and refactoring
    0.5     switched IDE from Eric to PyCharm
    0.6     migrated to Python 3.6 and Kivy 1.11.0.dev0/master (8-04-2019).
    0.7     code clean-up, raised min-sdk to default 21 (was 18) and commented out fullscreen = 0 (30-06-2019).
    0.8     prevent fontSize to get too small after triple-touch, for to be double-touchable for to increase.
    0.9     pep008 refactoring.
    0.10    started moving add/delete from ActionBar into menu and floating buttons.
    0.11    extended/corrected list items to the ones in Irmi's mobile phone, fixed bugs, added DEBUG_BUBBLE.
    0.12    refactoring of UI (migrate to KivyApp) and data structure (allow list in list).
  ToDo:
    - better handling of doubletap/tripletap
    - allow user to change order of item in list
    - nicer UI (from kivy.uix.effectwidget import EffectWidget, InvertEffect, HorizontalBlurEffect, VerticalBlurEffect)
    - user specific app theme (color, fonts) config screen

"""
import os
import time
from functools import partial

from ae.KivyApp import KivyApp as GUIApp


__version__ = '0.12'


MIN_FONT_SIZE = sp(24)
MAX_FONT_SIZE = sp(33)


class AppState(EventDispatcher):
    """ application state control """
    app_version = StringProperty(__version__)
    font_size = NumericProperty(MIN_FONT_SIZE)              # font size of list items/names
    filter_selected = StringProperty('normal')       # show toggled/checked items
    filter_unselected = StringProperty('normal')     # show normal/unchecked items
    selected_list_name = StringProperty()                   # default list on 1st startup (NOW is app_context)
    selected_list_item = StringProperty()
    all_lists = DictProperty()

    def __init__(self, path, **kwargs):
        super(EventDispatcher, self).__init__(**kwargs)
        # path: platform-specific App.user_data_dir because easier maintainable and accessible in android device
        # .. located mostly at /sdcard/maio in android, ~/.config/maio in linux, $APPDATA$\maio in windows
        # .. (see App.user_data_dir in kivy docs)
        # filename: name of this class with .txt extension
        self.filename = os.path.join(path, 'AppState.txt')

    def load(self):
        """ load_app_state app state """
        fn = self.filename
        try:
            if not os.path.exists(fn):
                # first run after first installation: ensure databases folder and use property default values
                dn = os.path.dirname(fn)
                if not os.path.exists(dn):
                    os.makedirs(dn)
        except OSError as exc:
            dprint('AppState.load_app_state() prepare database directory exception', exc)
        try:
            if os.path.exists(fn):
                with open(fn) as fp:
                    # keeps app version of first app start/install, used for data file format updates
                    self.app_version = eval(fp.readline())
                    self.font_size = min(max(MIN_FONT_SIZE, eval(fp.readline())), MAX_FONT_SIZE)
                    self.filter_selected = eval(fp.readline())
                    self.filter_unselected = eval(fp.readline())
                    self.selected_list_name = eval(fp.readline())
                    self.selected_list_item = eval(fp.readline())
                    self.all_lists = eval(fp.read())
        except OSError as exc:
            dprint('AppState.load_app_state() file ', fn, 'open/read/eval exception', exc)

        # ensure data integrity, preventing app crash later on (e.g. after corrupted data file)
        if not self.selected_list_name or self.selected_list_name not in self.all_lists:
            self.select_list()
        if self.selected_list_item not in self.all_lists[self.selected_list_name]:
            self.select_item('')

        return self

    def save(self):
        """ save_app_state app state """
        dprint('save_app_state', self.selected_list_name, self.selected_list_item, self.all_lists)
        if os.path.exists(self.filename):
            fn, ext = os.path.splitext(self.filename)
            fn += '_' + time.strftime('%Y%m%d%H') + ext
            if not os.path.exists(fn):
                os.rename(self.filename, fn)
        try:
            with open(self.filename, 'w') as fp:
                fp.write(repr(self.app_version) + '\n')
                fp.write(repr(self.font_size) + '\n')
                fp.write(repr(self.filter_selected) + '\n')
                fp.write(repr(self.filter_unselected) + '\n')
                fp.write(repr(self.selected_list_name) + '\n')
                fp.write(repr(self.selected_list_item) + '\n')
                fp.write(repr(self.all_lists))
        except OSError as exc:
            dprint('AppState.save_app_state() exception', exc)

    # list add/chg name/copy/del handling

    def add_list(self, list_name, copy_items_from=''):
        """ add new list """
        cl = list(self.all_lists[copy_items_from]) if copy_items_from else []
        self.all_lists[list_name] = cl
        self.select_list(list_name)

    def delete_list(self, list_name):
        """ delete existing list """
        del self.all_lists[list_name]
        self.select_list()

    def select_list(self, list_name=None):
        """ select a list """
        if not self.all_lists:
            self.all_lists = {'main': [dict(text='first item', state='normal'), ], }
        if list_name is None:
            list_name = next(iter(self.all_lists))
        if self.selected_list_name != list_name:
            self.select_item('')
            self.selected_list_name = list_name

    # list item handling

    def add_item(self, item_name, item_state='normal'):
        """ add item to list """
        if item_name:
            self.all_lists[self.selected_list_name].append(dict(text=item_name, state=item_state))
            self.select_item(item_name)

    def change_item(self, item_name, text=None, state=None):
        """ change list item """
        li = self.find_item(item_name)
        if text is not None:
            li['text'] = text
            item_name = text
        if state is not None:
            li['state'] = state
        self.select_item(item_name)

    def change_list_filter(self, filter_name, filter_state):
        """ change list filter """
        if filter_name == 'normal':
            self.filter_unselected = filter_state
        elif filter_name == 'down':
            self.filter_selected = filter_state

    def delete_item(self, item_name):
        """ delete list item """
        li = self.find_item(item_name)
        self.all_lists[self.selected_list_name].remove(li)
        self.select_item('')

    def find_item(self, item_name):
        """ find list item """
        li = self.all_lists[self.selected_list_name]
        for i in range(len(li)):
            if li[i]['text'] == item_name:
                return li[i]

    def select_item(self, item_name):
        """ select list item """
        self.selected_list_item = item_name


class MaioApp(GUIApp):
    """ app class """
    # screen switching/refreshing

    def switch_to_items_view(self):
        """ switch screen to list items view """
        self.root.ids.menuBar.add_widget(Factory.ItemsView())
        self.refresh_names_list()

    # list names

    @staticmethod
    def delete_list_name(list_name):
        """ delete list """
        pu = Factory.ConfirmListDeletePopup()
        pu.what = list_name
        pu.open()

    def delete_list_confirmed(self, list_name):
        """ delete list confirmation callback """
        self.data.delete_list(list_name)
        self.data.save_app_state()
        self.refresh_names_list()

    def list_name_edit_start(self, list_name='', copy_items_from=''):
        """ start/initiate the edit of a list name """
        self._edit_list_name = list_name
        self._copy_items_from = copy_items_from
        self.data.select_item('')
        pu = Factory.ListNameEditor(title=list_name)
        pu.open()  # calling self._currentListName on dismiss/close

    def list_name_edit_finished(self, list_name):
        """ dismiss call back for new, copy and edit list name """
        dprint('list_name_edit_finished - new list name=', list_name)
        if list_name not in self.data.all_lists:
            if self._copy_items_from:
                self.data.add_list(list_name, self._copy_items_from)
            elif self._edit_list_name:  # user edited list name
                self.data.add_list(list_name, self._edit_list_name)
                self.data.delete_list(self._edit_list_name)
            else:  # user added new list name (with text)
                self.data.add_list(list_name)
            self.data.save_app_state()
            self.refresh_names_list()  # refresh screen

    def refresh_names_list(self):
        """ refresh names list """
        lcw = self.root.ids.listContainer
        lcw.clear_widgets()
        h = 0
        for li in self.data.all_lists.keys():
            liw = Factory.ListName()
            liw.text = li
            lcw.add_widget(liw)
            h += liw.height
        lcw.height = h

        # ensure that selected_list_item is visible - if still exists in current list ?!?!?
        if self.data.selected_list_name in self.data.all_lists:
            pass

    # list items

    def add_list_item(self, item_name, wid):
        """ finish the addition of a new list item """
        self.data.add_item(item_name)
        lcw = self.root.ids.listContainer
        wid.text = item_name
        lcw.add_widget(wid)
        lcw.height += wid.height

    def add_new_list_item(self):
        """ start/initiate the addition of a new list item """
        self.data.select_item('')
        self._currentListItem = Factory.ListItem()
        pu = Factory.ListItemEditor(title='')
        pu.open()  # calling self._currentListItem on dismiss/close

    def delete_list_item(self, item_name):
        """ delete list item """
        if item_name:
            lcw = self.root.ids.listContainer
            for li in lcw.children:
                if li.text == item_name:
                    self.data.delete_item(li.text)
                    lcw.height -= li.height
                    lcw.remove_widget(li)
                    break

    def edit_list_item(self, item_name, *_):
        """ edit list item """
        self.data.select_item(item_name)
        lcw = self.root.ids.listContainer
        for li in lcw.children:
            if li.text == item_name:
                self._currentListItem = li
                pu = Factory.ListItemEditor(title=li.text)
                pu.open()  # calling list_item_edit_finished() on dismiss/close
                break

    def items_list_touch_down_handler(self, list_item_name, touch):
        """ long touch detection and double/triple tap event handlers for lists (only called if list is not empty) """
        dprint('listTouchDownHandler', list_item_name, touch)
        if touch.is_double_tap:
            self._multi_tap = 1
            return
        elif touch.is_triple_tap:
            self._multi_tap = -2  # -2 because couldn't prevent the double tap before/on triple tap
            return
        lcw = self.root.ids.listContainer
        local_touch_pos = lcw.to_local(touch.x, touch.y)
        dprint('..local', local_touch_pos)
        for wid in lcw.children:
            dprint('...widget', wid.text, wid.pos)
            if wid.collide_point(*local_touch_pos) and wid.text == list_item_name:
                dprint('....found', list_item_name)
                self._last_touch_start_callback[list_item_name] = partial(self.edit_list_item, list_item_name)
                Clock.schedule_once(self._last_touch_start_callback[list_item_name], 1.8)  # edit item text

    def items_list_touch_up_handler(self, list_item_name, touch):
        """ touch up detection and multi-tap event handlers for lists """
        dprint('listTouchUpHandler', list_item_name, touch)
        if list_item_name in self._last_touch_start_callback:
            Clock.unschedule(self._last_touch_start_callback[list_item_name])
        if self._multi_tap:
            # double/triple click allows to in-/decrease the list item font size
            dprint(f"FONT SIZE CHANGE from {self.data.font_size} to {self.data.font_size + sp(3) * self._multi_tap}")
            self.data.font_size += sp(3) * self._multi_tap
            if self.data.font_size < MIN_FONT_SIZE:
                self.data.font_size = MIN_FONT_SIZE
                dprint(f"   .. CORRECTED to MIN={self.data.font_size}")
            elif self.data.font_size > MAX_FONT_SIZE:
                self.data.font_size = MAX_FONT_SIZE
                dprint(f"   .. CORRECTED to MAX={self.data.font_size}")
            self.refresh_items_list()
            self._multi_tap = 0

    def list_item_edit_finished(self, text):
        """ finished list edit callback """
        dprint('list_item_edit_finished', text)
        remove_item = (text is None or text == '')
        new_item = (self._currentListItem.text == '')  # or use: self.data.select_item == ''
        if remove_item and new_item:  # user cancelled newly created but still not added list item
            pass
        elif remove_item:  # user cleared text of existing list item
            self.delete_list_item(self._currentListItem.text)
        elif new_item:  # user added new list item (with text)
            self.add_list_item(text, self._currentListItem)
        else:  # user edited list item
            self.data.change_item(self._currentListItem.text, text)
            self._currentListItem.text = text
        self.data.save_app_state()
        self._currentListItem = None  # release ref created by add_new_list_item()/edit_list_item()

    def refresh_items_list(self):
        """ refresh lists """
        lcw = self.root.ids.listContainer
        lcw.clear_widgets()
        lf_ds = self.root.ids.menuBar.ids.listFilterDown.state == 'normal'
        lf_ns = self.root.ids.menuBar.ids.listFilterNormal.state == 'normal'
        h = 0
        for liw in self.data.all_lists[self.data.selected_list_name]:
            if lf_ds and liw['state'] == 'down' or lf_ns and liw['state'] == 'normal':
                liw = Factory.ListItem(**liw)
                lcw.add_widget(liw)
                h += liw.height
        lcw.height = h

        # ensure that selected_list_item is visible - if still exists in current list
        if self.data.selected_list_item in self.data.all_lists[self.data.selected_list_name]:
            pass

    def select_items_list(self, list_name):
        """ select list """
        dprint('select_list', list_name)
        self.data.save_app_state()
        self.data.select_list(list_name)
        self.refresh_items_list()

    def toggle_list_filter(self, filter_name, filter_state):
        """ list item filter """
        dprint('toggle_list_filter', filter_name, 'down' if filter_name == 'B' else 'normal', filter_state)
        self.data.change_list_filter('down' if filter_name == 'B' else 'normal', filter_state)
        self.refresh_items_list()

    def toggle_list_item(self, item_name, state):
        """ toggle list item """
        dprint('toggle_list_item', item_name, state)
        self.data.change_item(item_name, state=state)
        self.data.save_app_state()
        if self.data.filter_selected or self.data.filter_unselected:
            self.refresh_items_list()  # refresh only needed if one filter is active


# app start
if __name__ in ('__android__', '__main__'):
    MaioApp().run_app()
