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
    0.8     prevent font size to get too small after triple-touch, for to be double-touchable for to increase.
    0.9     pep008 refactoring.
    0.10    started moving add/delete from ActionBar into menu and floating buttons.
    0.11    extended/corrected leafs to the ones in Irmi's mobile phone, fixed bugs, added DEBUG_BUBBLE.
    0.12    big refactoring of UI (migrate to KivyApp) and data structure (allow list in list).
  ToDo:
    - better handling of doubletap/tripletap
    - allow user to change order of item in list
    - nicer UI (from kivy.uix.effectwidget import EffectWidget, InvertEffect, HorizontalBlurEffect, VerticalBlurEffect)
    - user specific app theme (color, fonts) config screen

"""
from copy import deepcopy
from functools import partial
from typing import Any, Dict, List, Optional

from kivy.clock import Clock
from kivy.factory import Factory
from kivy.metrics import sp
from kivy.uix.widget import Widget
from kivy.core.window import Window

from ae.KivyApp import MIN_FONT_SIZE, MAX_FONT_SIZE, KivyApp


__version__ = '0.12'

ItemDataType = Dict[str, Any]
ListDataType = List[ItemDataType]


class MaioApp(KivyApp):
    """ app class """
    filter_selected: bool = True            #: True for to hide selected leafs
    filter_unselected: bool = True          #: True for to hide unselected leafs
    data_tree: ListDataType = list()        #: app data
    data_path: List[str] = list()   #: list of sub-list names, selected by user - last item can be a leaf name
    current_item: str = ""                  #: name of the currently/last by the user touched list item (sub-list/leaf]

    _edit_list_name: str = ''               #: list name to be initially edited ('' on add new list)
    _copy_items_from: str = ''              #: list name of source list for list copy
    _current_list: ListDataType = list()    #: currently displayed sub-list
    _current_widget: Optional[Widget] = None          #: widget used for to add a new or edit a list item
    _multi_tap: int = 0                     #: used for listTouchDownHandler
    _last_touch_start_callback: Dict = dict()

    # app init

    def set_app_state(self, app_state: Dict[str, Any]) -> str:
        """ set/change the state of a running app, called for to prepare app.run_app """
        err_msg = super().set_app_state(app_state)
        if not err_msg:
            pass
        return err_msg

    def on_draw_gui(self):
        """ callback after app init/build for to draw/refresh gui. """
        self.display_list()

    # item search and navigation in currently displayed list

    def find_item_index(self, item_name: str) -> int:
        """ determine list index in the currently displayed list. """
        for idx, data in enumerate(self._current_list):
            if data['text'] == item_name:
                return idx
        return -1

    def get_item_by_name(self, item_name: str) -> ItemDataType:
        """ search list item in current list """
        lx = self.find_item_index(item_name)
        if lx != -1:
            return self._current_list[lx]
        return dict(text='')

    def get_widget_by_name(self, item_name: str) -> Optional[Widget]:
        """ search list item widget """
        lcw = self.framework_app.root.ids.listContainer
        for li in lcw.children:
            if li.text == item_name:
                return li

    def go_down_tree(self, list_name: str):
        """ user navigates down in the tree into list_name """
        self.data_path.append(list_name)
        self.change_app_state('data_path', self.data_path)
        self.change_app_state('current_item', '')
        self.display_list()

    def go_up_tree(self):
        """ user navigates up in the data tree """
        list_name = self.data_path.pop()
        self.change_app_state('data_path', self.data_path)
        self.change_app_state('current_item', list_name)
        self.display_list()

    # item (leaf/sub_list) add/delete/edit of name/copy/del

    def add_leaf_confirmed(self, item_name: str, liw: Widget):
        """ finish the addition of a new list item """
        self._current_list.append(dict(text=item_name, state='normal'))

        liw.text = item_name
        lcw = self.framework_app.root.ids.listContainer
        lcw.add_widget(liw)
        lcw.height += liw.height

        self.change_app_state('current_item', item_name)

    def add_list(self, list_name, copy_items_from=''):
        """ add new list """
        if copy_items_from:
            new_list = deepcopy(self.get_item_by_name(copy_items_from))
        else:
            new_list = dict(sub_list=list())
        new_list['text'] = list_name
        self._current_list.append(new_list)
        self.change_app_state('current_item', list_name)

    def add_new_leaf(self):
        """ start/initiate the addition of a new list item """
        self.change_app_state('current_item', '')
        self._current_widget = Factory.Leaf()
        pu = Factory.LeafEditor(title='')
        pu.open()  # calling self._current_widget on dismiss/close

    def delete_current_item(self):
        """ menu delete button callback for current/last touched item in current list """
        item_name = self.current_item
        lid = self.get_item_by_name(item_name)
        if 'sub_list' in lid:
            self.delete_list_popup(item_name)
        else:
            self.delete_item_confirmed(item_name)

    def delete_data_item(self, item_name):
        """ delete list item """
        self._current_list.remove(self.get_item_by_name(item_name))
        self.change_app_state('current_item', '')

    def delete_item_confirmed(self, item_name):
        """ delete list item """
        lcw = self.framework_app.root.ids.listContainer
        liw = self.get_widget_by_name(item_name)
        if liw:
            self.delete_data_item(liw.text)
            lcw.height -= liw.height
            lcw.remove_widget(liw)

    @staticmethod
    def delete_list_popup(list_name):
        """ delete list """
        pu = Factory.ConfirmListDeletePopup()
        pu.what = list_name
        pu.open()

    def delete_list_confirmed(self, list_name):
        """ delete list confirmation callback """
        self.delete_data_item(list_name)
        self.save_app_state()
        self.display_list()

    def edit_leaf(self, item_name, *_):
        """ edit list item """
        self.dpo('edit long touched item', item_name)
        liw = self.get_widget_by_name(item_name)
        if liw:
            self.change_app_state('current_item', item_name)
            self._current_widget = liw
            svw = self.framework_app.root.ids.listContainer.parent
            border = (12, 3, 12, 3)   # (bottom, right, top, left)
            phx = (liw.x - border[3]) / Window.width  # svw.size[0]
            phy = (liw.y - (svw.viewport_size[1] - svw.size[1]) * svw.scroll_y - border[0]) / Window.height
            pu = Factory.LeafEditor(title=liw.text,
                                    pos_hint=dict(x=phx, y=phy),
                                    size_hint=(None, None), size=(liw.width, liw.height * 3),
                                    background_color=(.6, .6, .6, .6),
                                    border=border,
                                    separator_height=3,
                                    title_align='center',
                                    title_color=self.selected_item_ink,
                                    title_size=self.font_size / 1.8)
            # pu.open()  # calling leaf_edit_finished() on dismiss/close
            Clock.schedule_once(pu.open, 1.2)       # focus is still going away with touch_up

    def list_name_edit_start(self, list_name='', copy_items_from=''):
        """ start/initiate the edit of a list name """
        self._edit_list_name = list_name
        self._copy_items_from = copy_items_from
        self.change_app_state('current_item', '')
        pu = Factory.ListEditor(title=list_name)
        pu.open()  # calling self._currentList on dismiss/close

    def list_name_edit_finished(self, list_name):
        """ dismiss call back for new, copy and edit list name """
        self.dpo('list_name_edit_finished - new list name=', list_name)
        if not self.find_item_index(list_name) == -1:
            if self._copy_items_from:
                self.add_list(list_name, self._copy_items_from)
            elif self._edit_list_name:  # user edited list name
                self.add_list(list_name, self._edit_list_name)
                self.delete_data_item(self._edit_list_name)
            else:  # user added new list name (with text)
                self.add_list(list_name)
            self.save_app_state()
            self.display_list()  # refresh screen

    def item_touch_down_handler(self, leaf_name, touch):
        """ long touch detection and double/triple tap event handlers for lists (only called if list is not empty) """
        self.dpo('listTouchDownHandler', leaf_name, touch)
        if touch.is_double_tap:
            self._multi_tap = 1
            return
        elif touch.is_triple_tap:
            self._multi_tap = -2  # -2 because couldn't prevent the double tap before/on triple tap
            return
        lcw = self.framework_app.root.ids.listContainer
        local_touch_pos = lcw.to_local(touch.x, touch.y)
        self.dpo('..local', local_touch_pos)
        liw = self.get_widget_by_name(leaf_name)
        if liw and liw.collide_point(*local_touch_pos):
            self.dpo('....touched widget', leaf_name)
            self._last_touch_start_callback[leaf_name] = partial(self.edit_leaf, leaf_name)
            Clock.schedule_once(self._last_touch_start_callback[leaf_name], 1.5)  # edit item text

    def item_touch_up_handler(self, leaf_name, touch):
        """ touch up detection and multi-tap event handlers for lists """
        self.dpo('listTouchUpHandler', leaf_name, touch)
        if leaf_name in self._last_touch_start_callback:
            Clock.unschedule(self._last_touch_start_callback[leaf_name])
        if self._multi_tap:
            # double/triple click allows to in-/decrease the list item font size
            font_size = self.font_size
            self.dpo(f"FONT SIZE CHANGE from {font_size} to {font_size + sp(3) * self._multi_tap}")
            font_size += sp(3) * self._multi_tap
            if font_size < MIN_FONT_SIZE:
                font_size = MIN_FONT_SIZE
                self.dpo(f"   .. CORRECTED to MIN={font_size}")
            elif font_size > MAX_FONT_SIZE:
                font_size = MAX_FONT_SIZE
                self.dpo(f"   .. CORRECTED to MAX={font_size}")
            self.change_app_state('font_size', font_size)
            self.display_list()
            self._multi_tap = 0

    def leaf_edit_finished(self, text):
        """ finished list edit callback """
        self.dpo('leaf_edit_finished', text, self._current_widget)
        liw = self._current_widget
        if not liw:
            self.dpo("last_edit_finished(): current widget unset in popup dismiss callback")
            return  # sometimes this event is fired multiple times (on dismiss of popup)
        self._current_widget = None  # release ref created by add_new_leaf()/edit_leaf()

        remove_item = not text  # (text is None or text == '')
        new_item = (liw.text == '')
        if remove_item and new_item:
            return      # user cancelled newly created but still not added list item
        if text and self.find_item_index(text) != -1:
            self.play_beep()
            return      # prevent creation of duplicates

        if remove_item:  # user cleared text of existing list item
            self.delete_item_confirmed(liw.text)
        elif new_item:  # user added new list item (with text)
            self.add_leaf_confirmed(text, liw)
        else:  # user edited list item
            self.get_item_by_name(liw.text)['text'] = text
            liw.text = text
            self.change_app_state('current_item', text)
        self.save_app_state()

    def display_list(self):
        """ refresh lists """
        current_item = self.current_item
        self._current_list = self.data_tree
        for sub_list in self.data_path:
            self._current_list = self.get_item_by_name(sub_list)['sub_list']

        lf_ds = self.framework_app.root.ids.menuBar.ids.listFilterSelected.state == 'normal'
        lf_ns = self.framework_app.root.ids.menuBar.ids.listFilterUnselected.state == 'normal'

        lcw = self.framework_app.root.ids.listContainer
        lcw.clear_widgets()
        h = 0
        for lid in self._current_list:
            sel_state = lid.get('state', 'normal') == 'down'
            if lf_ds and sel_state or lf_ns and not sel_state:
                liw = Factory.List() if 'sub_list' in lid else Factory.Leaf()
                liw.text = lid['text']
                liw.state = lid.get('state', 'normal')

                lcw.add_widget(liw)
                h += liw.height
        lcw.height = h

        # ensure that current leaf/sub-list is visible - if still exists in current list
        if current_item:
            pass
        # restore self.current_item (changed in list redraw by setting observed selectButton.state)
        self.change_app_state('current_item', current_item)

    def toggle_list_filter(self, filter_button_text, filter_button_state):
        """ list item filter """
        self.dpo('toggle_list_filter', filter_button_text, filter_button_state)
        toggle_selected_filter = filter_button_text == "B"
        filtering = filter_button_state == 'down'
        if toggle_selected_filter:
            self.change_app_state('filter_selected', filtering)
            if filtering and self.filter_unselected:
                self.change_app_state('filter_unselected', False)
        else:
            self.change_app_state('filter_unselected', filtering)
            if filtering and self.filter_selected:
                self.change_app_state('filter_selected', False)
        self.save_app_state()
        self.display_list()

    def toggle_leaf(self, item_name, state):
        """ toggle list item """
        self.dpo('toggle_leaf', item_name, state)
        self.get_item_by_name(item_name)['state'] = state
        self.change_app_state('current_item', item_name)
        self.save_app_state()
        # if self.filter_selected or self.filter_unselected:
        #     self.display_list()  # refresh only needed if one filter is active


# app start
if __name__ in ('__android__', '__main__'):
    MaioApp(app_name='maio', app_title="Irmi's Shopping Listz").run_app()
