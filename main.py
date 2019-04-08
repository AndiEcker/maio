# -*- coding: UTF-8 -*-
import os
import time
from functools import partial

import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.properties import BooleanProperty, DictProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.metrics import sp

kivy.require('1.9.1')                       # 1.9.1 needed for Window.softinput_mode 'below_target'
Window.softinput_mode = 'below_target'      # ensure android keyboard is not covering Popup/text input

__version__ = '0.6'

"""
  My All In One - todo list and notes (c) 2019 Andreas Ecker.

  version history:
    0.1     first beta (mini shopping list for Irma with 4 static lists Lidl/Mercadona/Nor/Sur).
    0.2     enhanced icons/texts, fixed problems with ActionBar and Popup for to edit list item, moved data to sdcard.
    0.3     changed to dynamic lists, changed data file extension to txt (for easier device maintenance),
            added app version to data file
    0.4     code clean-ups and refactoring
    0.5     switched IDE from Eric to PyCharm
    0.6     migrated to Python 3.6 and Kivy 1.11.0.dev0/master (8-04-2019).

  ToDo:
    - better handling of doubletap/tripletap
    - allow user to change order of item in list
    - refactor ActionBar (more clear, more icons, add item/list add/edit/delete menu)
    - nicer UI (from kivy.uix.effectwidget import EffectWidget, InvertEffect, HorizontalBlurEffect, VerticalBlurEffect)
    - user specific app theme (color, fonts) config screen

"""


