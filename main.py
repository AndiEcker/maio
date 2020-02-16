# -*- coding: UTF-8 -*-
""" My All In One - (c) 2020 Andi Ecker.

  version history:
    0.1     first beta (mini shopping list for Irmi with 4 static lists Lidl/Mercadona/Nor/Sur).
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
    0.13    finished unit tests for gui_app portion.
    0.14-20 extended kivy_app portion and unit tests, added icon images and bug fixing.
    0-21-22 added ae.updater and small UI bug fixes.
  ToDo:
    - user specific app theme (color, fonts) config screen

"""
from typing import Any, Dict, List, Optional

from kivy.animation import Animation
from kivy.app import App
from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.core.window import Window

from ae.kivy_app import KivyMainApp


__version__ = '0.22'


ItemDataType = Dict[str, Any]
ListDataType = List[ItemDataType]


class MaioApp(KivyMainApp):
    """ app class """
    selected_item_ink: tuple = (0.69, 1.0, 0.39, 0.18)      #: rgba color tuple for list items (selected)
    unselected_item_ink: tuple = (0.39, 0.39, 0.39, 0.18)   #: rgba color tuple for list items (unselected)
    context_path_ink: tuple = (0.99, 0.99, 0.39, 0.48)      #: rgba color tuple for drag&drop item placeholder
    context_id_ink: tuple = (0.99, 0.99, 0.69, 0.69)        #: rgba color tuple for drag&drop sub_list placeholder
    filter_selected: bool = True                            #: True for to hide selected items
    filter_unselected: bool = True                          #: True for to hide unselected items
    data_tree: ListDataType = list()                        #: app data

    current_list: ListDataType = list()             #: item data of currently displayed sub-list
    dragging_list_idx: Optional[int] = None         #: index of dragged data in current list if in drag mode else None
    placeholders_above: Dict[int, Widget] = dict()  #: added placeholder above widgets (used for drag+drop)
    placeholders_below: Dict[int, Widget] = dict()  #: added placeholder below widgets (used for drag+drop)

    _current_widget: Optional[Widget]               #: widget used for to add a new or edit a list item

    # callbacks and event handling

    def on_context_draw(self):
        """ refresh lists """
        context_id = self.context_id
        sub_list, self.current_list = self.get_context_list()
        self.dpo("on_context_draw", sub_list or 'RooT', context_id)

        lf_ds = self.root_layout.ids.menuBar.ids.listFilterSelected.state == 'normal'
        lf_ns = self.root_layout.ids.menuBar.ids.listFilterUnselected.state == 'normal'
        lcw = self.root_layout.ids.listContainer
        lcw.clear_widgets()
        h = 0
        for list_idx, lid in enumerate(self.current_list):
            if list_idx != self.dragging_list_idx:
                sel_state = lid.get('sel')
                if lf_ds and sel_state or lf_ns and not sel_state:
                    for liw in self.create_item_widgets(list_idx, lid):
                        lcw.add_widget(liw)
                        h += liw.height
        lcw.height = h

        # ensure that current leaf/sub-list is visible - if still exists in current list
        redraw = False
        if context_id:
            liw = self.get_widget_by_name(context_id)
            if liw:
                lcw.parent.scroll_to(liw)
            else:
                context_id = ''     # last current item got filtered by user
                redraw = True

        # restore self.context_id (changed in list redraw by setting observed selectButton.state)
        self.set_context(context_id, redraw=redraw)
        # save changed app states (because context/content got changed by user)
        self.save_app_states()

    def on_app_start(self):
        """ callback after app init/build for to draw/refresh gui. """
        self.on_context_draw()

    def on_key_press(self, key_code, _modifiers):
        """ key press event. """
        if key_code == 'up':
            self.set_neighbour_context(-1)
        elif key_code == 'down':
            self.set_neighbour_context(1)
        elif key_code == 'pgup':
            self.set_neighbour_context(-15)
        elif key_code == 'pgdown':
            self.set_neighbour_context(15)
        elif key_code == 'home':
            self.set_neighbour_context(-999999)
        elif key_code == 'end':
            self.set_neighbour_context(999999)
        elif key_code == ' ' and self.context_id:    # key string 'space' is not in Window.command_keys
            liw = self.get_widget_by_name(self.context_id)
            new_state = 'normal' if liw.ids.toggleSelected.state == 'down' else 'down'
            self.update_item_data(liw, self.context_id, new_state)
            self.on_context_draw()
        elif key_code == 'escape' and len(self.root_win.children) > 1:
            for pu in self.pop_ups_opened():
                pu.dismiss()
        elif key_code in ('escape', 'left') and self.framework_app.app_state['context_path']:
            self.context_leave()
        elif key_code in ('enter', 'right') and self.context_id \
                and 'sub_list' in self.get_widget_by_name(self.context_id).item_data:
            self.context_enter(self.context_id)
        elif key_code == 'del' and self.context_id:
            self.delete_item_popup(self.context_id)
        else:
            return False
        return True

    # item/widget context handling and search in currently displayed list

    def context_enter(self, context_id: str, next_context_id: str = ''):
        """ overwrite to animate. """
        lcw = self.root_layout.ids.listContainer
        ani = Animation(x=Window.width, d=0.003) + Animation(x=lcw.x, d=0.21, t='out_quint')
        ani.start(lcw)
        super().context_enter(context_id, next_context_id=next_context_id)

    def context_leave(self, next_context_id: str = ''):
        """ overwrite to animate. """
        lcw = self.root_layout.ids.listContainer
        ani = Animation(y=100, right=100, d=0.006) + Animation(y=lcw.y, right=lcw.right, d=0.21, t='out_quint')
        ani.start(lcw)
        super().context_leave(next_context_id=next_context_id)

    def find_item_index(self, item_name: str, searched_list: Optional[ListDataType] = None) -> int:
        """ determine list index in the currently displayed list. """
        if searched_list is None:
            searched_list = self.current_list
        for list_idx, data in enumerate(searched_list):
            if data['id'] == item_name:
                return list_idx
        return -1

    def get_context_list(self, path_end_idx: Optional[int] = None):
        """ get list name and data of the current context list. """
        current_list = self.data_tree
        sub_list_name = ''
        for sub_list_name in self.context_path[:path_end_idx]:
            current_list = self.get_item_by_name(sub_list_name, searched_list=current_list)['sub_list']
        return sub_list_name, current_list

    def get_item_by_name(self, item_name: str, searched_list: Optional[ListDataType] = None) -> ItemDataType:
        """ search list item in current list """
        if searched_list is None:
            searched_list = self.current_list
        lx = self.find_item_index(item_name, searched_list=searched_list)
        if lx != -1:
            return searched_list[lx]
        return dict(id='')

    def get_widget_by_name(self, item_name: str) -> Optional[Widget]:
        """ search list item widget """
        lcw = self.root_layout.ids.listContainer
        for liw in lcw.children:
            item_data = getattr(liw, 'item_data', None)
            if item_data and item_data['id'] == item_name:
                return liw

    def set_neighbour_context(self, delta):
        """ move context id to previous/next item. """
        current_list = self.current_list
        if current_list:
            context_id = self.context_id
            if context_id:
                idx = min(max(0, self.find_item_index(context_id) + delta), len(current_list) - 1)
            else:
                idx = min(max(-1, delta), 0)
            self.set_context(current_list[idx]['id'])

    def sub_item_names(self, item_name, sub_list_only, sub_list=None, sub_item_names=None):
        """ return item names of item, including sub_list items (if exists). """
        if sub_list is None:
            sub_list = self.current_list
        if sub_item_names is None:
            sub_item_names = list()

        if not sub_list_only:
            sub_item_names.append(item_name)

        item_data = self.get_item_by_name(item_name, sub_list)
        sub_list = item_data.get('sub_list', list())
        for sub_item in sub_list:
            if sub_item.get('sub_list'):
                self.sub_item_names(sub_item['id'], False, sub_list, sub_item_names)
            else:
                sub_item_names.append(sub_item['id'])

        return sub_item_names

    # item (leaf/sub_list) add/delete/edit of name/copy/del

    def add_item_popup(self):
        """ start/initiate the addition of a new list item """
        self.set_context('', redraw=False)
        self._current_widget = Factory.ListItem()
        pu = Factory.ItemEditor(title='')
        pu.open()  # calling self._current_widget on dismiss/close

    def add_item_confirmed(self, item_name: str, liw: Widget, has_sub_list: bool):
        """ finish the addition of a new list item """
        liw.item_data['id'] = item_name
        if has_sub_list:
            liw.item_data['sub_list'] = list()
        self.current_list.append(liw.item_data)

        lcw = self.root_layout.ids.listContainer
        lcw.add_widget(liw)
        lcw.height += liw.height

        self.set_context(item_name)

    def create_placeholder(self, child_idx: int, liw: Widget, touch_y: float) -> bool:
        """ create placeholder data structures. """
        child_idx -= self.cleanup_placeholder(child_idx=child_idx)
        part = (touch_y - liw.y) / liw.height
        list_idx = liw.list_idx
        self.dpo(f"create placeholder {child_idx:2} {list_idx:2} {liw.item_data['id'][:9]:9}"
                 f" {liw.y:4.2f} {touch_y:4.2f} {part:4.2f}")
        if 'sub_list' in liw.item_data and 0.123 < part < 0.9:
            self.placeholders_above[list_idx] = Factory.DropPlaceholder(height=liw.height / 2.7)
            self.placeholders_below[list_idx] = Factory.DropPlaceholder(height=liw.height / 2.7)
        elif -0.111 < part < 1.11:
            placeholders = self.placeholders_above if part >= 0.501 else self.placeholders_below
            placeholders[list_idx] = Factory.DropPlaceholder(dark=True, height=liw.height * 1.11)
        else:
            return False

        # add widgets without redrawing (self.on_context_draw())
        lcw = self.root_layout.ids.listContainer
        for phw in self.placeholders_below.values():
            lcw.add_widget(phw, index=child_idx)
            lcw.height += phw.height
            child_idx += 1
        for phw in self.placeholders_above.values():
            lcw.add_widget(phw, index=child_idx + 1)
            lcw.height += phw.height

        return True

    def cleanup_placeholder(self, child_idx=0):
        """ cleanup placeholder data and widgets. """
        delta_idx = 0
        placeholders = list(self.placeholders_above.values()) + list(self.placeholders_below.values())
        for placeholder in placeholders:
            lcw = placeholder.parent
            if lcw:
                del_idx = lcw.children.index(placeholder)
                if del_idx < child_idx:
                    delta_idx = 1
                lcw.remove_widget(placeholder)
                lcw.height -= placeholder.height

        self.placeholders_above.clear()
        self.placeholders_below.clear()

        return delta_idx

    def create_item_widgets(self, list_idx: int, lid: ItemDataType) -> List[Widget]:
        """ create widgets for to display one item, optionally with placeholder markers

        :param list_idx:    index of item_data within current list.
        :param lid:         list item data.
        :return:            list of created widgets: one ListItem widget with item_data from lid and
                            optional placeholders above/below.
        """
        widgets = list()

        if list_idx in self.placeholders_above:
            widgets.append(self.placeholders_above[list_idx])

        # original item data dict passed to ListItem.__init__ will be reset by kv rules of the new widget
        # .. also toggleButton state will not be set correctly if assigning only item data with: liw.item_data = lid
        ori_lid = lid.copy()
        liw = Factory.ListItem(item_data=lid, list_idx=list_idx)
        liw.ids.toggleSelected.text = ori_lid['id']
        liw.ids.toggleSelected.state = 'down' if ori_lid.get('sel') else 'normal'
        widgets.append(liw)
        assert liw.item_data is lid
        assert liw.list_idx == list_idx

        if list_idx in self.placeholders_below:
            widgets.append(self.placeholders_below[list_idx])

        return widgets

    def delete_item_popup(self, item_name, sub_list_only=False):
        """ delete list """
        if sub_list_only and not self.sub_item_names(item_name, sub_list_only=sub_list_only):
            self.delete_item_confirmed(item_name, del_sub_list=True)    # no confirm needed for del of empty sub list
            self.set_context(item_name)
        else:
            pu = Factory.ConfirmItemDeletePopup()
            pu.which_item = item_name
            pu.sub_list_only = sub_list_only
            pu.open()

    def delete_item_confirmed(self, item_name, del_sub_list=False):
        """ delete item or sub-list of this item """
        lcw = self.root_layout.ids.listContainer
        liw = self.get_widget_by_name(item_name)
        lid = self.get_item_by_name(item_name)
        if del_sub_list:
            lid.pop('sub_list')
        else:
            self.current_list.remove(lid)
            # already re-drawn, so no need to reduce height: lcw.height -= liw.height
            lcw.remove_widget(liw)
            self.set_context('', redraw=False)

        self.on_context_draw()

    def edit_item_popup(self, item_name):
        """ edit list item """
        liw = self.get_widget_by_name(item_name)
        self.set_context(item_name)     # redraw needed for edit popup positioning
        self._current_widget = liw
        root = self.root_layout
        lcw = root.ids.listContainer
        svw = lcw.parent
        svw.scroll_to(liw)
        pos = svw.parent.to_widget(*liw.to_window(*liw.pos))    # - (lcw.size[1] - svw.size[1]) * svw.scroll_y
        border = Popup.border.defaultvalue   # (bottom, right, top, left)
        phx = pos[0] - border[3]
        phy = pos[1] - border[0]
        if svw.top > lcw.top:
            phy += svw.top - lcw.top
        else:
            phy += svw.g_translate.xy[1]
        height = liw.height * 1.5 + border[0] + border[2]
        phy = min(max(0, phy), svw.height - height)
        pu = Factory.ItemEditor(title=liw.item_data['id'],
                                pos_hint=dict(x=phx / Window.width, y=phy / Window.height),
                                size_hint=(None, None), size=(svw.width + border[1] + border[3], height),
                                background_color=(.9, .6, .6, .6),
                                border=border,
                                separator_height=0,
                                title_size=self.font_size / 80.1,
                                )
        pu.open()  # calling edit_item_finished() on dismiss/close
        # Clock.schedule_once(pu.open, 1.2)       # focus is still going away with touch_up

    def edit_item_finished(self, text, state):
        """ finished list edit callback """
        liw = self._current_widget
        if not liw:
            self.dpo("last_edit_finished(): current widget unset in popup dismiss callback")
            return                      # sometimes this event is fired multiple times (on dismiss of popup)
        self._current_widget = None     # release ref created by add_item_popup()/edit_item_popup()

        item_data = liw.item_data       # self.get_item_by_name(liw.text)
        remove_item = not text          # (text is None or text == '')
        append_item = (item_data['id'] == '')
        if remove_item and append_item:
            return                      # user cancelled newly created but still not added list item
        if (append_item or text != item_data['id']) and self.find_item_index(text) != -1:
            self.play_beep()
            return                      # prevent creation of duplicates

        if remove_item:                 # user cleared text of existing list item -> let user confirm the deletion
            self.delete_item_popup(item_data['id'])
            return

        if append_item:                 # user added new list item (with text)
            self.add_item_confirmed(text, liw, has_sub_list=state == 'down')
            return

        self.edit_item_confirmed(text, state == 'down', item_data)

    def edit_item_confirmed(self, new_name, want_list, old_item_data):
        """ change list data of edited/added item. """
        has_list = 'sub_list' in old_item_data
        if want_list != has_list:
            if not want_list:       # user removed list
                self.delete_item_popup(new_name, sub_list_only=True)
                return
            old_item_data['sub_list'] = list()
        old_item_data['id'] = new_name  # binding does set also: liw.text = text
        self.set_context(new_name)

    def pop_ups_opened(self):
        """ determine tuple of all opened PopUp instances. """
        for wid in self.root_win.children:     # PopUps are attached to the (SDL) Window instance
            if isinstance(wid, Popup):
                yield wid

    def toggle_list_filter(self, filter_button):
        """ list item filter """
        filter_button_state = filter_button.state
        self.dpo('toggle_list_filter', filter_button, filter_button_state)

        toggle_selected_filter = filter_button == self.root_layout.ids.menuBar.ids.listFilterSelected
        filtering = filter_button_state == 'down'
        if toggle_selected_filter:
            self.change_app_state('filter_selected', filtering)
            if filtering and self.filter_unselected:
                self.change_app_state('filter_unselected', False)
        else:
            self.change_app_state('filter_unselected', filtering)
            if filtering and self.filter_selected:
                self.change_app_state('filter_selected', False)

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


