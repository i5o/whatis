#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014  Ignacio Rodríguez <ignacio@sugarlabs.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  021101301, USA.

import cairo
import gi
import os
import random

gi.require_version('Gst', "1.0")

from art4apps import Art4Apps
from gettext import gettext as _

from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GObject
from gi.repository import Gst
from gi.repository import Gtk

from sugar3.activity import activity
from sugar3.activity.widgets import ActivityButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolcombobox import ToolComboBox

Gst.init([])


class WhatIs(activity.Activity):
    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        self.game = Game(self)

        self.build_toolbar()
        self.set_canvas(self.game)
        self.show_all()

    def build_toolbar(self):
        toolbox = ToolbarBox()
        toolbar = toolbox.toolbar

        activity_button = ActivityButton(self)
        toolbar.insert(activity_button, -1)
        toolbar.insert(Gtk.SeparatorToolItem(), -1)

        new_game = ToolButton("media-playlist-repeat")
        new_game.set_tooltip(_("New game"))
        new_game.connect("clicked", self.game.new_game)

        play_sound = ToolButton("media-playback-start")
        play_sound.set_tooltip(_("Replay level objetive"))
        play_sound.connect("clicked", self.game.sound_current_game)

        toolbar.insert(new_game, -1)
        toolbar.insert(play_sound, -1)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar.insert(separator, -1)

        locale = os.environ["LANG"]
        locale = locale.split("_")[0]

        if locale == "en":
            current = 0
        elif locale == "fr":
            current = 1
        elif locale == "es":
            current = 2
        else:
            current = 0

        combo = ToolComboBox()
        combo.set_property("label-text", "Language:")
        combo.combo.append_item("en", _("English"), icon_name="en")
        combo.combo.append_item("fr", _("French"), icon_name="fr")
        combo.combo.append_item("es", _("Spanish"), icon_name="es")

        combo.combo.set_active(current)
        combo.combo.connect("changed", self.game.change_language)

        toolbar.insert(separator, -1)
        toolbar.insert(combo, -1)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar.insert(separator, -1)

        stopbtn = StopButton(self)
        toolbar.insert(stopbtn, -1)
        toolbar.show_all()

        self.set_toolbar_box(toolbox)


class Game(Gtk.DrawingArea):
    def __init__(self, parent):
        Gtk.DrawingArea.__init__(self)
        self.add_events(Gdk.EventMask.BUTTON_MOTION_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.LEAVE_NOTIFY_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.POINTER_MOTION_HINT_MASK)

        self._parent = parent
        self._players = []
        self.finished = False

        locale = os.environ["LANG"]
        locale = locale.split("_")[0]

        if locale == "en" or locale == "es" or locale == "fr":
            pass
        else:
            locale = "en"

        self.set_language(locale)

        self._id = self.connect("button-press-event", self.check_option)

    def check_option(self, widget, event):
        x = int(event.x)
        y = int(event.y)
        image = self.get_image_pressed(x, y)
        if not image:
            return

        self.mute_all()
        sound = self._sounds[image]
        player = Player()
        player.load(sound)
        player.player.set_state(Gst.State.PLAYING)
        self._players.append(player)

        self.is_the_correct(x, y)

    def do_draw(self, ctx):
        cursor = Gdk.Cursor.new(Gdk.CursorType.WATCH)
        self._parent.get_window().set_cursor(cursor)
        square = Gdk.Rectangle()
        square.x = 0
        square.y = 0
        square.width = Gdk.Screen.width()
        square.height = Gdk.Screen.height()
        color = Gdk.color_parse("white")
        Gdk.cairo_set_source_color(ctx, color)
        Gdk.cairo_rectangle(ctx, square)
        ctx.fill()

        self.draw_images(ctx, self.current_images)

        if not self.finished:
            if not self._id:
                self._id = self.connect('button-press-event', self.check_option)

        self._parent.get_window().set_cursor(None)

    def draw_images(self, ctx, load_images=None):
        self.options = {}

        max_images = Gdk.Screen.width() / 210
        if not load_images:
            self.current_images = images = random.sample(self._images,
                max_images)
            self.current_option = random.choice(images)
        else:
            images = load_images

        x = 0
        w = 210
        y = (Gdk.Screen.height() / 2) - 105

        separation = (Gdk.Screen.width() - (max_images * w)) / max_images

        for image in images:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(image, w, w)
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                     w, w)

            self.options[image] = {"min_x": x,
                                    "max_x": x + w,
                                    "min_y": y,
                                    "max_y": y + w}

            x += separation
            ct = cairo.Context(surface)
            Gdk.cairo_set_source_pixbuf(ct, pixbuf, 0, 0)
            ct.paint()

            ctx.save()
            ctx.rectangle(x, y, w, w)
            ctx.clip()
            ctx.set_source_surface(surface, x, y)
            ctx.paint()
            ctx.restore()

            x += w

        if not load_images:
            self.sound_current_game()

    def get_image_pressed(self, x, y):
        for option in self.options:
            data = self.options[option]
            if (x >= data["min_x"] and x <= data["max_x"]) and \
                (y >= data["min_y"] and y <= data["max_y"]):
                break
        return option

    def is_the_correct(self, x, y):
        for option in self.options:
            data = self.options[option]
            if (x >= data["min_x"] and x <= data["max_x"]) and \
                (y >= data["min_y"] and y <= data["max_y"]):
                break

        if option == self.current_option:
            self.disconnect(self._id)
            self._id = None
            self.finished = True
            self.queue_draw()
            GObject.timeout_add(2000, self.new_game)

    def sound_current_game(self, *kwargs):
        self.mute_all()
        player = Player()
        player.load(self._sounds[self.current_option])
        player.player.set_state(Gst.State.PLAYING)
        self._players.append(player)

    def new_game(self, widget=None):
        if widget:
            self.disconnect(self._id)
            self._id = None

        def internal_callback():
            self.current_images = None
            self.queue_draw()
            self.finished = False
            self.set_sensitive(True)

        cursor = Gdk.Cursor.new(Gdk.CursorType.WATCH)
        self._parent.get_window().set_cursor(cursor)
        GObject.idle_add(internal_callback)

    def change_language(self, widget):
        it = widget.get_active_iter()
        model = widget.get_model()
        value = model.get_value(it, 0)
        self.set_language(value)
        self.queue_draw()

    def set_language(self, locale):
        self.options = {}
        self.current_images = None

        art = Art4Apps()
        images = art.get_words()
        new_images = []
        for image in images:
            path = art.get_image_filename(image)
            if os.path.exists(path):
                new_images.append(path.encode("utf-8"))

        self._sounds = {}
        for image in new_images:
            image_name = os.path.basename(image)[:-4]
            audio = art.get_audio_filename(image_name, language=locale)
            if not audio:
                new_images.remove(image)
            if audio:
                self._sounds[image] = audio

        # Check again!
        self._images = []
        for image in new_images:
            try:
                sound = self._sounds[image]
                if os.path.exists(sound):
                    self._images.append(image)
            except Exception:
                continue

    def mute_all(self):
        for player in self._players:
            player.player.set_state(Gst.State.NULL)
            self._players.remove(player)


class Player:
    def __init__(self):
        self.player = Gst.ElementFactory.make("playbin", "player")
        self.player.set_state(Gst.State.READY)

    def load(self, path):
        uri = "file://%s" % path
        self.player.set_property("uri", uri)
        self.player.set_property("volume", 1.0)
        self.player.set_state(Gst.State.READY)
