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
    0.12    big refactoring of UI (migrate to KivyMainApp) and data structure (allow list in list).
  ToDo:
    - better handling of doubletap/tripletap
    - allow user to change order of item in list
    - nicer UI (from kivy.uix.effectwidget import EffectWidget, InvertEffect, HorizontalBlurEffect, VerticalBlurEffect)
    - user specific app theme (color, fonts) config screen

"""
from copy import deepcopy
import datetime
from functools import partial
from typing import Any, Dict, List, Optional

from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.metrics import sp
from kivy.uix.behaviors import DragBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.core.window import Window

from ae.KivyApp import MIN_FONT_SIZE, MAX_FONT_SIZE, KivyMainApp


__version__ = '0.12'

ItemDataType = Dict[str, Any]
ListDataType = List[ItemDataType]

DEL_SUB_LIST_PREFIX = "from "               #: delete_item_confirmed() item_name prefix: if list or sub_list get deleted


class MaioApp(KivyMainApp):
    """ app class """
    filter_selected: bool = True            #: True for to hide selected items
    filter_unselected: bool = True          #: True for to hide unselected items
    data_tree: ListDataType = list()        #: app data

    current_list: ListDataType = list()     #: item data of currently displayed sub-list
    dragging_idx: Optional[int] = None      #: index of dragged data in current list if in drag mode else None
    placeholders_above: Dict[int, Widget] = dict()  #: added placeholder above widgets (used for drag+drop)
    placeholders_below: Dict[int, Widget] = dict()  #: added placeholder below widgets (used for drag+drop)

    _current_widget: Optional[Widget]       #: widget used for to add a new or edit a list item
    _multi_tap: int = 0                     #: used for listTouchDownHandler
    _last_touch_start_callback: Dict = dict()

    # app init

    def set_app_state(self, app_state: Dict[str, Any]) -> str:
        """ set/change the state of a running app, called for to prepare app.run_app """
        err_msg = super().set_app_state(app_state)
        if not err_msg:
            pass
        return err_msg

    def on_framework_app_start(self):
        """ callback after app init/build for to draw/refresh gui. """
        self.on_context_draw()

    # item/widget search in currently displayed list

    def find_item_index(self, item_name: str) -> int:
        """ determine list index in the currently displayed list. """
        for idx, data in enumerate(self.current_list):
            if data['id'] == item_name:
                return idx
        return -1

    def get_item_by_name(self, item_name: str) -> ItemDataType:
        """ search list item in current list """
        lx = self.find_item_index(item_name)
        if lx != -1:
            return self.current_list[lx]
        return dict(id='')

    def get_widget_by_name(self, item_name: str) -> Optional[Widget]:
        """ search list item widget """
        lcw = self.framework_app.root.ids.listContainer
        for liw in lcw.children:
            if liw.item_data['id'] == item_name:
                return liw

    # item (leaf/sub_list) add/delete/edit of name/copy/del

    def add_leaf_confirmed(self, item_name: str, liw: Widget):
        """ finish the addition of a new list item """
        # self.current_list.append(dict(id=item_name))
        # liw.item_data['id'] = item_name
        liw.item_data['id'] = item_name
        self.current_list.append(liw.item_data)
        lcw = self.framework_app.root.ids.listContainer
        lcw.add_widget(liw)
        lcw.height += liw.height

        self.change_app_state('context_id', item_name)

    def add_list(self, list_name, copy_items_from=''):
        """ add new list """
        if copy_items_from:
            new_list = deepcopy(self.get_item_by_name(copy_items_from))
        else:
            new_list = dict(sub_list=list())
        new_list['id'] = list_name
        self.current_list.append(new_list)
        self.change_app_state('context_id', list_name)

    def add_new_item(self):
        """ start/initiate the addition of a new list item """
        self.change_app_state('context_id', '')
        self._current_widget = Factory.ListItem(item_data=dict(id=''))
        pu = Factory.ItemEditor(title='')
        pu.open()  # calling self._current_widget on dismiss/close

    def create_placeholder(self, idx, liw, part):
        """ create placeholder data structures. """
        self.cleanup_placeholder(redraw=False)

        if 'syb_list' in liw.item_data and 1 < part < 2:
            self.placeholders_above[idx] = Factory.DropPlaceholder(height=liw.height / 2)
            self.placeholders_below[idx] = Factory.DropPlaceholder(height=liw.height / 2)
        else:
            placeholders = self.placeholders_above if part > 1.5 else self.placeholders_below
            placeholders[idx] = Factory.DropPlaceholder(height=liw.height)
        self.on_context_draw()

    def cleanup_placeholder(self, redraw=True):
        """ cleanup placeholder data and widgets. """
        placeholders = list(self.placeholders_above.values()) + list(self.placeholders_below.values())
        for placeholder in placeholders:
            # if placeholder.parent:
            placeholder.parent.remove_widget(placeholder)

        self.placeholders_above.clear()
        self.placeholders_below.clear()

        if redraw:
            self.on_context_draw()

    def create_item_widgets(self, idx: int, lid: ItemDataType) -> List[Widget]:
        """ create widgets for to display one item, optionally with placeholder markers

        :param idx:
        :param lid:
        :return:
        """
        widgets = list()

        if idx in self.placeholders_above:
            widgets.append(self.placeholders_above[idx])

        old_lid = lid.copy()    # save item data because will be reset by new widget
        liw = Factory.ListItem(item_data=lid)
        liw.ids.toggleSelected.text = old_lid['id']
        liw.ids.toggleSelected.state = 'down' if old_lid.get('sel') else 'normal'
        assert liw.item_data == old_lid

        liw.list_idx = idx
        widgets.append(liw)

        if idx in self.placeholders_above:
            widgets.append(self.placeholders_above[idx])

        return widgets

    def delete_current_item(self):
        """ menu delete button callback for current/last touched item in current list """
        item_name = self.context_id
        lid = self.get_item_by_name(item_name)
        if 'sub_list' in lid:
            if lid['sub_list']:
                self.delete_list_popup(item_name)
                return
            lid.pop('sub_list')
        else:
            self.delete_item_confirmed(item_name)

    def delete_data_item(self, item_name):
        """ delete list item """
        self.current_list.remove(self.get_item_by_name(item_name))
        self.change_app_state('context_id', '')

    def delete_item_confirmed(self, item_name):
        """ delete item or sub-list of this item """
        if item_name.startswith(DEL_SUB_LIST_PREFIX):
            item_name = item_name[len(DEL_SUB_LIST_PREFIX):]
            del_sub_list = True
        else:
            del_sub_list = False
        lcw = self.framework_app.root.ids.listContainer
        liw = self.get_widget_by_name(item_name)
        if liw:
            if del_sub_list:
                self.get_item_by_name(item_name).pop('sub_list', None)
            else:
                self.delete_data_item(item_name)
                lcw.height -= liw.height
                lcw.remove_widget(liw)

    @staticmethod
    def delete_list_popup(list_name):
        """ delete list """
        pu = Factory.ConfirmListDeletePopup()
        pu.what = list_name
        pu.open()

    def edit_item_popup(self, item_name, *_):
        """ edit list item """
        self.dpo('edit long touched item', item_name)
        liw = self.get_widget_by_name(item_name)
        if liw:
            self.change_app_state('context_id', item_name)
            self._current_widget = liw
            svw = self.framework_app.root.ids.listContainer.parent
            border = (12, 3, 12, 3)   # (bottom, right, top, left)
            phx = (liw.x - border[3]) / Window.width  # svw.size[0]
            phy = (liw.y - (svw.viewport_size[1] - svw.size[1]) * svw.scroll_y - border[0]) / Window.height
            pu = Factory.ItemEditor(title=liw.item_data['id'],
                                    pos_hint=dict(x=phx, y=phy),
                                    size_hint=(None, None), size=(liw.width, liw.height * 3),
                                    background_color=(.6, .6, .6, .6),
                                    border=border,
                                    separator_height=3,
                                    title_align='center',
                                    title_color=self.selected_item_ink,
                                    title_size=self.font_size / 1.8)
            # pu.open()  # calling edit_item_finished() on dismiss/close
            Clock.schedule_once(pu.open, 1.2)       # focus is still going away with touch_up

    def edit_item_finished(self, text, state):
        """ finished list edit callback """
        self.dpo('edit_item_finished', text, self._current_widget)
        liw = self._current_widget
        if not liw:
            self.dpo("last_edit_finished(): current widget unset in popup dismiss callback")
            return  # sometimes this event is fired multiple times (on dismiss of popup)
        self._current_widget = None  # release ref created by add_new_item()/edit_item_popup()

        item_data = liw.item_data       # self.get_item_by_name(liw.text)
        remove_item = not text  # (text is None or text == '')
        append_item = (item_data['id'] == '')
        if remove_item and append_item:
            return      # user cancelled newly created but still not added list item
        if (append_item or text != item_data['id']) and self.find_item_index(text) != -1:
            self.play_beep()
            return      # prevent creation of duplicates

        if remove_item:  # user cleared text of existing list item
            if item_data.get('sub_list'):
                self.delete_list_popup(item_data['id'])
                return
            self.delete_item_confirmed(item_data['id'])
        elif append_item:  # user added new list item (with text)
            if state == 'down':
                self.add_list(text)
            else:
                self.add_leaf_confirmed(text, liw)
        else:  # user edited list item
            item_data['id'] = text
            # liw.text = text
            if state != 'down' if 'sub_list' in item_data else 'normal':
                if state == 'normal':
                    if item_data.get('sub_list'):
                        self.delete_list_popup(DEL_SUB_LIST_PREFIX + text)
                        return
                    if 'sub_list' in item_data:
                        item_data.pop('sub_list')
                else:
                    item_data['sub_list'] = list()
            self.change_app_state('context_id', text)
        self.save_app_state()
        self.on_context_draw()

    def glide_start(self, liw: Widget):
        """ start gliding for to move item in current list. """
        liw.gliding = True
        lcw = self.framework_app.root.ids.listContainer
        lcw.remove_widget(liw)
        self.framework_app.root.add_widget(liw)

    def glide_stop(self, liw: Widget):
        """ stop gliding and move item in current list. """
        lcw = self.framework_app.root.ids.listContainer
        self.framework_app.root.remove_widget(liw)
        lcw.add_widget(liw)
        liw.gliding = False
        self.on_context_draw()

    def item_touch_down_handler(self, item_name, touch):
        """ long touch detection and double/triple tap event handlers for lists (only called if list is not empty) """
        self.dpo('listTouchDownHandler', item_name, touch)
        if touch.is_double_tap:
            self._multi_tap = 1
            return
        elif touch.is_triple_tap:
            self._multi_tap = -2  # -2 because couldn't prevent the double tap before/on triple tap
            return
        lcw = self.framework_app.root.ids.listContainer
        local_touch_pos = lcw.to_local(touch.x, touch.y)
        self.dpo('..local', local_touch_pos)
        liw = self.get_widget_by_name(item_name)
        if liw and liw.collide_point(*local_touch_pos):
            self.dpo('....touched widget', item_name)
            self._last_touch_start_callback[item_name] = partial(self.edit_item_popup, item_name)
            Clock.schedule_once(self._last_touch_start_callback[item_name], 0.9)
            return True
        return False

    def item_touch_up_handler(self, item_name, touch):
        """ touch up detection and multi-tap event handlers for lists """
        self.dpo('listTouchUpHandler', item_name, touch)
        if item_name in self._last_touch_start_callback:
            Clock.unschedule(self._last_touch_start_callback[item_name])
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
            self.on_context_draw()
            self._multi_tap = 0
            return True
        return False

    def on_context_draw(self):
        """ refresh lists """
        context_id = self.context_id
        self.current_list = self.data_tree
        for sub_list in self.context_path:
            self.current_list = self.get_item_by_name(sub_list)['sub_list']

        lf_ds = self.framework_app.root.ids.menuBar.ids.listFilterSelected.state == 'normal'
        lf_ns = self.framework_app.root.ids.menuBar.ids.listFilterUnselected.state == 'normal'

        lcw = self.framework_app.root.ids.listContainer
        lcw.clear_widgets()
        h = 0
        for idx, lid in enumerate(self.current_list):
            if idx != self.dragging_idx:
                sel_state = lid.get('sel')
                if lf_ds and sel_state or lf_ns and not sel_state:
                    for liw in self.create_item_widgets(idx, lid):
                        lcw.add_widget(liw)
                        h += liw.height
        lcw.height = h

        # ensure that current leaf/sub-list is visible - if still exists in current list
        if context_id:
            pass
        # restore self.context_id (changed in list redraw by setting observed selectButton.state)
        self.change_app_state('context_id', context_id)

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
        self.on_context_draw()

    @staticmethod
    def update_item_data(liw: Widget, item_name: str, state: str) -> ItemDataType:
        """ update item_data of ListItem widget """
        liw.item_data['id'] = item_name
        if state == 'down':
            liw.item_data['sel'] = 1
        elif 'sel' in liw.item_data:
            liw.item_data.pop('sel')
        return liw.item_data


class ListItem(DragBehavior, BoxLayout):
    """ widget to display data item in list. """
    def __init__(self, **kwargs):
        self.item_data = kwargs.pop('item_data')
        super(ListItem, self).__init__(**kwargs)

        kivy_app = App.get_running_app()
        self.app_root = kivy_app.root       # MaioRoot
        self.main_app = kivy_app.main_app   # MaioApp
        self.lcw = kivy_app.root.ids.listContainer
        self.dragged_from_list = None
        self.dragged_from_idx = None
        self.list_idx = -1
        # self.new_idx = -1

        self.gliding = False

    def on_touch_down(self, touch):
        """ move gliding list item widget """
        self._po('DOWN', touch)
        if not self.ids.glideStart.collide_point(*touch.pos):
            return False

        self.dragged_from_list = self.main_app.current_list
        self.dragged_from_idx = self.main_app.dragging_idx = self.list_idx
        self.parent.remove_widget(self)

        self.x = touch.pos[0] - self.ids.glideStart.x - self.ids.glideStart.width / 2
        # Window.mouse_pos[0] - (touch.pos[0] - self.x)
        self.y = Window.mouse_pos[1] - self.height / 2  # Window.mouse_pos[1] - (touch.pos[1] - self.y)
        self.app_root.add_widget(self)
        touch.pos = Window.mouse_pos

        print('RETURN touch', touch)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        """ move gliding list item widget """
        self._po('MOVE', touch)
        # if touch.grab_current is not self:
        #     return False
        ma = self.main_app
        self.pos = touch.pos[0] - self.ids.glideStart.x - self.ids.glideStart.width / 2, touch.pos[1] - self.height / 2
        if self.lcw.collide_point(*touch.pos):
            placeholders = list(ma.placeholders_above.values()) + list(ma.placeholders_below.values())
            for idx, liw in enumerate(self.lcw.children):
                if liw.collide_point(*touch.pos):
                    if liw not in placeholders:
                        ma.create_placeholder(idx, liw, (touch.x - liw.x) + liw.height / 3)
                    print('INNER RETURN TRUE')
                    return True

        ma.cleanup_placeholder()

        # if not self.gliding:
        #     return
        # self.pos = touch.pos[0] - self.ids.glideStart.x, touch.pos[1]
        print('RETURN TRUE')
        return True

    def on_touch_up(self, touch):
        """ drop / finish drag """
        self._po("UP", touch)

        if touch.grab_current is not self:
            return super().on_touch_up(touch)     # False

        if self.main_app.placeholders_above and self.main_app.placeholders_below:   # drop into sub list
            sub_list = self.dragged_from_list[self.dragged_from_idx]['sub_list']
            sub_list.insert(0, self.item_data)
        else:
            if self.main_app.placeholders_above:
                idx = list(self.main_app.placeholders_above.keys())[0]
            else:
                idx = list(self.main_app.placeholders_below.keys())[0] + 1
            item_data = self.dragged_from_list[self.dragged_from_idx]
            self.dragged_from_list.remove(item_data)
            self.main_app.current_list.insert(idx, item_data)

        self.dragged_from_list = None
        self.dragged_from_idx = None
        self.main_app.dragging_idx = None
        self.app_root.remove_widget(self)
        self.main_app.cleanup_placeholder()

        print('RETURN TRUE')
        return True

    def _po(self, title, touch):
        """ debug helper """
        print()
        print(title, self.item_data.get('id', '-PH-'), datetime.datetime.now())

        root = self.get_root_window()
        if root:
            print("   WidRoot", root.left, root.top, root.width, root.height, len(root.children))
        root = App.get_running_app().root
        print("   AppRoot", root.pos, root.size, len(root.children))
        lcw = root.ids.listContainer
        print("   SroPos ", lcw.parent.pos, lcw.parent.size, len(lcw.parent.children))
        print("   ContPos", lcw.pos, lcw.size, len(lcw.children))
        print("   ItemPos", self.pos, self.size)
        print("   GliPos ", self.ids.glideStart.pos, self.ids.glideStart.size)
        print("   TouPos ", touch.pos, touch)
        print("   MouPos ", Window.mouse_pos)


# app start
if __name__ in ('__android__', '__main__'):
    MaioApp(app_name='maio', app_title="Irmi's Shopping Listz").run_app()