class ListItem(BoxLayout):
    """ widget to display data item in list. """
    def __init__(self, **kwargs):
        self.item_data = kwargs.pop('item_data', dict(id=''))
        self.list_idx = kwargs.pop('list_idx', -1)
        super().__init__(**kwargs)

        kivy_app = App.get_running_app()
        self.app_root = kivy_app.root       # MaioRoot
        self.main_app = kivy_app.main_app   # MaioApp
        self.lcw = kivy_app.root.ids.listContainer
        self.dragged_from_list = None
        self.dragging_on_back = None

    def on_touch_down(self, touch):
        """ move gliding list item widget """
        if not self.ids.dragHandle.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        touch.grab(self)
        touch.ud[self] = 'drag'
        self.dragged_from_list = self.main_app.current_list
        self.main_app.dragging_list_idx = self.list_idx
        assert self.list_idx == self.dragged_from_list.index(self.item_data)
        self.parent.remove_widget(self)
        self.x = touch.pos[0] - self.ids.dragHandle.x - self.ids.dragHandle.width / 2
        self.y = Window.mouse_pos[1] - self.height / 2
        self.app_root.add_widget(self)
        return True

    def on_touch_move(self, touch):
        """ move gliding list item widget """
        if touch.grab_current is not self or touch.ud.get(self) != 'drag':
            return False

        self.pos = touch.pos[0] - self.ids.dragHandle.x - self.ids.dragHandle.width / 2, touch.pos[1] - self.height / 2

        ma = self.main_app
        svw = self.lcw.parent
        if svw.collide_point(*svw.parent.to_local(*touch.pos)):
            placeholders = list(ma.placeholders_above.values()) + list(ma.placeholders_below.values())
            for child_idx, liw in enumerate(self.lcw.children):
                lc_pos = self.lcw.to_local(*svw.to_local(*touch.pos))
                if liw not in placeholders and liw.collide_point(*lc_pos) \
                        and ma.create_placeholder(child_idx, liw, lc_pos[1]):
                    self._restore_menu_bar()
                    return True

        mb = self.app_root.ids.menuBar
        bb = mb.children[-1]
        if not bb.disabled and bb.collide_point(*mb.to_local(*touch.pos)):
            ma.cleanup_placeholder()
            if not self.dragging_on_back:
                self.dragging_on_back = bb
                mb.remove_widget(bb)
                ph = Factory.DropPlaceholder(size=bb.size)
                ph.add_widget(Image(source='img/72/context_leave.png', allow_stretch=True, pos=bb.pos, size=bb.size))
                mb.add_widget(ph, index=len(mb.children))
        elif touch.pos[1] < self.height:
            svw.scroll_y = min(max(0, svw.scroll_y - svw.convert_distance_to_scroll(0, self.height)[1]), 1)
        elif touch.pos[1] > svw.top - self.height:
            svw.scroll_y = min(max(0, svw.scroll_y + svw.convert_distance_to_scroll(0, self.height)[1]), 1)

        return True

    def on_touch_up(self, touch):
        """ drop / finish drag """
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        if touch.ud[self] != 'drag':
            return False

        ma = self.main_app

        if self.dragging_on_back or ma.placeholders_above or ma.placeholders_below:
            if self.dragging_on_back:
                _, dst_list = self.main_app.get_context_list(path_end_idx=-1)
                list_idx = 0
            elif ma.placeholders_above and ma.placeholders_below:   # drop into sub list
                list_idx = list(ma.placeholders_below.keys())[0]
                dst_list = self.dragged_from_list[list_idx]['sub_list']
                list_idx = 0
            else:
                dst_list = self.dragged_from_list
                if ma.placeholders_above:
                    list_idx = list(ma.placeholders_above.keys())[0]
                else:
                    list_idx = list(ma.placeholders_below.keys())[0] + 1
            assert self.dragged_from_list.index(self.item_data) == self.list_idx
            self.dragged_from_list.remove(self.item_data)
            if list_idx != 0:
                self.main_app.set_context(self.item_data['id'], redraw=False)
            if list_idx > self.list_idx:
                list_idx -= 1
            dst_list.insert(list_idx, self.item_data)

        self.dragged_from_list = None
        ma.dragging_list_idx = None
        self._restore_menu_bar()
        self.app_root.remove_widget(self)
        ma.cleanup_placeholder()
        ma.on_context_draw()
        touch.ungrab(self)

        return True

    def _restore_menu_bar(self):
        if self.dragging_on_back:
            mb = self.app_root.ids.menuBar
            bb = self.dragging_on_back
            ph = mb.children[-1]
            mb.remove_widget(ph)
            mb.add_widget(bb, index=len(mb.children))
            self.dragging_on_back = None


class DropPlaceholder(Widget):
    """ placeholder for to display screen box to drop a dragged item onto """
    def __init__(self, **kwargs):
        self.dark = kwargs.pop('dark', False)
        super().__init__(**kwargs)


# app start
if __name__ in ('__android__', '__main__'):
    MaioApp(app_name='maio', app_title="Irmi's Shopping Lisz").run_app()
