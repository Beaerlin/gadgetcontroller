#!/usr/bin/env python3

import os
import subprocess
import tempfile
import time
from functools import partial
import xml.etree.ElementTree as ET
from pydbus import SystemBus

import gi

UIDEV = False


gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, GObject, Gio, Gdk, GLib, Pango

gi.require_version("Handy", "1")
from gi.repository import Handy

BUS_NAME = "de.beaerlin.GadgetController"
datapath = os.path.expanduser("~/.gadget")
if not os.path.isdir(os.path.join(datapath, "iso")):
    os.makedirs(os.path.join(datapath, "iso"))
if not os.path.isdir(os.path.join(datapath, "image")):
    os.makedirs(os.path.join(datapath, "image"))
if not os.path.isdir(os.path.join(datapath, "config")):
    os.makedirs(os.path.join(datapath, "config"))


class GadgetWindow:
    def __init__(self, application):
        self.application = application
        self.status = "Stopped"
        self.no_emmit = False
        Handy.init()

        self.widgets = []

        if not UIDEV:
            bus = SystemBus()
            self.service = bus.get(BUS_NAME)
        self.xmlfile = os.path.join(datapath, "config", "current.xml")
        if os.path.isfile(self.xmlfile):
            with open(self.xmlfile, "rb") as xfile:
                self.root = ET.fromstring(xfile.read().decode("utf-8"))
        else:
            self.root = ET.Element("usb")
            name = ET.SubElement(self.root, "name")
            name.text = "current"

        self.window = None
        self.headerbar = None
        self.leaflet = None
        self.sidebar = None
        self.content = None
        self.listbox = None
        self.stack = None
        self.back = None

        self._create_window()

        self.add_flash()
        self.add_iso()
        self.add_net()

        self.add_hid()
        self.add_soundcard()
        self.add_serial()
        # self.create_pages()
        self._load_state()
        self.leaflet.set_visible_child_name("sidebar")
        self.window.show_all()

        Gtk.main()

    def _widgets_disable(self, disable=True):
        for widget in self.widgets:
            if disable:
                widget.set_sensitive(False)
            else:
                widget.set_sensitive(True)

    def _create_window(self):
        self.window = Handy.Window()
        self.window.set_icon_from_file(
            "/usr/share/icons/Adwaita/512x512/devices/media-removable.png"
        )

        # self.window.set_default_size(640, 480)
        self.hight = 1440 / 2
        self.width = 720 / 2
        self.window.set_default_size(self.width, self.hight)
        self.window.set_title("Gadget Controller")
        self.window.connect("destroy", self.on_main_window_destroy)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(box)

        self.headerbar = Handy.HeaderBar()
        self.headerbar.set_title("Gadget Controller")
        self.headerbar.set_show_close_button(True)

        self.back = Gtk.Button.new_from_icon_name("go-previous-symbolic", 1)
        self.back.connect("clicked", self.on_back_clicked)
        self.back.set_visible(False)
        self.back.set_no_show_all(True)
        self.headerbar.pack_start(self.back)

        self.leaflet = Handy.Leaflet()
        self.leaflet.set_transition_type(Handy.LeafletTransitionType.SLIDE)
        self.leaflet.connect("notify::folded", self.on_leaflet_change)
        self.leaflet.connect("notify::visible-child", self.on_leaflet_change)
        self.sidebar = Gtk.Box()
        self.sidebar.set_size_request(720 / 2, 0)
        self.content = Gtk.Box()
        self.content.props.hexpand = True
        self.leaflet.add(self.sidebar)
        self.leaflet.child_set(self.sidebar, name="sidebar")
        self.leaflet.add(self.content)
        self.leaflet.child_set(self.content, name="content")
        self.leaflet.set_visible_child_name("sidebar")

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.sidebar.pack_start(sw, True, True, 0)
        self.listbox = Gtk.ListBox()
        self.listbox.connect("row-activated", self.on_select_page)
        sw.add(self.listbox)

        self.stack = Gtk.Stack()
        self.content.pack_start(self.stack, True, True, 0)

        box.pack_start(self.headerbar, False, True, 0)

        statbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.mainswitch = Gtk.Switch()
        statbox.pack_end(self.mainswitch, False, True, 10)
        self.mainswitch.connect("notify::active", self.on_start_stop)

        self.statlabel = Gtk.Label()
        self.statlabel.set_markup("Service: <b>Disabled</b>")
        statbox.pack_start(self.statlabel, False, True, 10)

        # box.pack_start(self.mainswitch, False, False, 10)
        # box.pack_end(self.mainswitch, False, True, 10)

        box.pack_start(statbox, False, True, 10)

        self.actionbar = Gtk.ActionBar()
        self.action_revealer = Gtk.Revealer()
        box.pack_start(self.action_revealer, False, True, 0)
        self.action_revealer.add(self.actionbar)

        save_btn = Gtk.Button()
        save_img = Gtk.Image()
        save_img.set_from_file("/usr/share/icons/Adwaita/32x32/legacy/list-add.png")
        save_btn.set_image(save_img)
        save_btn.connect("clicked", self.on_save_preset)
        self.actionbar.pack_start(save_btn)

        rem_btn = Gtk.Button()
        rem_img = Gtk.Image()
        rem_img.set_from_file("/usr/share/icons/Adwaita/32x32/legacy/list-remove.png")
        rem_btn.set_image(rem_img)
        save_btn.connect("clicked", self.on_remove_preset)
        self.actionbar.pack_start(rem_btn)

        self.preset_store = Gtk.ListStore(GObject.TYPE_STRING)

        self.preset_combo = Gtk.ComboBox()
        # self.preset_store.set_width_chars(5)
        self.preset_combo.set_model(self.preset_store)
        # combobox.set_active(0)
        cell = Gtk.CellRendererText()
        cell.set_property("wrap_mode", Pango.WrapMode.WORD)
        cell.set_property("wrap_width", 20)
        cell.set_property("max-width-chars", 20)
        # cell.max_width_chars(10)
        # help(cell)

        self.preset_combo.pack_start(cell, True)
        self.preset_combo.add_attribute(cell, "text", 0)
        self.actionbar.pack_start(self.preset_combo)

        action_button = Gtk.Button.new_with_label("Load")
        action_button.get_style_context().add_class("suggested-action")
        save_btn.connect("clicked", self.on_load_preset)
        self.actionbar.pack_end(action_button)
        # Add the Listview
        box.pack_start(self.leaflet, True, True, 0)

        self.messagebar = Gtk.ActionBar()
        self.message_revealer = Gtk.Revealer()
        box.pack_start(self.message_revealer, False, True, 0)
        self.message_revealer.add(self.messagebar)

        self.message_revealer_label = Gtk.Label(
            label="You have changed settings that need root permissions to save.",
            xalign=0.0,
        )
        self.message_revealer_label.set_line_wrap(True)
        self.messagebar.pack_start(self.message_revealer_label)
        self.message_button = Gtk.Button.new_with_label("Close")
        self.message_button.get_style_context().add_class("suggested-action")
        self.messagebar.pack_end(self.message_button)
        self.message_button.connect("clicked", self.on_message_hide)

    def add_serial(self):

        page = "Serial"
        label = Gtk.Label(label=page, xalign=0.0)
        label.set_margin_top(8)
        label.set_margin_bottom(8)
        label.set_margin_left(10)
        label.set_margin_right(10)
        label.set_name("row")
        row = Gtk.ListBoxRow()
        row.add(label)
        row.name = page
        row.title = page
        self.listbox.add(row)

        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(box)
        self.stack.add_named(sw, page)

        label = Gtk.Label(label="Status", xalign=0.0)
        label.get_style_context().add_class("heading")
        label.set_margin_bottom(4)
        box.pack_start(label, False, True, 0)
        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")
        frame.set_margin_bottom(12)
        box.pack_start(frame, False, True, 0)
        fbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(fbox)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Enable", xalign=0.0)
        lbox.pack_start(label, False, True, 0)

        switch = Gtk.Switch()
        self.serial_switch = switch
        switch.connect("notify::active", partial(self.on_activate, switch, "serial"))
        self.widgets.append(switch)
        rbox.pack_start(switch, False, False, 0)

    def storage_clicked(self, iv, ev):

        p = iv.get_path_at_pos(int(ev.x), int(ev.y))
        if not p is None:

            if iv.get_selection().path_is_selected(p[0]):

                iv.get_selection().unselect_path(p[0])
            else:
                iv.get_selection().select_path(p[0])

        return True  # make the IconView ignore this click

    def add_iso(self):

        page = "ISO Images"
        label = Gtk.Label(label=page, xalign=0.0)
        label.set_margin_top(8)
        label.set_margin_bottom(8)
        label.set_margin_left(10)
        label.set_margin_right(10)
        label.set_name("row")
        row = Gtk.ListBoxRow()
        row.add(label)
        row.name = page
        row.title = page
        self.listbox.add(row)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(box)
        self.stack.add_named(sw, page)
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)

        label = Gtk.Label(label="ISO Images", xalign=0.0)
        label.get_style_context().add_class("heading")
        label.set_margin_bottom(8)
        label.set_margin_top(8)
        box.pack_start(label, False, True, 0)

        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")
        frame.set_margin_bottom(12)
        box.pack_start(frame, False, True, 0)
        fbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(fbox)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        self.iso_store = Gtk.ListStore(str, str)

        self.iso_treeView = Gtk.TreeView(model=self.iso_store)
        self.iso_treeView.set_margin_bottom(10)

        renderer_text = Gtk.CellRendererText()

        str_column = Gtk.TreeViewColumn("", renderer_text, text=0)
        str_column.set_expand(True)
        self.iso_treeView.append_column(str_column)
        str_column = Gtk.TreeViewColumn("", renderer_text, text=1)
        self.iso_treeView.append_column(str_column)

        self.iso_treeView.set_headers_visible(False)

        sel = self.iso_treeView.get_selection()
        sel.set_mode(Gtk.SelectionMode.MULTIPLE)

        self.iso_treeView.connect("button-press-event", self.storage_clicked)

        self.widgets.append(self.iso_treeView)

        fbox.pack_start(self.iso_treeView, False, False, 0)

        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")
        frame.set_margin_bottom(12)
        box.pack_start(frame, False, True, 0)
        fbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(fbox)

        sbox = Gtk.Box()
        sbox.set_margin_top(12)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Enable", xalign=0.0)
        lbox.pack_start(label, False, True, 0)

        switch = Gtk.Switch()
        self.iso_switch = switch
        switch.connect(
            "notify::active", partial(self.on_activate, switch, "storage_iso")
        )

        self.widgets.append(switch)
        rbox.pack_start(switch, False, False, 0)

        frame = Gtk.Frame()

        frame.set_margin_top(12)
        frame.set_margin_bottom(12)

        box.pack_start(frame, False, True, 0)

        label = Gtk.Label(label="Delete ISO Image", xalign=0.0)
        label.get_style_context().add_class("heading")
        label.set_margin_bottom(8)
        label.set_margin_top(8)
        box.pack_start(label, False, True, 0)
        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")
        frame.set_margin_bottom(12)
        box.pack_start(frame, False, True, 0)
        fbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(fbox)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Image", xalign=0.0)
        label.set_margin_top(6)
        lbox.pack_start(label, False, True, 0)

        cell = Gtk.CellRendererText()
        cell.set_property("wrap_mode", Pango.WrapMode.WORD)
        cell.set_property("wrap_width", 20)
        cell.set_property("max-width-chars", 20)
        cell.set_property("width", 220)

        self.iso_delete_combo = Gtk.ComboBox()

        self.iso_delete_combo.set_model(self.iso_store)

        self.iso_delete_combo.pack_start(cell, True)
        self.iso_delete_combo.add_attribute(cell, "text", 0)
        self.widgets.append(self.iso_delete_combo)
        rbox.pack_start(self.iso_delete_combo, False, False, 0)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        delete_button = Gtk.Button.new_with_label("Delete")
        delete_button.set_margin_bottom(8)
        delete_button.set_margin_left(8)
        delete_button.set_margin_right(8)
        self.widgets.append(delete_button)

        delete_button.connect("clicked", self.on_delete_iso)
        fbox.pack_start(delete_button, True, False, 0)

    def add_flash(self):

        page = "Flash Images"
        label = Gtk.Label(label=page, xalign=0.0)
        label.set_margin_top(8)
        label.set_margin_bottom(8)
        label.set_margin_left(10)
        label.set_margin_right(10)
        label.set_name("row")
        row = Gtk.ListBoxRow()
        row.add(label)
        row.name = page
        row.title = page
        self.listbox.add(row)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(box)
        self.stack.add_named(sw, page)
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)

        label = Gtk.Label(label="Flash Images", xalign=0.0)
        label.get_style_context().add_class("heading")
        label.set_margin_bottom(8)
        label.set_margin_top(8)
        box.pack_start(label, False, True, 0)

        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")
        frame.set_margin_bottom(12)
        box.pack_start(frame, False, True, 0)
        fbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(fbox)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        self.flash_store = Gtk.ListStore(str, str)

        self.flash_treeView = Gtk.TreeView(model=self.flash_store)
        self.flash_treeView.set_margin_bottom(10)

        renderer_text = Gtk.CellRendererText()

        str_column = Gtk.TreeViewColumn("", renderer_text, text=0)
        str_column.set_expand(True)
        self.flash_treeView.append_column(str_column)
        str_column = Gtk.TreeViewColumn("", renderer_text, text=1)
        self.flash_treeView.append_column(str_column)

        self.flash_treeView.set_headers_visible(False)

        sel = self.flash_treeView.get_selection()
        sel.set_mode(Gtk.SelectionMode.MULTIPLE)

        self.flash_treeView.connect("button-press-event", self.storage_clicked)
        self.widgets.append(self.flash_treeView)

        fbox.pack_start(self.flash_treeView, False, False, 0)

        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")
        frame.set_margin_bottom(12)
        box.pack_start(frame, False, True, 0)
        fbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(fbox)

        sbox = Gtk.Box()
        sbox.set_margin_top(12)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Enable", xalign=0.0)
        lbox.pack_start(label, False, True, 0)

        switch = Gtk.Switch()
        self.flash_switch = switch

        switch.connect(
            "notify::active", partial(self.on_activate, switch, "storage_flash")
        )

        self.widgets.append(switch)
        rbox.pack_start(switch, False, False, 0)

        frame = Gtk.Frame()

        frame.set_margin_top(12)
        frame.set_margin_bottom(12)

        box.pack_start(frame, False, True, 0)

        label = Gtk.Label(label="Create Flash Image", xalign=0.0)
        label.get_style_context().add_class("heading")
        label.set_margin_bottom(8)
        label.set_margin_top(8)
        box.pack_start(label, False, True, 0)
        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")
        frame.set_margin_bottom(12)
        box.pack_start(frame, False, True, 0)
        fbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(fbox)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Name", xalign=0.0)
        label.set_margin_top(6)
        lbox.pack_start(label, False, True, 0)

        self.flash_create_name = Gtk.Entry()

        self.flash_create_name.set_width_chars(26)
        rbox.pack_start(self.flash_create_name, False, False, 0)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Size", xalign=0.0)
        label.set_margin_top(6)
        lbox.pack_start(label, False, True, 0)

        adj = Gtk.Adjustment(
            value=10.0,
            lower=1.0,
            upper=10000000000000.0,
            step_increment=5.0,
            page_increment=5.0,
            page_size=0.0,
        )

        self.flash_create_size = Gtk.SpinButton(adjustment=adj)
        self.flash_create_size.set_width_chars(15)
        self.flash_create_size.set_margin_right(10)

        label = Gtk.Label(label="GiB", xalign=0.0)

        sizebox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        sizebox.pack_start(self.flash_create_size, False, False, 0)
        sizebox.pack_start(label, False, False, 0)
        rbox.pack_start(sizebox, False, False, 0)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        create_button = Gtk.Button.new_with_label("Create")
        create_button.set_margin_bottom(8)
        create_button.set_margin_left(8)
        create_button.set_margin_right(8)
        create_button.connect("clicked", self.on_create_flash)
        fbox.pack_start(create_button, True, False, 0)

        label = Gtk.Label(label="Delete Flash Image", xalign=0.0)
        label.get_style_context().add_class("heading")
        label.set_margin_bottom(8)
        label.set_margin_top(8)
        box.pack_start(label, False, True, 0)
        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")
        frame.set_margin_bottom(12)
        box.pack_start(frame, False, True, 0)
        fbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(fbox)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Image", xalign=0.0)
        label.set_margin_top(6)
        lbox.pack_start(label, False, True, 0)

        cell = Gtk.CellRendererText()
        cell.set_property("wrap_mode", Pango.WrapMode.WORD)
        cell.set_property("wrap_width", 20)
        cell.set_property("max-width-chars", 20)
        cell.set_property("width", 220)

        self.flash_delete_combo = Gtk.ComboBox()

        self.flash_delete_combo.set_model(self.flash_store)

        self.flash_delete_combo.pack_start(cell, True)
        self.flash_delete_combo.add_attribute(cell, "text", 0)

        self.widgets.append(self.flash_delete_combo)

        rbox.pack_start(self.flash_delete_combo, False, False, 0)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        delete_button = Gtk.Button.new_with_label("Delete")
        delete_button.set_margin_bottom(8)
        delete_button.set_margin_left(8)
        delete_button.set_margin_right(8)

        self.widgets.append(delete_button)

        delete_button.connect("clicked", self.on_delete_flash)

        fbox.pack_start(delete_button, True, False, 0)

    def add_soundcard(self):

        page = "Sound"
        label = Gtk.Label(label=page, xalign=0.0)
        label.set_margin_top(8)
        label.set_margin_bottom(8)
        label.set_margin_left(10)
        label.set_margin_right(10)
        label.set_name("row")
        row = Gtk.ListBoxRow()
        row.add(label)
        row.name = page
        row.title = page
        self.listbox.add(row)

        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(box)
        self.stack.add_named(sw, page)

        label = Gtk.Label(label="Status", xalign=0.0)
        label.get_style_context().add_class("heading")
        label.set_margin_bottom(4)
        box.pack_start(label, False, True, 0)
        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")
        frame.set_margin_bottom(12)
        box.pack_start(frame, False, True, 0)
        fbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(fbox)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Enable", xalign=0.0)
        lbox.pack_start(label, False, True, 0)

        switch = Gtk.Switch()
        self.sound_switch = switch
        switch.connect("notify::active", partial(self.on_activate, switch, "sound"))

        self.widgets.append(switch)
        rbox.pack_start(switch, False, False, 0)

    def add_net(self):

        page = "Network"
        label = Gtk.Label(label=page, xalign=0.0)
        label.set_margin_top(8)
        label.set_margin_bottom(8)
        label.set_margin_left(10)
        label.set_margin_right(10)
        label.set_name("row")
        row = Gtk.ListBoxRow()
        row.add(label)
        row.name = page
        row.title = page
        self.listbox.add(row)

        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(box)
        self.stack.add_named(sw, page)

        label = Gtk.Label(label="Status", xalign=0.0)
        label.get_style_context().add_class("heading")
        label.set_margin_bottom(4)
        box.pack_start(label, False, True, 0)
        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")
        frame.set_margin_bottom(12)
        box.pack_start(frame, False, True, 0)
        fbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(fbox)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Enable RNDIS", xalign=0.0)
        lbox.pack_start(label, False, True, 0)

        switch = Gtk.Switch()
        self.rndis_switch = switch
        switch.connect("notify::active", partial(self.on_activate, switch, "net_rndis"))
        self.widgets.append(switch)
        rbox.pack_start(switch, False, False, 0)

    def add_hid(self):

        page = "HID"
        label = Gtk.Label(label=page, xalign=0.0)
        label.set_margin_top(8)
        label.set_margin_bottom(8)
        label.set_margin_left(10)
        label.set_margin_right(10)
        label.set_name("row")
        row = Gtk.ListBoxRow()
        row.add(label)
        row.name = page
        row.title = page
        self.listbox.add(row)

        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(box)
        self.stack.add_named(sw, page)

        label = Gtk.Label(label="HID", xalign=0.0)
        label.get_style_context().add_class("heading")
        label.set_margin_bottom(4)
        box.pack_start(label, False, True, 0)
        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")
        frame.set_margin_bottom(12)
        box.pack_start(frame, False, True, 0)
        fbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(fbox)

        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Enable Keyboard", xalign=0.0)
        lbox.pack_start(label, False, True, 0)

        switch = Gtk.Switch()
        self.keyboard_switch = switch

        switch.connect(
            "notify::active", partial(self.on_activate, switch, "hid_keyboard")
        )

        self.widgets.append(switch)
        rbox.pack_start(switch, False, False, 0)
        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Enable Mouse", xalign=0.0)
        lbox.pack_start(label, False, True, 0)

        switch = Gtk.Switch()
        self.mouse_switch = switch
        switch.connect("notify::active", partial(self.on_activate, switch, "hid_mouse"))

        self.widgets.append(switch)
        rbox.pack_start(switch, False, False, 0)
        sbox = Gtk.Box()
        sbox.set_margin_top(8)
        sbox.set_margin_bottom(8)
        sbox.set_margin_left(8)
        sbox.set_margin_right(8)
        lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_start(lbox, True, True, 0)
        fbox.pack_start(sbox, False, True, 0)
        rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sbox.pack_end(rbox, False, False, 0)

        label = Gtk.Label(label="Enable Joystick", xalign=0.0)
        lbox.pack_start(label, False, True, 0)

        switch = Gtk.Switch()
        self.joystick_switch = switch
        switch.connect(
            "notify::active", partial(self.on_activate, switch, "hid_joystick")
        )

        self.widgets.append(switch)
        rbox.pack_start(switch, False, False, 0)

    def on_main_window_destroy(self, widget):
        Gtk.main_quit()

    def on_back_clicked(self, widget, *args):
        self.leaflet.set_visible_child_name("sidebar")
        self.headerbar.set_subtitle("")
        self._load_state()

    def on_leaflet_change(self, *args):
        folded = self.leaflet.get_folded()
        content = self.leaflet.get_visible_child_name() == "content"
        self.back.set_visible(folded and content)

    def on_select_page(self, widget, row):
        self.action_revealer.set_reveal_child(False)
        if self.listbox.get_selection_mode() == Gtk.SelectionMode.NONE:
            self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
            self.listbox.select_row(row)
        self.stack.set_visible_child_name(row.name)
        self.headerbar.set_subtitle(row.title)
        self.leaflet.set_visible_child_name("content")

        # In folded view unselect the row in the listbox
        # so it's possible to go back to the same page
        if self.leaflet.get_folded():
            self.listbox.unselect_row(row)

    # def on_save_presets(self, *args):
    #     pass
    def is_active(self, dev_type):
        devs = self.root.findall("dev")
        for dev in devs:
            if dev.attrib.get("type") == dev_type:
                return True
        return False

    def on_activate(self, switch, dev_type, *args):

        if self.no_emmit:
            return

        if dev_type == "storage_flash":
            if switch.get_active():

                sel = self.flash_treeView.get_selection()
                treestore, iter = sel.get_selected_rows()
                if len(iter) == 0:
                    self.flash_switch.set_state(False)

                if iter is not None:
                    for x in iter:
                        s = ET.SubElement(self.root, "dev", type="storage_flash")
                        p = ET.SubElement(s, "path")
                        p.text = os.path.join(datapath, "image", treestore[x][0])

            else:
                devs = self.root.findall("dev")
                for dev in devs:
                    if dev.attrib.get("type") == "storage_flash":
                        self.root.remove(dev)

        elif dev_type == "storage_iso":
            if switch.get_active():

                sel = self.iso_treeView.get_selection()
                treestore, iter = sel.get_selected_rows()

                if iter is not None:
                    for x in iter:
                        s = ET.SubElement(self.root, "dev", type="storage_iso")
                        p = ET.SubElement(s, "path")
                        p.text = os.path.join(datapath, "iso", treestore[x][0])

            else:
                devs = self.root.findall("dev")
                for dev in devs:
                    if dev.attrib.get("type") == "storage_iso":
                        self.root.remove(dev)

        else:
            if switch.get_active():
                s = ET.SubElement(self.root, "dev", type=dev_type)

            else:
                devs = self.root.findall("dev")
                for dev in devs:
                    if dev.attrib.get("type") == dev_type:
                        self.root.remove(dev)

        xmlstr = ET.tostring(self.root, encoding="utf8", method="xml")
        with open(self.xmlfile, "wb") as xml_file:
            xml_file.write(xmlstr)

        self.show()

    def on_load_preset(self, widget, *args):
        self._load_state()

    def on_save_preset(self, widget, *args):

        dialog = TextEntryDialog(
            self.window,
            title="Save Preset",
            text="Enter the name of your Preset",
            size=(self.width, self.hight),
        )
        text = dialog.ask()
        print(text)

        self._load_state()

    def on_message_hide(self, widget, *args):
        self.message_revealer.set_reveal_child(False)

    def on_create_flash(self, widget, *args):

        filename = self.flash_create_name.get_text()
        if len(filename) == 0:
            return

        imgfile = os.path.join(datapath, "image", f"{filename}.img")

        if os.path.isdir(imgfile):
            return

        size = 1024 * 1024 * 1024 * int(self.flash_create_size.get_value())

        with open(imgfile, "wb") as img:
            img.truncate(size)

        os.system(f'chmod 777 "{imgfile}"')
        self._load_state()

    def on_delete_iso(self, widget, *args):
        model = self.iso_delete_combo.get_model()
        index = self.iso_delete_combo.get_active()

        filename = model[index][0]

        dialog = YesNoDialog(
            self.window,
            title="Delete ISO Image",
            text="Delete ISO Image File?",
            text2=filename,
            size=(self.width, self.hight),
        )
        do_delete = dialog.ask()
        if do_delete:
            os.remove(os.path.join(datapath, "iso", filename))
            self._load_state()

    def on_delete_flash(self, widget, *args):

        model = self.flash_delete_combo.get_model()
        index = self.flash_delete_combo.get_active()

        filename = model[index][0]

        dialog = YesNoDialog(
            self.window,
            title="Delete Flash Image",
            text="Delete Flash Image File?",
            text2=filename,
            size=(self.width, self.hight),
        )
        do_delete = dialog.ask()
        if do_delete:
            os.remove(os.path.join(datapath, "image", filename))
            self._load_state()

    def on_remove_preset(self, widget, *args):
        self._load_state()

    def on_start_stop(self, widget, *args):

        if widget.get_active():
            print("activate")

            # ~ self.status = "RUNNING"
            self.message_revealer.set_reveal_child(True)

            response = self.service.status()
            print(f'Service answered "{response}"')
            with open(self.xmlfile, "r") as gfile:
                response = self.service.set_config(gfile.read())
            print(response)

            response = self.service.status()
            print(f'Service answered "{response}"')
            response = self.service.start()
            self.message_revealer_label.set_text(response)
            print(f'Service answered "{response}"')
            response = self.service.status()
            print(f'Service answered "{response}"')
        else:
            print("deactivate")
            self.service.stop()
            # ~ self.status = "Stopped"

        self._load_state()

    def sizeof_fmt(self, num, suffix="B"):
        for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f} Yi{suffix}"

    def _load_state(self):

        self.flash_store.clear()
        for flash_image in os.listdir(os.path.join(datapath, "image")):
            if flash_image.endswith(".img"):
                size = os.path.getsize(os.path.join(datapath, "image", flash_image))
                self.flash_store.append([flash_image, self.sizeof_fmt(size)])

        self.iso_store.clear()
        for iso in os.listdir(os.path.join(datapath, "iso")):
            if iso.endswith(".iso"):
                size = os.path.getsize(os.path.join(datapath, "iso", iso))
                self.iso_store.append([iso, self.sizeof_fmt(size)])

        self.no_emmit = True

        if self.is_active("serial"):
            self.serial_switch.set_state(True)

        if self.is_active("storage_flash"):
            self.flash_switch.set_state(True)

        if self.is_active("storage_iso"):
            self.iso_switch.set_state(True)

        if self.is_active("sound"):
            self.sound_switch.set_state(True)

        if self.is_active("net_rndis"):
            self.rndis_switch.set_state(True)

        if self.is_active("hid_keyboard"):
            self.keyboard_switch.set_state(True)

        if self.is_active("hid_mouse"):
            self.mouse_switch.set_state(True)

        if self.is_active("hid_joystick"):
            self.joystick_switch.set_state(True)

        self.no_emmit = False

        self.preset_store.clear()
        self.keys = [
            "Default",
        ]
        for key in self.keys:
            # cell.set_width_chars(10)
            self.preset_store.append((key,))
        if UIDEV:
            status = "Stopped"
        else:
            status = self.service.status()

        print(status)

        # ~ status = self.status
        if status == "RUNNING":
            # self.action_revealer.set_reveal_child(False)
            self.mainswitch.set_active(True)
            self.statlabel.set_markup("Service: <b>Enabled</b>")
            print("Disable switches")
            self._widgets_disable(True)

        else:
            # self.action_revealer.set_reveal_child(True)
            self.mainswitch.set_active(False)
            self.statlabel.set_markup("Service: <b>Disabled</b>")
            self._widgets_disable(False)

    def _indent(self, elem, level=0):
        i = "\n" + level * "  "
        j = "\n" + (level - 1) * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for subelem in elem:
                self._indent(subelem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = j
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = j
        return elem

    def show(self, pritty=True):
        import copy

        root = copy.deepcopy(self.root)
        if pritty:
            self._indent(root)
        print(ET.tostring(root).decode())


class GadgetApplication(Gtk.Application):
    def __init__(self, application_id, flags):
        Gtk.Application.__init__(self, application_id=application_id, flags=flags)
        self.connect("activate", self.new_window)

    def new_window(self, *args):
        GadgetWindow(self)


class TextEntryDialog(Gtk.Dialog):
    def __init__(self, parent, title, text="", size=(150, 100)):
        super().__init__(parent=parent, title=title, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.set_default_size(*size)

        label = Gtk.Label(label=text)
        self.entry = Gtk.Entry()
        # entry.set_text(str(default_value))
        box = self.get_content_area()
        box.add(label)
        box.add(self.entry)
        # self.show_all()

    def ask(self):
        response = self.run()
        if response == Gtk.ResponseType.OK:
            value = self.entry.get_text()
            if value == "":
                value = None
        else:
            value = None

        self.destroy()
        return value


class YesNoDialog(Gtk.Dialog):
    def __init__(self, parent, title, text="", text2="", size=(150, 100)):
        super().__init__(parent=parent, title=title, flags=0)
        self.add_buttons(
            Gtk.STOCK_NO, Gtk.ResponseType.NO, Gtk.STOCK_YES, Gtk.ResponseType.YES
        )

        self.set_default_size(*size)

        box = self.get_content_area()
        label = Gtk.Label(label=text)
        label.set_margin_top(20)
        box.add(label)
        label = Gtk.Label(label=text2)
        label.set_margin_top(8)
        box.add(label)
        self.show_all()

    def ask(self):
        response = self.run()
        if response == Gtk.ResponseType.YES:
            value = True
        else:
            value = False

        self.destroy()
        return value


if __name__ == "__main__":
    Handy.init()
    app = GadgetApplication(
        "de.beaerlin.gadgetcontroller", Gio.ApplicationFlags.FLAGS_NONE
    )
    app.run()