class AppState(EventDispatcher):
    appVersion = StringProperty(__version__)
    fontSize = NumericProperty(sp(27))
    listFilterDownState = StringProperty('normal')      # show toggled/checked items
    listFilterNormalState = StringProperty('normal')    # show normal/unchecked items
    selectedListName = StringProperty('Lidl')           # default list on 1st startup
    selectedListItem = StringProperty('')
    allLists = DictProperty({'Lidl': [
                                    {'text': u'Salami', 'state': 'normal'}, 
                                    {'text': u'Maultäschle', 'state': 'down'}, 
                                    {'text': u'Quarktasche', 'state': 'normal'}, 
                                    {'text': u'Speck', 'state': 'normal'}, 
                                    {'text': u'Schoko-Erdnüsse', 'state': 'normal'}, 
                                    {'text': u'Apfelsaft', 'state': 'normal'}, 
                                    {'text': u'Gummibärle', 'state': 'normal'}, 
                                    {'text': u'Trauben-Nuss-Schokolade', 'state': 'normal'}, 
                                    {'text': u'Quark', 'state': 'normal'}, 
                                ], 
                             'Mercadona': [
                                    {'text': u'Datteln im Speckmantel', 'state': 'normal'},
                                    {'text': u'Chopped', 'state': 'normal'}, 
                                    {'text': u'Atun', 'state': 'normal'}, 
                                    {'text': u'Frischkäse', 'state': 'normal'}, 
                                    {'text': u'Gruyere', 'state': 'normal'}, 
                                    {'text': u'Emmentaler gerieben', 'state': 'normal'}, 
                                    {'text': u'Sahne', 'state': 'normal'}, 
                                    {'text': u'Bananen', 'state': 'normal'}, 
                                    {'text': u'Tomaten', 'state': 'normal'}, 
                                    {'text': u'Paprika', 'state': 'normal'}, 
                                    {'text': u'Salat', 'state': 'normal'}, 
                                    {'text': u'Zwiebeln', 'state': 'normal'}, 
                                    {'text': u'Kartoffeln', 'state': 'normal'}, 
                                    {'text': u'Äpfel', 'state': 'normal'}, 
                                ], 
                             'Nor': [
                                    {'text': u'Hundefutter', 'state': 'normal'}, 
                                    {'text': u'Teelichter', 'state': 'normal'}, 
                                ], 
                             'Sur': [
                                    {'text': u'Kopfhörer', 'state': 'down'}, 
                                    {'text': u'Jenjibre', 'state': 'normal'}, 
                                    {'text': u'Eier', 'state': 'normal'}, 
                                    {'text': u'Zitronen', 'state': 'normal'}, 
                                    {'text': u'Post', 'state': 'normal'}, 
                                    {'text': u'Blumen', 'state': 'normal'}, 
                                    {'text': u'Vanillezucker', 'state': 'normal'}, 
                                    {'text': u'Maisstärke', 'state': 'normal'}, 
                                    {'text': u'Gewürze', 'state': 'normal'}, 
                                    {'text': u'Griess', 'state': 'normal'}, 
                                    {'text': u'Dinkelbäcker', 'state': 'normal'}, 
                                ]
                             })

    def __init__(self, path, **kwargs):
        super(EventDispatcher, self).__init__(**kwargs)
        # path: platform-specific App.user_data_dir because easier maintainable and accessible in android device
        # .. located mostly at /sdcard/maio in android, ~/.config/maio in linux, $APPDATA$\maio in windows
        # .. (see App.user_data_dir in kivy docs)
        # filename: name of this class with .txt extension
        self.filename = os.path.join(path, 'AppState.txt')
    
    def load(self):
        fn = self.filename
        try:
            if not os.path.exists(fn):
                # first run after first installation: ensure databases folder and use property default values
                dn = os.path.dirname(fn)
                if not os.path.exists(dn):
                    os.makedirs(dn)
        except OSError as exc:
            print('AppState.load() prepare database directory exception',  exc)
        try:
            if os.path.exists(fn):
                with open(fn) as fp:
                    # keeps app version of first app start/install, used for data file format updates
                    self.appVersion = eval(fp.readline())
                    self.fontSize = eval(fp.readline())
                    self.listFilterDownState = eval(fp.readline())
                    self.listFilterNormalState = eval(fp.readline())
                    self.selectedListName = eval(fp.readline())
                    self.selectedListItem = eval(fp.readline())
                    self.allLists = eval(fp.read())
        except OSError as exc:
            print('AppState.load() file ', fn, 'open/read/eval exception', exc)

        # ensure data integrity, preventing app crash later on (e.g. after corrupted data file)
        if not self.allLists:
            self.allLists = {'main': [dict(text=u'first item', state='normal'), ], }
        if not self.selectedListName or self.selectedListName not in self.allLists:
            self.select_list(next(self.allLists))
        if self.selectedListItem not in self.allLists[self.selectedListName]:
            self.select_item('')

        return self
    
    def save(self):
        print('save', self.selectedListName, self.selectedListItem, self.allLists)
        if os.path.exists(self.filename):
            fn, ext = os.path.splitext(self.filename)
            fn += '_' + time.strftime('%Y%m%d%H') + ext
            if not os.path.exists(fn):
                os.rename(self.filename, fn)
        try:
            with open(self.filename, 'w') as fp:
                fp.write(repr(self.appVersion) + '\n')
                fp.write(repr(self.fontSize) + '\n')
                fp.write(repr(self.listFilterDownState) + '\n')
                fp.write(repr(self.listFilterNormalState) + '\n')
                fp.write(repr(self.selectedListName) + '\n')
                fp.write(repr(self.selectedListItem) + '\n')
                fp.write(repr(self.allLists))
        except OSError as exc:
            print('AppState.save() exception', exc)
    
    # list add/chg name/copy/del handling
    
    def add_list(self, list_name, copy_items_from=''):
        cl = list(self.allLists[copy_items_from]) if copy_items_from else []
        self.allLists[list_name] = cl
        self.select_list(list_name)
    
    def delete_list(self, list_name):
        del self.allLists[list_name]
        if self.allLists:
            self.select_list(next(self.allLists))
    
    def select_list(self, list_name):
        if self.selectedListName != list_name:
            self.select_item('')
        self.selectedListName = list_name

    # list item handling
    
    def add_item(self, item_name, item_state='normal'):
        if item_name:
            self.allLists[self.selectedListName].append(dict(text=item_name, state=item_state))
            self.select_item(item_name)
    
    def change_item(self, item_name, text=None, state=None):
        li = self.find_item(item_name)
        if text is not None:
            li['text'] = text
            item_name = text
        if state is not None:
            li['state'] = state
        self.select_item(item_name)
    
    def change_list_filter(self, filter_name, filter_state):
        if filter_name == 'normal':
            self.listFilterNormalState = filter_state
        elif filter_name == 'down':
            self.listFilterDownState = filter_state
    
    def delete_item(self, item_name):
        li = self.find_item(item_name)
        self.allLists[self.selectedListName].remove(li)
        self.select_item('')
    
    def find_item(self, item_name):
        li = self.allLists[self.selectedListName]
        for i in range(len(li)):
            if li[i]['text'] == item_name:
                return li[i]
    
    def select_item(self, item_name):
        self.selectedListItem = item_name


class MaioApp(App):
    """ app class
    """
    title = 'My All In One'
    icon = 'img/app_icon.png'
    version = __version__
    toggleButtonInk = (0.69, 1.0, 0.39, 0.18)
    buttonInk = (0.39, 0.39, 0.39, 0.18)

    landscape = BooleanProperty()
    
    data = ObjectProperty()

    _edit_list_name = ''            # list name to be initially edited ('' on add new list)
    _copy_items_from = ''           # list name of source list for list copy

    _currentListItem = None         # ListItem widget used for to add a new or edit a list item

    _multiTap = 0                   # used for listTouchDownHandler
    _lastTouchStartCallback = {}

    # screen switching/refreshing

    def switch_to_lists_view(self):
        self.root.ids.actionBar.add_widget(Factory.ListsView())
        self.refresh_names_list()

    def switch_to_items_view(self):
        self.create_list_sel_buttons()
        self.refresh_items_list()

    # list names

    def delete_list_name(self, list_name):
        Factory.DeleteConfirmPopup(ok_callback=partial(self.data.delete_list, list_name)).popup()

    def list_name_edit_start(self, list_name='', copy_items_from=''):  # start/initiate the edit of a list name
        self._edit_list_name = list_name
        self._copy_items_from = copy_items_from
        self.data.select_item('')
        pu = Factory.ListNameEditor(title=list_name)
        pu.open()  # calling self._currentListName on dismiss/close

    def list_name_edit_finished(self, list_name):   # dismiss call back for new, copy and edit list name
        print('list_name_edit_finished - new list name=', list_name)
        if list_name not in self.data.allLists:
            if self._copy_items_from:
                self.data.add_list(list_name, self._copy_items_from)
            elif self._edit_list_name:                          # user edited list name
                self.data.add_list(list_name, self._edit_list_name)
                self.data.delete_list(self._edit_list_name)
            else:                                               # user added new list name (with text)
                self.data.add_list(list_name)
            self.data.save()
            self.switch_to_lists_view()                         # refresh screen

    def refresh_names_list(self):
        lcw = self.root.ids.listContainer
        lcw.clear_widgets()
        h = 0
        for li in self.data.allLists.keys():
            liw = Factory.ListName(text=li)
            lcw.add_widget(liw)
            h += liw.height
        lcw.height = h

        # ensure that selectedListItem is visible - if still exists in current list ?!?!?
        if self.data.selectedListName in self.data.allLists:
            pass

    # list items handling
    
    def add_list_item(self, item_name, wid):      # finish the addition of a new list item
        self.data.add_item(item_name)
        lc = self.root.ids.listContainer
        wid.text = item_name
        lc.add_widget(wid)
        lc.height += wid.height
    
    def add_new_list_item(self):                   # start/initiate the addition of a new list item
        self.data.select_item('')
        self._currentListItem = Factory.ListItem()
        pu = Factory.ListItemEditor(title='')
        pu.open()       # calling self._currentListItem on dismiss/close

    def create_list_sel_buttons(self):
        lc = self.root.ids.actionBar.ids.listSelActionGroup
        lc.clear_widgets()
        for list_name in self.data.allLists.keys():
            wid = Factory.ListSelButton(text=list_name)
            lc.add_widget(wid)
            lc.width += wid.width

    def delete_list_item(self, item_name):
        if item_name:
            lc = self.root.ids.listContainer
            for li in lc.children:
                if li.text == item_name:
                    self.data.delete_item(li.text)
                    lc.height -= li.height
                    lc.remove_widget(li)
                    break
    
    def edit_list_item(self, item_name, *_):
        self.data.select_item(item_name)
        lc = self.root.ids.listContainer
        for li in lc.children:
            if li.text == item_name:
                self._currentListItem = li
                pu = Factory.ListItemEditor(title=li.text)
                pu.open()       # calling list_item_edit_finished() on dismiss/close
                break
    
    # long touch detection and double/triple tap event handlers for lists (only called if list is not empty)
    def items_list_touch_down_handler(self, list_item_name, touch):
        print('listTouchDownHandler', list_item_name, touch)
        if touch.is_double_tap:
            self._multiTap = 1
            return
        elif touch.is_triple_tap:
            self._multiTap = -2  # -2 because couldn't prevent the double tap action before/on triple tap
            return
        lc = self.root.ids.listContainer
        local_touch_pos = lc.to_local(touch.x, touch.y)
        print('..local', local_touch_pos)
        for wid in lc.children:
            print('...widget', wid.text, wid.pos)
            if wid.collide_point(*local_touch_pos) and wid.text == list_item_name:
                print('....found', list_item_name)
                self._lastTouchStartCallback[list_item_name] = partial(self.edit_list_item, list_item_name)
                Clock.schedule_once(self._lastTouchStartCallback[list_item_name], 1.8)        # edit item text
    
    def items_list_touch_up_handler(self, list_item_name, touch):
        print('listTouchUpHandler', list_item_name, touch)
        if list_item_name in self._lastTouchStartCallback:
            Clock.unschedule(self._lastTouchStartCallback[list_item_name])
        if self._multiTap:
            # double/triple click allows to in-/decrease the list item font size
            self.data.fontSize += sp(3) * self._multiTap
            self.refresh_items_list()
            self._multiTap = 0

    def list_item_edit_finished(self, text):
        print('list_item_edit_finished', text)
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
        self.data.save()
        self._currentListItem = None  # release ref created by add_new_list_item()/edit_list_item()

    def refresh_items_list(self):
        lcw = self.root.ids.listContainer
        lcw.clear_widgets()
        lf_ds = self.root.ids.actionBar.ids.listFilterDown.state == 'normal'
        lf_ns = self.root.ids.actionBar.ids.listFilterNormal.state == 'normal'
        h = 0
        for li in self.data.allLists[self.data.selectedListName]:
            if lf_ds and li['state'] == 'down' or lf_ns and li['state'] == 'normal':
                liw = Factory.ListItem(**li)  # text = li['text'], state = li['state']
                lcw.add_widget(liw)
                h += liw.height
        lcw.height = h
        
        # ensure that selectedListItem is visible - if still exists in current list ?!?!?
        if self.data.selectedListItem in self.data.allLists[self.data.selectedListName]:
            pass

    def select_items_list(self, list_name):
        print('select_list', list_name)
        self.data.save()
        self.data.select_list(list_name)
        self.refresh_items_list()

    def toggle_list_filter(self, filter_name, filter_state):
        print('toggle_list_filter', filter_name, 'down' if filter_name == 'B' else 'normal', filter_state)
        self.data.change_list_filter('down' if filter_name == 'B' else 'normal', filter_state)
        self.refresh_items_list()
    
    def toggle_list_item(self, item_name, state):
        print('toggle_list_item', item_name, state)
        self.data.change_item(item_name, state=state)
        self.data.save()
        if self.data.listFilterDownState == 'down' or self.data.listFilterNormalState == 'down':
            self.refresh_items_list()      # refresh only needed if one filter is active

    # App class methods

    def build(self):
        print('App.build(), user_data_dir', self.user_data_dir)
        self.data = AppState(self.user_data_dir).load()
        self.root = Factory.MaioRoot()
        self.create_list_sel_buttons()
        self.refresh_items_list()
        Window.bind(on_resize=self.screen_size_changed)
        return self.root

    def screen_size_changed(self, *_):  # screen resize handler
        self.landscape = self.root.width >= self.root.height

    def on_start(self):
        self.screen_size_changed()  # init. app./self.landscape (on app startup and after build)

    def on_pause(self):
        self.data.save()
        return True

    def on_stop(self):
        self.data.save()


# app start
if __name__ in ('__android__', '__main__'):
    MaioApp().run()
